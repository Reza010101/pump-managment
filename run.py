#!/usr/bin/env python3
"""
فایل اصلی اجرای برنامه
"""
import os
import sys

# اضافه کردن مسیر پروژه به sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from config import get_config

def main():
    """تابع اصلی اجرای برنامه"""
    app.config.from_object(get_config())
    
    print("🚀 سیستم مدیریت پمپ‌ها در حال اجراست...")
    print("📧 برای ورود: http://localhost:5000/login")
    print("   کاربران پیشفرض:")
    print("   - admin / 1234 (مدیر سیستم)")
    print("   - user1 / 1234 (کاربر معمولی)")
    print("   - برای توقف: Ctrl+C")
    print("=" * 50)
    
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()