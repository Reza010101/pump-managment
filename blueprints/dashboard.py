from flask import Blueprint, render_template, session, redirect
from database.models import get_all_pumps
from utils.date_utils import gregorian_to_jalali
from datetime import datetime
from database.wells_operations import get_well_by_pump_id


dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    pumps = get_all_pumps()
    pumps_with_well_status = []
    
    for pump in pumps:
        pump_dict = dict(pump)
        pump_dict['has_history'] = pump['has_history']
        
        # دریافت وضعیت چاه مرتبط
        well = get_well_by_pump_id(pump['id'])
        if well:
            pump_dict['well_status'] = well['status']
            pump_dict['well_id'] = well['id']
        else:
            pump_dict['well_status'] = 'active'  # حالت پیشفرض
            pump_dict['well_id'] = None
            
        if pump['last_action']:
            pump_dict['status'] = 1 if pump['last_action'] == 'ON' else 0
        else:
            pump_dict['status'] = 0
            
        if pump['last_change']:
            pump_dict['last_change_jalali'] = gregorian_to_jalali(pump['last_change'])
        else:
            pump_dict['last_change_jalali'] = 'بدون تاریخچه'
            
        pumps_with_well_status.append(pump_dict)
    
    return render_template('dashboard.html', pumps=pumps_with_well_status)

def check_deletion_alerts(user_id):
    """نمایش الارم حذف‌ها - یک بار در روز برای هر کاربر"""
    from database.models import get_db_connection
    
    conn = get_db_connection()
    
    try:
        # حذف‌های 24 ساعت گذشته
        recent_deletions = conn.execute('''
            SELECT dl.pump_number, u.username as deleted_by_username
            FROM deletion_logs dl
            JOIN users u ON dl.deleted_by_user_id = u.id
            WHERE dl.deleted_at >= datetime('now', '-24 hours')
            ORDER BY dl.deleted_at DESC
        ''').fetchall()
        
        if not recent_deletions:
            return
        
        # 🎯 بررسی برای کاربر خاص - نه همه کاربران
        today = datetime.now().strftime('%Y-%m-%d')
        
        # ایجاد کلید منحصر به فرد برای هر کاربر
        user_alert_key = f'last_deletion_alert_date_{user_id}'
        
        # اگر کاربر امروز این الارم را ندیده است
        if session.get(user_alert_key) != today:
            # ایجاد پیام
            if len(recent_deletions) == 1:
                message = f'🗑️ حذف رکورد مربوط به پمپ {recent_deletions[0]["pump_number"]} توسط کاربر {recent_deletions[0]["deleted_by_username"]}'
            else:
                unique_pumps = set(deletion['pump_number'] for deletion in recent_deletions)
                pumps_list = "، ".join([f'پمپ {pump}' for pump in sorted(unique_pumps)[:3]])
                if len(unique_pumps) > 3:
                    pumps_list += f" و {len(unique_pumps) - 3} پمپ دیگر"
                message = f'🗑️ حذف رکوردهای مربوط به {pumps_list} در 24 ساعت گذشته'
            
            from flask import flash
            flash(message, 'warning')
            
            # ذخیره تاریخ برای این کاربر خاص
            session[user_alert_key] = today
            session.modified = True
            
            print(f"✅ الارم نمایش داده شد برای کاربر {user_id} در تاریخ {today}")
        
    except Exception as e:
        print(f"خطا در بررسی الارم حذف: {e}")
    finally:
        conn.close()
