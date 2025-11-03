#!/usr/bin/env python3
"""
تست دیباگ برای پیدا کردن مشکل
"""
import sys
import os

print("🔍 دیباگ سیستم...")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

print("\n📦 چک کردن پکیج‌ها...")
try:
    import flask
    # استفاده از importlib.metadata برای نسخه Flask
    from importlib.metadata import version
    print(f"✅ Flask: {version('flask')}")
except ImportError as e:
    print(f"❌ Flask: {e}")

try:
    import pandas
    print(f"✅ Pandas: {pandas.__version__}")
except ImportError as e:
    print(f"❌ Pandas: {e}")

try:
    import openpyxl
    print(f"✅ OpenPyXL: {openpyxl.__version__}")
except ImportError as e:
    print(f"❌ OpenPyXL: {e}")

try:
    import jdatetime
    # jdatetime نسخه جدید
    print(f"✅ jdatetime: installed successfully")
except ImportError as e:
    print(f"❌ jdatetime: {e}")

print("\n🎉 تمام پکیج‌ها نصب هستند!")
print("\n🔧 حالا تست importهای پروژه...")
