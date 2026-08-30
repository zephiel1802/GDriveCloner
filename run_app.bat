@echo off
REM ============================================================
REM  GDriveCloner - Desktop App Launcher (Windows)
REM  Chay app.py voi pywebview (cua so rieng, khong can browser)
REM ============================================================

title GDriveCloner Desktop App
color 0A
cd /d "%~dp0"

echo.
echo  ==========================================
echo     GDriveCloner Desktop App Launcher
echo  ==========================================
echo.

REM -- 1. Kiem tra quyen Admin
echo [1/4] Kiem tra quyen Administrator...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo    OK - Dang chay voi quyen Admin
) else (
    echo    Dang yeu cau quyen Admin...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM -- 2. Kiem tra Python
echo [2/4] Kiem tra Python 3...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo    LOI: Khong tim thay Python!
    echo    Vui long tai Python 3.9+ tu: https://python.org
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo    OK - Python %PY_VER%

REM -- 3. Cai dependencies
echo [3/4] Cai dat dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo.
    echo    LOI: Khong the cai dependencies!
    pause
    exit /b 1
)
echo    OK - Tat ca dependencies da san sang

REM -- 4. Chay Desktop App
echo [4/4] Khoi dong GDriveCloner Desktop App...
echo.
echo    Cua so app se hien ra trong giay lat...
echo    De thoat: click chuot phai icon tray chon Thoat
echo.
start "" pythonw app.py