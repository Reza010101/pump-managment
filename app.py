from flask import Flask
from config import get_config

def create_app():
    """
    ایجاد و پیکربندی برنامه Flask
    """
    app = Flask(__name__)
    app.config.from_object(get_config())
    
    # ثبت blueprintها (بعداً اضافه می‌شوند)
    register_blueprints(app)
    
    # ثبت error handlers (بعداً اضافه می‌شوند)
    register_error_handlers(app)
    
    return app

def register_blueprints(app):
    """ثبت تمام blueprintهای برنامه"""
    # بعداً import و register می‌شوند
    pass

def register_error_handlers(app):
    """ثبت handlerهای خطا"""
    @app.errorhandler(404)
    def not_found(error):
        return "صفحه مورد نظر یافت نشد!", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return "خطای داخلی سرور!", 500

# ایجاد نمونه برنامه
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)