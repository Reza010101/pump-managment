import os

class Config:
    """
    تنظیمات اصلی برنامه
    """
    SECRET_KEY = 'pump_management_secret_key_2024'
    DATABASE_PATH = 'pump_management.db'
    
    # تنظیمات آپلود فایل
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    # تنظیمات session
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # تنظیمات گزارشات
    REPORTS_PER_PAGE = 50

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# انتخاب کانفیگ بر اساس محیط
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """دریافت تنظیمات بر اساس محیط اجرا"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])