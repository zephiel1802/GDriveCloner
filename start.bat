@echo off
REM ============================================================
REM  GDriveCloner - Start Script (Windows)
REM ============================================================

title GDriveCloner Launcher
cd /d "%~dp0"

REM ── 1. Xin quyen Admin ───────────────────────────────────────
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [GDriveCloner] Dang yeu cau quyen Administrator...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

echo.
echo ============================================================
echo   GDriveCloner Launcher
echo ============================================================
echo.

REM ── 2. Kiem tra Python ──────────────────────────────────────
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [LOI] Khong tim thay Python! Vui long cai dat Python 3.9+ tu https://python.org
    pause
    exit /b 1
)

REM ── 3. Cai dat thu vien ─────────────────────────────────────
echo [1/2] Dang cai dat/kiem tra dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo [LOI] Cai dat dependencies that bai!
    pause
    exit /b 1
)
echo      Dependencies da san sang!

REM ── 4. Khoi dong ung dung ───────────────────────────────────
echo [2/2] Dang khoi dong GDriveCloner...
python app.py
if %errorLevel% neq 0 (
    echo [LOI] Ung dung bi loi khi khoi dong.
    pause
)
