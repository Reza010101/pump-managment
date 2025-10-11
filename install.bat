@echo off
chcp 65001 >nul
title نصب سیستم مدیریت پمپ‌ها

echo ======================================
echo    نصب سیستم مدیریت پمپ‌ها
echo ======================================
echo.

echo 🔍 بررسی پایتون...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ پایتون پیدا نشد!
    echo 📥 لطفا از سایت python.org دانلود و نصب کنید
    echo 💡 هنگام نصب، گزینه 'Add Python to PATH' را انتخاب کنید
    pause
    exit /b 1
)

echo ✅ پایتون پیدا شد

echo 📦 در حال نصب نیازمندی‌ها...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ خطا در نصب نیازمندی‌ها
    pause
    exit /b 1
)

echo 🗃️ در حال ساخت دیتابیس...
python create_database.py
if errorlevel 1 (
    echo ❌ خطا در ساخت دیتابیس
    pause
    exit /b 1
)

echo.
echo ✅ نصب با موفقیت کامل شد!
echo.
echo 🚀 برای اجرای سیستم:
echo    - دابل-کلیک روی run.bat
echo.
echo 👤 کاربران پیشفرض:
echo    - admin / 1234 (مدیر)
echo    - user1 / 1234 (کاربر)
echo.

pause