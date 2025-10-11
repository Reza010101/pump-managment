from flask import Blueprint, render_template, session, redirect
from database.models import get_all_pumps
from utils.date_utils import gregorian_to_jalali

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    pumps = get_all_pumps()
    pumps_with_jalali = []
    
    for pump in pumps:
        pump_dict = dict(pump)
        pump_dict['has_history'] = pump['has_history']
        
        if pump['last_action']:
            pump_dict['status'] = 1 if pump['last_action'] == 'ON' else 0
        else:
            pump_dict['status'] = 0
            
        if pump['last_change']:
            pump_dict['last_change_jalali'] = gregorian_to_jalali(pump['last_change'])
        else:
            pump_dict['last_change_jalali'] = 'بدون تاریخچه'
        pumps_with_jalali.append(pump_dict)
    
    return render_template('dashboard.html', pumps=pumps_with_jalali)