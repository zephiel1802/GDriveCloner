#!/bin/bash
# ============================================================
#  GDriveCloner — Launch Script (macOS / Linux)
#  Tự động cài dependencies và chạy app
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       🗂️  GDriveCloner Launcher      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Kiểm tra Python 3 ────────────────────────────────────
echo -e "${YELLOW}[1/4] Kiểm tra Python 3...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌  Không tìm thấy Python 3. Vui lòng cài từ https://python.org${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅  Python $PYTHON_VERSION${NC}"

# ── 2. Nâng cấp pip & cài dependencies ─────────────────────
echo -e "${YELLOW}[2/4] Chuẩn bị pip...${NC}"
# Luôn dùng python3 -m pip để tránh vấn đề PATH
PIP="python3 -m pip"
python3 -m pip install --upgrade pip --quiet --no-warn-script-location 2>/dev/null
echo -e "${GREEN}✅  pip OK${NC}"

# ── 3. Cài dependencies ─────────────────────────────────────
echo -e "${YELLOW}[3/4] Cài đặt dependencies...${NC}"
$PIP install -r "$SCRIPT_DIR/requirements.txt" --quiet --no-warn-script-location

echo -e "${GREEN}✅  Tất cả dependencies đã sẵn sàng${NC}"

# ── 4. Kiểm tra credentials.json ────────────────────────────
echo -e "${YELLOW}[4/4] Kiểm tra credentials.json...${NC}"
if [ ! -f "$SCRIPT_DIR/credentials.json" ]; then
    echo ""
    echo -e "${RED}⚠️  Chưa có file credentials.json!${NC}"
    echo ""
    echo "  Vui lòng:"
    echo "  1. Vào https://console.cloud.google.com"
    echo "  2. Bật Google Drive API"
    echo "  3. Tạo OAuth 2.0 Client ID (Desktop app)"
    echo "  4. Tải credentials.json về và đặt vào cùng thư mục với file này"
    echo ""
    read -p "  Nhấn Enter sau khi đã thêm file... " _
fi

# ── 5. Chạy app ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}🚀  Đang khởi động GDriveCloner...${NC}"
echo ""
python3 "$SCRIPT_DIR/main.py"
