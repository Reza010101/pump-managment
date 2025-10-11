#!/usr/bin/env python3
"""
تست نهایی importهای پروژه
"""
import sys
import os

# اضافه کردن مسیر جاری به sys.path برای imports بهتر
sys.path.insert(0, os.path.dirname(__file__))

print("🧪 تست نهایی importهای پروژه...")

try:
    print("1. تست importهای اصلی...")
    import app
    import config
    import run
    print("   ✅ app, config, run - OK")

    print("2. تست blueprints...")
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.pumps import pumps_bp
    from blueprints.reports import reports_bp
    from blueprints.admin import admin_bp
    print("   ✅ تمام blueprints - OK")

    print("3. تست database...")
    from database.models import get_db_connection
    from database.operations import change_pump_status
    from database.reports import calculate_daily_operating_hours
    from database.users import get_all_users
    print("   ✅ تمام database modules - OK")

    print("4. تست utils...")
    from utils.date_utils import gregorian_to_jalali, jalali_to_gregorian
    from utils.export_utils import export_operating_hours_to_excel
    print("   ✅ تمام utils - OK")

    print("\n🎉 🎉 🎉")
    print("✅ ساختار ماژولار کاملاً کار می‌کند!")
    print("✅ تمام importها موفقیت‌آمیز بودند!")
    print("✅ حالا می‌تونی برنامه رو اجرا کنی: python run.py")

except Exception as e:
    print(f"\n❌ خطا: {e}")
    import traceback
    traceback.print_exc()
    