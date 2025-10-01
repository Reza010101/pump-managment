@echo off
chcp 65001
title Pump Management System - Running
echo ======================================
echo    Pump Management System
echo ======================================
echo.

echo Starting server...
echo Access URLs:
echo    - This computer: http://localhost:5000
echo    - Other computers: http://[THIS-IP]:5000
echo.
echo Press Ctrl+C to stop
echo.

venv\Scripts\python app.py
pause