@echo off
chcp 65001 >nul
title نمایش آی‌پی سیستم

echo ======================================
echo    آدرس‌های دسترسی به سیستم
echo ======================================
echo.

echo 🔍 در حال پیدا کردن آی‌پی‌ها...
echo.

for /f "tokens=1-2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    echo 🌐 %%a : %%b
)

echo.
echo 🌐 آدرس‌های دسترسی:
echo    - این کامپیوتر: http://localhost:5000
echo    - سایر کامپیوترها: http://[آی‌پی-بالا]:5000
echo.
echo 📋 برای کپی کردن آی‌پی، آن را انتخاب کرده و Ctrl+C بزنید
echo.

pause