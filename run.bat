@echo off
chcp 65001 >nul
title سیستم مدیریت پمپ‌ها - نسخه ماژولار

echo ======================================
echo    سیستم مدیریت پمپ‌ها - اجرای خودکار
echo ======================================
echo.

echo 🔍 بررسی محیط پایتون...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ پایتون پیدا نشد! لطفا پایتون را نصب کنید.
    echo 📥 از سایت python.org دانلود کنید
    pause
    exit /b 1
)

echo ✅ پایتون پیدا شد

echo 🔍 بررسی نیازمندی‌ها...
python -c "import flask, pandas, openpyxl, jdatetime" >nul 2>&1
if errorlevel 1 (
    echo 📦 در حال نصب نیازمندی‌ها...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ خطا در نصب نیازمندی‌ها
        pause
        exit /b 1
    )
    echo ✅ نیازمندی‌ها نصب شدند
) else (
    echo ✅ تمام نیازمندی‌ها نصب هستند
)

echo 🔍 بررسی دیتابیس...
if not exist "pump_management.db" (
    echo 🗃️ در حال ساخت دیتابیس...
    python create_database.py
    if errorlevel 1 (
        echo ❌ خطا در ساخت دیتابیس
        pause
        exit /b 1
    )
    echo ✅ دیتابیس ساخته شد
) else (
    echo ✅ دیتابیس موجود است
)

echo.
echo 🚀 در حال اجرای سرور...
echo.
echo 🌐 آدرس‌های دسترسی:
echo    - این کامپیوتر: http://localhost:5000
echo    - سایر کامپیوترها: http://[آی‌پی-این-کامپیوتر]:5000
echo.
echo 👤 کاربران پیشفرض:
echo    - مدیر سیستم: admin / 1234
echo    - کاربر معمولی: user1 / 1234
echo.
echo ⏹️  برای توقف: Ctrl+C
echo ======================================
echo.

python run.py

if errorlevel 1 (
    echo.
    echo ❌ خطا در اجرای برنامه
    echo 🔧 مشکل احتمالی: پورت 5000 occupied است
    echo 💡 راه‌حل: برنامه دیگری که از پورت 5000 استفاده می‌کند را ببندید
    pause
)