@echo off
title Smart Attendance System — Flask Server
echo.
echo ============================================================
echo   SMART ATTENDANCE SYSTEM
echo   Starting Flask Backend Server...
echo ============================================================
echo.

REM Always run from the project root (this script's directory)
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [!] No venv found — using system Python.
    echo     To set up: python -m venv venv ^&^& pip install -r requirements.txt
)

echo.
echo [*] Working directory : %cd%
echo [*] Starting server   : http://127.0.0.1:5000
echo.

python BACKEND\app.py

pause
