import requests
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes

# Import from config
from config import API_KEY, DEPOSIT_METHODS_ENDPOINT, CREATE_DEPOSIT_ENDPOINT, API_ENDPOINT

# Conversation states
SELECTING_METHOD, ENTERING_AMOUNT = range(2)

async def get_deposit_methods(method_type=None, metode=None):
    """
    Retrieves deposit methods from API as per documentation.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    data_body = {
        "api_key": API_KEY,
    }
    
    if method_type:
        data_body["type"] = method_type
    if metode:
        data_body["metode"] = metode

    try:
        response = requests.post(
            DEPOSIT_METHODS_ENDPOINT,
            headers=headers,
            data=data_body,
            timeout=30
        )
        
        print(f"Request to: {DEPOSIT_METHODS_ENDPOINT}")
        print(f"Parameters: {data_body}")
        print(f"Status Code: {response.status_code}")
        
        response.raise_for_status()
        res_data = response.json()
        
        print(f"API Response: {res_data}")
        
        return res_data
        
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return {"status": False, "message": f"API Communication Error: {e}"}
    except Exception as e:
        print(f"General Error: {e}")
        return {"status": False, "message": f"Unexpected error: {e}"}

async def show_topup_methods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays available top-up methods with appropriate filters."""
    query = update.callback_query
    await query.answer()
    message = query.message
    
    await message.reply_text("🔄 Loading top-up methods... Please wait.")
    
    result = await get_deposit_methods()
    
    if result.get("status") is True and result.get("data"):
        methods = result.get("data")
        keyboard = []
        
        active_methods = [m for m in methods if m.get('status') == 'aktif']
        
        if not active_methods:
            await message.reply_text("❌ No active deposit methods available.")
            return SELECTING_METHOD
        
        for method in active_methods:
            method_name = method.get('name', 'Unknown Method')
            min_amount = int(method.get('min', 0))
            max_amount = int(method.get('max', 0))
            fee = method.get('fee', 0)
            fee_percent = method.get('fee_persen', 0)
            method_code = method.get('metode', 'unknown')
            method_type = method.get('type', 'unknown')
            
            fee_text = ""
            if float(fee) > 0:
                fee_text = f" + Rp {int(fee):,}"
            elif float(fee_percent) > 0:
                fee_text = f" + {fee_percent}%"
            
            button_text = f"{method_name} (Rp {min_amount:,} - Rp {max_amount:,}{fee_text})"
            callback_data = f"select_topup_method_{method_code}_{method_type}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            "💳 **Available Deposit Methods:**\n\nSelect a payment method:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return SELECTING_METHOD
        
    else:
        error_msg = result.get("message", "Failed to load deposit methods")
        await message.reply_text(f"❌ Error: {error_msg}")
        return ConversationHandler.END

