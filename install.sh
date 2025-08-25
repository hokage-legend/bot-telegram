#!/bin/bash

# Exit jika ada perintah yang gagal
set -e

# --- KONFIGURASI ---
# Ganti dengan link repository GitHub Anda
REPO_URL="https://github.com/hokage-legend/bot-telegram.git"
SERVICE_NAME="telegram_bot.service"
PROJECT_DIR="bot-telegram"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"

echo "========================================"
echo "      HESDA PPOB BOT INSTALLER"
echo "========================================"

# --- LANGKAH PEMBESIHAN (CLEANUP) ---
echo "Memulai proses pembersihan instalasi sebelumnya..."

# Menghentikan service jika sedang berjalan
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Service bot ditemukan. Menghentikan service..."
    sudo systemctl stop "$SERVICE_NAME"
    sudo systemctl disable "$SERVICE_NAME"
else
    echo "Tidak ada service bot yang aktif ditemukan."
fi

# Menghapus file service systemd
if [ -f "$SERVICE_FILE" ]; then
    echo "Menghapus file service lama di $SERVICE_FILE..."
    sudo rm "$SERVICE_FILE"
    sudo systemctl daemon-reload
else
    echo "Tidak ada file service lama yang ditemukan."
fi

# Menghapus direktori proyek sebelumnya
if [ -d "$PROJECT_DIR" ]; then
    echo "Menghapus direktori proyek lama: $PROJECT_DIR..."
    sudo rm -rf "$PROJECT_DIR"
else
    echo "Tidak ada direktori proyek lama yang ditemukan."
fi

echo "Proses pembersihan selesai."
echo "----------------------------------------"

# --- LANGKAH INSTALASI BARU ---

# Memeriksa apakah Git sudah terinstal
if ! command -v git &> /dev/null
then
    echo "Git tidak ditemukan. Menginstal Git..."
    sudo apt-get update
    sudo apt-get install -y git
fi

# Mengunduh kode dari GitHub
echo "Mengunduh repository dari GitHub..."
git clone "$REPO_URL"
cd "$PROJECT_DIR"

# Membuat dan mengaktifkan virtual environment
echo "Membuat virtual environment Python..."
python3 -m venv venv

echo "Menginstal library yang dibutuhkan..."
source venv/bin/activate
pip install -r requirements.txt

# Membuat file service systemd
echo "Membuat file service systemd di $SERVICE_FILE..."
cat > "$SERVICE_FILE" << EOF
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
EOF

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
