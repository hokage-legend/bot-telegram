import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# Import from config
from config import API_KEY, API_ENDPOINT

# Cache for storing product data retrieved from the API
product_data_cache = {}
# List of specific product codes to display
SELECTED_CODES = ["AVXLCF1", "AVXLC1", "VXLX1", "XLDXCS8"]

def get_selected_products(api_key, api_endpoint):
    """
    Retrieves the full price list from the API and filters for selected products.
    Returns a list of matching products or an error dictionary.
    """
    global product_data_cache
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    data_body = {
        "api_key": api_key,
        "type": "prabayar",
    }

    try:
        response = requests.post(
            api_endpoint,
            headers=headers,
            data=data_body
        )
        response.raise_for_status()
        res_data = response.json()

        if res_data.get("status") is True:
            products_from_api = res_data.get("data", [])
            
            products_to_display = []
            for item in products_from_api:
                if item.get('code') in SELECTED_CODES:
                    products_to_display.append(item)
                    product_data_cache[item.get('code')] = item
            
            return products_to_display
        else:
            return {"error": res_data.get("message", "Failed to retrieve data from API")}
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while communicating with the API: {e}."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_product_details_from_cache(code):
    """
    Retrieves product details from the cache by code.
    """
    return product_data_cache.get(code)

async def display_selected_products(message) -> None:
    """Displays a list of selected products as buttons."""
    await message.reply_text("Loading selected product data... Please wait.")
    
    products_to_display = get_selected_products(API_KEY, API_ENDPOINT)

    if isinstance(products_to_display, dict) and "error" in products_to_display:
        await message.reply_text(products_to_display["error"])
        return

    if not products_to_display:
        await message.reply_text("No selected products were found from the API.")
        return

    prices_text = "💰 **Selected Products:**\n\n"
    keyboard = []

    for item in products_to_display:
        button_text = f"[{item.get('code')}] {item.get('name')}"
        callback_data = f"show_details_{item.get('code')}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(prices_text, parse_mode='Markdown', reply_markup=reply_markup)

async def show_product_details(message, code: str) -> None:
    """Displays full product details based on a product code."""
    product = get_product_details_from_cache(code)
    
    if product:
        details_text = (
            f"**Service Details:**\n\n"
            f"**Service Name:** {product.get('name')}\n"
            f"**Code:** `{product.get('code')}`\n"
            f"**Category:** {product.get('category')}\n"
            f"**Provider:** {product.get('provider')}\n"
            f"**Price:** Rp {product.get('price')}\n"
            f"**Status:** {product.get('status')}\n"
            f"**Note:** {product.get('note', '-')}\n"
        )
        await message.reply_text(details_text, parse_mode='Markdown')
    else:
        await message.reply_text("Product details not found.")