#!/bin/bash
# ============================================================
#  GDriveCloner - Start Script (Linux/macOS)
# ============================================================

# ── 1. Xin quyen Root ──────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "[GDriveCloner] Dang yeu cau quyen root..."
    exec sudo "$0" "$@"
fi

cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "  GDriveCloner Launcher"
echo "============================================================"
echo ""

# ── 2. Kiem tra Python ────────────────────────────────────────
if ! command -v python3 &> /dev/null; then
    echo "[LOI] Khong tim thay Python 3! Vui long cai dat Python 3.9+."
    exit 1
fi

# ── 3. Cai dat thu vien ───────────────────────────────────────
echo "[1/2] Dang cai dat/kiem tra dependencies..."
python3 -m pip install --upgrade pip --quiet
python3 -m pip install -r requirements.txt --quiet

# ── 4. Khoi dong ung dung ─────────────────────────────────────
echo "[2/2] Dang khoi dong GDriveCloner..."
python3 app.py