async def handle_method_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the selection of a top-up method."""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split('_')
    if len(data_parts) >= 4:
        method_code = data_parts[3]
        method_type = data_parts[4] if len(data_parts) > 4 else 'unknown'
        
        context.user_data['selected_method'] = method_code
        context.user_data['selected_method_type'] = method_type
        
        result = await get_deposit_methods(metode=method_code)
        method_info = None
        
        if result.get("status") is True and result.get("data"):
            methods = result.get("data")
            method_info = next((m for m in methods if m.get('metode') == method_code), None)
        
        if method_info:
            min_amount = int(method_info.get('min', 0))
            max_amount = int(method_info.get('max', 0))
            
            instructions = f"💵 **Enter Top-up Amount**\n\n"
            instructions += f"Selected: **{method_code}**\n"
            instructions += f"Minimum: Rp {min_amount:,}\n"
            instructions += f"Maximum: Rp {max_amount:,}\n\n"
            instructions += "Enter amount (example: `50000`):"
        else:
            instructions = f"💵 **Enter Top-up Amount**\n\nSelected: **{method_code}**\n\nEnter amount:"
        
        await query.message.reply_text(instructions, parse_mode='Markdown')
        
        return ENTERING_AMOUNT
    
    else:
        await query.message.reply_text("❌ Invalid method selection.")
        return ConversationHandler.END

async def handle_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user's top-up amount input and creates a deposit."""
    amount_str = update.message.text
    selected_method = context.user_data.get('selected_method')
    selected_method_type = context.user_data.get('selected_method_type')
    
    try:
        amount = int(amount_str.replace('.', '').replace(',', ''))
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0.")
            return ENTERING_AMOUNT

        result = await get_deposit_methods(metode=selected_method)
        method_info = None
        
        if result.get("status") is True and result.get("data"):
            methods = result.get("data")
            method_info = next((m for m in methods if m.get('metode') == selected_method), None)
        
        if method_info:
            min_amount = int(method_info.get('min', 0))
            max_amount = int(method_info.get('max', 0))
            
            if amount < min_amount:
                await update.message.reply_text(
                    f"❌ Minimum amount for {selected_method} is Rp {min_amount:,}"
                )
                return ENTERING_AMOUNT
            if amount > max_amount:
                await update.message.reply_text(
                    f"❌ Maximum amount for {selected_method} is Rp {max_amount:,}"
                )
                return ENTERING_AMOUNT

        await update.message.reply_text(f"🔄 Creating deposit request for Rp {amount:,}...")

        reff_id = f"tg{update.effective_user.id}_{int(time.time())}"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        data_body = {
            "api_key": API_KEY,
            "reff_id": reff_id,
            "nominal": amount,
            "type": selected_method_type,
            "metode": selected_method.upper()
        }

        print(f"Creating deposit with data: {data_body}")
        
        response = requests.post(
            CREATE_DEPOSIT_ENDPOINT,
            headers=headers,
            data=data_body,
            timeout=30
        )
        
        response.raise_for_status()
        res_data = response.json()

        if res_data.get("status") is True and res_data.get("data"):
            deposit_info = res_data.get("data")
            await process_deposit_response(update, deposit_info)
        else:
            error_msg = res_data.get("message", "Failed to create deposit")
            await update.message.reply_text(f"❌ Deposit Error: {error_msg}")

        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return ENTERING_AMOUNT
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ API Error: {str(e)}"
        if hasattr(e, 'response') and e.response:
            error_msg += f"\nStatus: {e.response.status_code}"
            error_msg += f"\nResponse: {e.response.text}"
        await update.message.reply_text(error_msg)
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {str(e)}")
        return ConversationHandler.END

async def process_deposit_response(update, deposit_info):
    """Memproses response deposit."""
    try:
        transaction_id = deposit_info.get('id', 'N/A')
        nominal = deposit_info.get('nominal', 0)
        fee = deposit_info.get('fee', 0)
        get_balance = deposit_info.get('get_balance', 0)
        status = deposit_info.get('status', 'pending')
        
        base_text = (
            f"✅ **Deposit Created**\n\n"
            f"**ID:** `{transaction_id}`\n"
            f"**Amount:** Rp {int(nominal):,}\n"
            f"**Fee:** Rp {int(fee):,}\n"
            f"**Receive:** Rp {int(get_balance):,}\n"
            f"**Status:** {status}\n\n"
        )
        
        if deposit_info.get('qr_image'):
            qr_image = deposit_info.get('qr_image')
            payment_text = base_text + "Scan QR code below:"
            await update.message.reply_photo(photo=qr_image, caption=payment_text, parse_mode='Markdown')
        
        elif deposit_info.get('nomor_va'):
            bank = deposit_info.get('bank', 'N/A')
            va_number = deposit_info.get('nomor_va', 'N/A')
            account_name = deposit_info.get('atas_nama', 'N/A')
            
            payment_text = (
                base_text +
                f"**Bank:** {bank}\n"
                f"**VA Number:** `{va_number}`\n"
                f"**Account Name:** {account_name}\n\n"
                f"⚠️ Transfer exactly **Rp {int(nominal):,}**"
            )
            await update.message.reply_text(payment_text, parse_mode='Markdown')
        
        elif deposit_info.get('tujuan'):
            bank = deposit_info.get('bank', 'N/A')
            account_number = deposit_info.get('tujuan', 'N/A')
            account_name = deposit_info.get('atas_nama', 'N/A')
            
            payment_text = (
                base_text +
                f"**Bank:** {bank}\n"
                f"**Account:** `{account_number}`\n"
                f"**Name:** {account_name}\n\n"
                f"⚠️ Transfer exactly **Rp {int(nominal):,}**"
            )
            await update.message.reply_text(payment_text, parse_mode='Markdown')
        
        elif deposit_info.get('url'):
            payment_url = deposit_info.get('url')
            payment_text = base_text + f"Complete payment at: {payment_url}"
            await update.message.reply_text(payment_text, parse_mode='Markdown')
        
        else:
            await update.message.reply_text(base_text + "Check your account for instructions.", parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing deposit: {str(e)}")