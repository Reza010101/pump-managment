from flask import Flask, session, redirect
import os
import json
from datetime import timedelta

# Import the blueprint OBJECTS from their respective files (use the actual variable names)
from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp
from blueprints.pumps import pumps_bp
from blueprints.records_management import records_bp
from blueprints.reports import reports_bp
from blueprints.admin import admin_bp
from blueprints.wells import wells_bp

# Import utility functions
from utils.date_utils import gregorian_to_jalali

# 1. Create the Flask app instance
app = Flask(__name__)

# 2. Configure the app
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=1)

# 3. Define template filters AFTER the app is created
@app.template_filter('jalali')
def jalali_filter(value, include_time=False):
    """Custom template filter to convert Gregorian date to Jalali."""
    if not value:
        return ""
    return gregorian_to_jalali(value, include_time=include_time)


@app.template_filter('from_json')
def from_json_filter(value):
    """Custom template filter to parse a JSON string in templates."""
    if value:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None
    return None

# Also expose as a template global so templates can call `from_json(...)` directly
app.jinja_env.globals['from_json'] = from_json_filter

# 4. Register all blueprint objects
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(pumps_bp)
app.register_blueprint(records_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(wells_bp)

# Default route to redirect to login
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

# 5. Run the app
if __name__ == '__main__':
    # Use host='0.0.0.0' to make the server accessible from other devices on the network
    app.run(debug=True, host='0.0.0.0')
