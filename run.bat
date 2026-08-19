@echo off
REM ============================================================
REM  GDriveCloner — Launch Script (Windows)
REM  Tự động cài dependencies và chạy app
REM ============================================================

title GDriveCloner Launcher
color 0A
cd /d "%~dp0"

echo.
echo  ==========================================
echo     🗂️  GDriveCloner Launcher (Windows)
echo  ==========================================
echo.

REM ── 1. Kiểm tra quyền Admin ──────────────────────────────
echo [1/5] Kiem tra quyen Administrator...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo    OK - Dang chay voi quyen Admin
) else (
    echo    Dang yeu cau quyen Admin...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM ── 2. Kiểm tra Python ───────────────────────────────────
echo [2/5] Kiem tra Python 3...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo    LOI: Khong tim thay Python!
    echo    Vui long tai Python 3.9+ tu: https://python.org
    echo    (Nho tick "Add Python to PATH" khi cai^)
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo    OK - Python %PY_VER%

REM ── 3. Nâng cấp pip ──────────────────────────────────────
echo [3/5] Nang cap pip...
python -m pip install --upgrade pip --quiet
echo    OK

REM ── 4. Cài dependencies ──────────────────────────────────
echo [4/5] Cai dat dependencies...
python -m pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo.
    echo    LOI: Khong the cai dependencies!
    echo    Kiem tra ket noi mang va thu lai.
    pause
    exit /b 1
)
echo    OK - Tat ca dependencies da san sang

REM ── 5. Kiểm tra credentials.json ─────────────────────────
echo [5/5] Kiem tra credentials.json...
if not exist "credentials.json" (
    echo.
    echo  ==========================================
    echo    CHUA CO FILE credentials.json!
    echo  ==========================================
    echo.
    echo   Vui long:
    echo   1. Vao https://console.cloud.google.com
    echo   2. Bat Google Drive API
    echo   3. Tao OAuth 2.0 Client ID (Desktop app^)
    echo   4. Tai credentials.json ve va dat vao
    echo      cung thu muc voi file nay
    echo.
    pause
)

REM ── 6. Chạy app ──────────────────────────────────────────
echo.
echo  Dang khoi dong GDriveCloner...
echo.
python main.py

if %errorLevel% neq 0 (
    echo.
    echo  App bi loi. Xem thong bao o tren.
    pause
)
