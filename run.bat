@echo off
chcp 65001 >nul
title سیستم مدیریت پمپ‌ها - نسخه ماژولار

echo ======================================
echo    سیستم مدیریت پمپ‌ها - اجرای خودکار
echo ======================================
echo.

echo 🔍 بررسی محیط پایتون...
python --version >nul 2>&1
if not errorlevel 1 goto python_ok

py --version >nul 2>&1
if not errorlevel 1 goto py_ok

python3 --version >nul 2>&1
if not errorlevel 1 goto python3_ok

echo ❌ پایتون پیدا نشد! لطفا پایتون را نصب کنید.
echo 📥 از سایت python.org دانلود کنید
echo 💡 هنگام نصب، تیک 'Add Python to PATH' را بزنید
pause
exit /b 1

:python_ok
set PY_CMD=python
goto check_requirements

:py_ok
set PY_CMD=py
goto check_requirements

:python3_ok
set PY_CMD=python3
goto check_requirements

:check_requirements
echo ✅ پایتون پیدا شد (%PY_CMD%)

echo 🔍 بررسی نیازمندی‌ها...
%PY_CMD% -c "import flask, pandas, openpyxl, jdatetime" >nul 2>&1
if not errorlevel 1 goto requirements_ok

echo 📦 در حال نصب نیازمندی‌ها...
%PY_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ خطا در نصب نیازمندی‌ها
    pause
    exit /b 1
)
echo ✅ نیازمندی‌ها نصب شدند
goto check_database

:requirements_ok
echo ✅ تمام نیازمندی‌ها نصب هستند

:check_database
echo 🔍 بررسی دیتابیس...
if not exist "pump_management.db" (
    echo 🗃️ در حال ساخت دیتابیس...
    %PY_CMD% create_database.py
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

%PY_CMD% run.py

if errorlevel 1 (
    echo.
    echo ❌ خطا در اجرای برنامه
    echo 🔧 مشکل احتمالی: پورت 5000 occupied است
    echo 💡 راه‌حل: برنامه دیگری که از پورت 5000 استفاده می‌کند را ببندید
    pause
)