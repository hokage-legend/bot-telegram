from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def admin_panel(message) -> None:
    """Menampilkan panel admin."""
    keyboard = [
        [InlineKeyboardButton("Top Up Saldo", callback_data="show_topup_methods")],
        # Tambahkan tombol admin lainnya di sini
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Silakan pilih opsi admin:", reply_markup=reply_markup)

async def show_topup_methods(message, api_key) -> None:
    """Mengambil dan menampilkan metode top up."""
    await message.reply_text("Memuat metode top up... Mohon tunggu sebentar.")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data_body = {
        "api_key": api_key,
        "type": "bank", # Contoh: filter hanya bank dan e-wallet
    }

    try:
        response = requests.post(
            "https://atlantich2h.com/deposit/metode", # Pastikan ini URL yang benar
            headers=headers,
            data=data_body
        )
        response.raise_for_status()
        res_data = response.json()

        if res_data.get("status") is True and res_data.get("data"):
            methods = res_data.get("data")
            keyboard = []
            
            for method in methods:
                button_text = f"{method.get('name')} (Min: Rp {method.get('min')}, Fee: {method.get('fee_persen')}%)"
                callback_data = f"select_method_{method.get('metode')}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text("Pilih metode top up:", reply_markup=reply_markup)
        else:
            await message.reply_text("Tidak ada metode top up yang ditemukan atau gagal memuat data.")
            
    except requests.exceptions.RequestException as e:
        await message.reply_text(f"Terjadi kesalahan saat berkomunikasi dengan API: {e}.")
    except Exception as e:
        await message.reply_text(f"Terjadi kesalahan tak terduga: {e}")