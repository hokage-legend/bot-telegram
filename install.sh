#!/bin/bash

# Exit jika ada perintah yang gagal
set -e

# --- KONFIGURASI ---
REPO_URL="https://github.com/hokage-legend/bot-telegram.git"
SERVICE_NAME="telegram_bot.service"
PROJECT_DIR="bot-telegram"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
CONFIG_FILE="$PROJECT_DIR/config.py"

# ==========================================================
# GANTI KREDENSIAL HESDA STORE ANDA DI BAWAH INI
# PERINGATAN: Kredensial ini akan disimpan dalam skrip.
# Jaga kerahasiaan file ini.
# ==========================================================
HESDASTORE_KEY_DEFAULT="2iB0Qvvqaw85lCOvCy"
EMAIL_ANDA_DEFAULT="ikbal192817@gmail.com"
PASSWORD_ANDA_DEFAULT="ayomasuk123"
# ==========================================================

echo "========================================"
echo "      HESDA PPOB BOT INSTALLER"
echo "========================================"

# --- LANGKAH PEMBESIHAN (CLEANUP) ---
echo "Memulai proses pembersihan instalasi sebelumnya..."

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Service bot ditemukan. Menghentikan service..."
    sudo systemctl stop "$SERVICE_NAME"
    sudo systemctl disable "$SERVICE_NAME"
fi

if [ -f "$SERVICE_FILE" ]; then
    echo "Menghapus file service lama di $SERVICE_FILE..."
    sudo rm "$SERVICE_FILE"
    sudo systemctl daemon-reload
fi

if [ -d "$PROJECT_DIR" ]; then
    echo "Menghapus direktori proyek lama: $PROJECT_DIR..."
    sudo rm -rf "$PROJECT_DIR"
fi

echo "Proses pembersihan selesai."
echo "----------------------------------------"

# --- LANGKAH INSTALASI BARU ---

if ! command -v git &> /dev/null
then
    echo "Git tidak ditemukan. Menginstal Git..."
    sudo apt-get update
    sudo apt-get install -y git
fi

# Mengunduh kode dari GitHub
echo "Mengunduh repository dari GitHub..."
git clone "$REPO_URL"

# Masuk ke direktori proyek
cd "$PROJECT_DIR"

# Meminta input untuk Telegram Bot Token saja
echo "----------------------------------------"
echo "Masukkan Telegram Bot Token Anda."
read -p "Telegram Bot Token: " TELEGRAM_BOT_TOKEN_INPUT
echo "----------------------------------------"

# Membuat file config.py dengan kredensial default Hesda dan token yang diinput
echo "Membuat file konfigurasi (config.py)..."
cat > config.py << EOFF
# ==========================================================
# FILE INI DIGUNAKAN UNTUK MENYIMPAN INFORMASI RAHASIA
# ==========================================================

HESDASTORE_KEY = "$HESDASTORE_KEY_DEFAULT"
EMAIL_ANDA = "$EMAIL_ANDA_DEFAULT"
PASSWORD_ANDA = "$PASSWORD_ANDA_DEFAULT"

API_BASE_URL = "https://api.hesda-store.com/v2/"
TELEGRAM_BOT_TOKEN = "$TELEGRAM_BOT_TOKEN_INPUT"
EOFF

# Membuat dan mengaktifkan virtual environment
echo "Membuat virtual environment Python..."
python3 -m venv venv

echo "Menginstal library yang dibutuhkan..."
source venv/bin/activate
pip install -r requirements.txt

# Membuat file service systemd dengan sudo
echo "Membuat file service systemd di $SERVICE_FILE..."
cat << EOF_SERVICE | sudo tee "$SERVICE_FILE" > /dev/null
[Unit]
Description=Telegram PPOB Reseller Bot
After=network.target

[Service]
ExecStart=$PWD/venv/bin/python $PWD/main.py
WorkingDirectory=$PWD
User=root
Group=root
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF_SERVICE

# Memuat ulang systemd, mengaktifkan, dan memulai service
echo "Mengaktifkan dan memulai service bot..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

echo "========================================"
echo "       INSTALASI SELESAI!"
echo "========================================"
echo "Bot Anda sekarang berjalan sebagai service."
echo "Untuk mengecek status bot, jalankan: sudo systemctl status $SERVICE_NAME"
echo "Untuk melihat log, jalankan: sudo journalctl -u $SERVICE_NAME -f"

# Deactivate the virtual environment
deactivate
