from flask import Flask, session, redirect, flash, request
import os
import json
from datetime import timedelta, datetime

# Import the blueprint OBJECTS from their respective files (use the actual variable names)
from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp
from blueprints.pumps import pumps_bp
from blueprints.records_management import records_bp
from blueprints.reports import reports_bp
from blueprints.admin import admin_bp
from blueprints.setup import setup_bp
from blueprints.wells import wells_bp

# Import utility functions
from utils.date_utils import gregorian_to_jalali

# 1. Create the Flask app instance
app = Flask(__name__)

# 2. Configure the app
app.secret_key = os.urandom(24)
# Set inactivity timeout to 1 hour (sliding window)
app.permanent_session_lifetime = timedelta(hours=1)


@app.before_request
def _check_session_timeout():
    """Enforce inactivity timeout: if user is logged in and last activity
    was more than permanent_session_lifetime seconds ago, clear session and
    force re-login. Otherwise update last_activity (sliding expiration).
    """
    try:
        # Only enforce for authenticated sessions
        if 'user_id' in session:
            # ensure Flask treats this as a permanent session
            session.permanent = True

            now = datetime.utcnow().timestamp()
            last = session.get('last_activity')
            lifetime = app.permanent_session_lifetime.total_seconds()

            if last is not None:
                try:
                    elapsed = now - float(last)
                except Exception:
                    elapsed = 0

                if elapsed > lifetime:
                    # expire session
                    session.clear()
                    flash('نشست شما منقضی شد؛ لطفاً دوباره وارد شوید.', 'error')
                    return redirect('/login')

            # update sliding last_activity
            session['last_activity'] = now
    except Exception:
        # be conservative: don't break requests on unexpected errors here
        pass

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
app.register_blueprint(setup_bp)
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
