@echo off
REM ============================================================
REM  GDriveCloner - Desktop App Launcher (Windows)
REM ============================================================

title GDriveCloner Desktop App
color 0A
cd /d "%~dp0"

echo.
echo  ==========================================
echo     GDriveCloner Desktop App Launcher
echo  ==========================================
echo.

REM -- 1. Kiem tra Python
echo [1/3] Kiem tra Python 3...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo    LOI: Khong tim thay Python!
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo    OK - Python %PY_VER%

REM -- 2. Cai dependencies
echo [2/3] Cai dat dependencies...
python -m pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo    LOI: Khong the cai dependencies!
    pause
    exit /b 1
)
echo    OK - Dependencies da san sang

REM -- 3. Chay Desktop App
echo [3/3] Khoi dong GDriveCloner...
echo    (Cua so se hien ra trong giay lat, cmd nay tu dong dong)
echo.

REM Ghi log loi ra file de debug
pythonw app.py 2>"%~dp0app_error.log"

REM Neu pythonw khong start duoc, thu voi python thuong
if %errorLevel% neq 0 (
    echo    pythonw that bai, dang thu lai voi python...
    python app.py
    if %errorLevel% neq 0 (
        echo.
        echo    App gap loi! Xem file app_error.log de biet chi tiet.
        pause
    )
)