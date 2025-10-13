from flask import Flask
from config import get_config

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp
from blueprints.pumps import pumps_bp
from blueprints.reports import reports_bp
from blueprints.admin import admin_bp
from blueprints.records_management import records_bp


def create_app():
    """
    ایجاد و پیکربندی برنامه Flask
    """
    app = Flask(__name__)
    app.config.from_object(get_config())
    
    # ثبت blueprintها
    register_blueprints(app)
    
    # ثبت error handlers
    register_error_handlers(app)
    
    return app

def register_blueprints(app):
    """ثبت تمام blueprintهای برنامه"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pumps_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(records_bp)


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