#!/bin/bash
# ============================================================
#  GDriveCloner - Desktop App Launcher (macOS / Linux)
#  Chay app.py voi pywebview (cua so rieng, khong can browser)
# ============================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "========================================"
echo "    GDriveCloner Desktop App Launcher"
echo "========================================"
echo ""

# 1. Quyen root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Requesting root privileges...${NC}"
    exec sudo "$0" "$@"
fi

# 2. Kiem tra Python 3
echo -e "${YELLOW}[1/3] Kiem tra Python 3...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}LOI: Khong tim thay Python 3. Vui long cai tu https://python.org${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}OK - Python $PYTHON_VERSION${NC}"

# 3. Cai dependencies
echo -e "${YELLOW}[2/3] Cai dat dependencies...${NC}"
python3 -m pip install --upgrade pip --quiet --no-warn-script-location 2>/dev/null
python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet --no-warn-script-location
echo -e "${GREEN}OK - Tat ca dependencies da san sang${NC}"

# 4. Chay Desktop App
echo -e "${YELLOW}[3/3] Khoi dong GDriveCloner Desktop App...${NC}"
echo ""
echo -e "${GREEN}Cua so app se hien ra trong giay lat...${NC}"
echo -e "${GREEN}De thoat: click chuot phai icon tray chon Thoat${NC}"
echo ""

if command -v pythonw &>/dev/null; then
    pythonw "$SCRIPT_DIR/app.py" &
else
    python3 "$SCRIPT_DIR/app.py" &
fi