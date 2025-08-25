import requests

# Daftar kode produk yang ingin Anda tampilkan
SELECTED_CODES = ["AVXLCF1", "AVXLC1", "VXLX1", "XLDXCS8"]

# Cache untuk menyimpan data produk yang diambil dari API
product_data_cache = {}

def get_selected_products(api_key, api_endpoint):
    """
    Mengambil seluruh daftar harga dari API dan memfilter produk yang dipilih.
    Mengembalikan daftar produk yang cocok.
    """
    global product_data_cache # Memastikan kita menggunakan cache global
    
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
                    product_data_cache[item.get('code')] = item # Simpan ke cache
            
            return products_to_display
        else:
            return {"error": res_data.get("message", "Gagal mengambil data dari API")}
    except requests.exceptions.RequestException as e:
        return {"error": f"Terjadi kesalahan saat berkomunikasi dengan API: {e}."}
    except Exception as e:
        return {"error": f"Terjadi kesalahan tak terduga: {e}"}

def get_product_details_from_cache(code):
    """
    Mengambil detail produk dari cache berdasarkan kode.
    """
    return product_data_cache.get(code)