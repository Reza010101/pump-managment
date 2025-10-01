@echo off
chcp 65001
title Pump Management System - Installation
echo ======================================
echo    Pump Management System Setup
echo ======================================
echo.

echo Installing Python environment...
python -m venv venv

echo Installing required packages...
venv\Scripts\pip install flask

echo Creating database...
venv\Scripts\python database.py

echo.
echo ✅ Installation completed successfully!
echo.
echo 🚀 To run the system:
echo   1. Double-click run.bat
echo   2. Open your browser
echo   3. Go to: http://localhost:5000
echo   4. Login with: admin / 1234
echo.
pause