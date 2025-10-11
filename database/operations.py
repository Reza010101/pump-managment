from datetime import datetime
from .models import get_db_connection
from utils.date_utils import jalali_to_gregorian, gregorian_to_jalali

def change_pump_status(pump_id, action, user_id, reason, notes, manual_time=False, action_date_jalali=None, action_time=None):
    """تغییر وضعیت پمپ"""
    conn = get_db_connection()
    
    try:
        current_pump = conn.execute(
            'SELECT status FROM pumps WHERE id = ?', (pump_id,)
        ).fetchone()
        
        if not current_pump:
            return {'success': False, 'error': 'پمپ پیدا نشد'}
        
        current_status = current_pump['status']
        new_status = True if action.upper() == 'ON' else False
        
        if current_status == new_status and get_last_pump_event_time(pump_id):
            return {
                'success': False, 
                'error': f'پمپ در حال حاضر {"روشن" if current_status else "خاموش"} است'
            }
        
        event_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        recorded_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if manual_time and action_date_jalali and action_time:
            jalali_datetime_str = f"{action_date_jalali} {action_time}:00"
            event_time = jalali_to_gregorian(jalali_datetime_str)
            
            last_event_time = get_last_pump_event_time(pump_id)
            if last_event_time and event_time <= last_event_time:
                last_event_jalali = gregorian_to_jalali(last_event_time)
                return {
                    'success': False, 
                    'error': f'تاریخ انتخاب شده باید بعد از آخرین ثبت ({last_event_jalali[:16]}) باشد'
                }

        conn.execute(
            'UPDATE pumps SET status = ?, last_change = ? WHERE id = ?',
            (new_status, event_time, pump_id)
        )
        
        conn.execute(
            '''INSERT INTO pump_history 
            (pump_id, user_id, action, event_time, recorded_time, reason, notes, manual_time) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (pump_id, user_id, action.upper(), event_time, recorded_time, reason, notes, manual_time)
        )
        
        conn.commit()
        
        return {
            'success': True, 
            'message': f'پمپ با موفقیت {"روشن" if new_status else "خاموش"} شد'
        }
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def get_last_pump_event_time(pump_id):
    """دریافت آخرین زمان رویداد پمپ"""
    conn = get_db_connection()
    last_event = conn.execute(
        'SELECT event_time FROM pump_history WHERE pump_id = ? ORDER BY event_time DESC LIMIT 1',
        (pump_id,)
    ).fetchone()
    conn.close()
    return last_event['event_time'] if last_event else None

def update_pump_current_status():
    """بروزرسانی وضعیت فعلی پمپ‌ها بر اساس آخرین رویداد"""
    conn = get_db_connection()
    
    for pump_id in range(1, 59):
        last_event = conn.execute('''
            SELECT action, event_time 
            FROM pump_history 
            WHERE pump_id = ? 
            ORDER BY event_time DESC, id DESC
            LIMIT 1
        ''', (pump_id,)).fetchone()
        
        if last_event:
            current_status = 1 if last_event['action'].upper() == 'ON' else 0
            conn.execute(
                'UPDATE pumps SET status = ?, last_change = ? WHERE id = ?',
                (current_status, last_event['event_time'], pump_id)
            )
        else:
            conn.execute(
                'UPDATE pumps SET status = 0, last_change = CURRENT_TIMESTAMP WHERE id = ?',
                (pump_id,)
            )
    
    conn.commit()
    conn.close()