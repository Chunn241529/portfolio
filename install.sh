#!/bin/bash
# Script cài đặt môi trường cho Linux/macOS
set -e

# Kiểm tra và tạo môi trường ảo nếu chưa có
if [ ! -d ".venv" ]; then
    echo "Đang tạo môi trường ảo Python..."
    python3 -m venv .venv
fi

# Kích hoạt môi trường ảo
source .venv/bin/activate

# Tạo requirements.txt với các thư viện cần thiết
cat <<EOT > requirements.txt
fastapi
uvicorn
requests
pydantic
pillow
aiohttp
PyPDF2
EOT

# Cài đặt các thư viện từ requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

echo "\033[1;32mHoàn tất cài đặt!\033[0m"
