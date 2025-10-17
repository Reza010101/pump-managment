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
    
    try:
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
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating pump status: {e}")
        raise
    finally:
        conn.close()

    # اضافه کردن این توابع به انتهای فایل operations.py

def get_last_event_before(pump_id, datetime_obj):
    """پیدا کردن آخرین رویداد قبل از زمان مشخص"""
    conn = get_db_connection()
    event = conn.execute('''
        SELECT action, event_time 
        FROM pump_history 
        WHERE pump_id = ? AND event_time < ?
        ORDER BY event_time DESC 
        LIMIT 1
    ''', (pump_id, datetime_obj.strftime('%Y-%m-%d %H:%M:%S'))).fetchone()
    conn.close()
    
    if event:
        return {
            'action': event['action'],
            'event_time': datetime.strptime(event['event_time'], '%Y-%m-%d %H:%M:%S')
        }
    return None

def get_pump_events_in_range(pump_id, start_time, end_time):
    """دریافت رویدادهای یک پمپ در بازه زمانی مشخص"""
    conn = get_db_connection()
    events = conn.execute('''
        SELECT action, event_time 
        FROM pump_history 
        WHERE pump_id = ? AND event_time BETWEEN ? AND ?
        ORDER BY event_time
    ''', (pump_id, start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'))).fetchall()
    conn.close()
    
    result = []
    for event in events:
        result.append({
            'action': event['action'],
            'event_time': datetime.strptime(event['event_time'], '%Y-%m-%d %H:%M:%S')
        })
    return result

def get_pump_history_from_db(pump_number):
    """دریافت تاریخچه یک پمپ خاص از دیتابیس"""
    conn = get_db_connection()
    
    pump = conn.execute(
        'SELECT id FROM pumps WHERE pump_number = ?', (pump_number,)
    ).fetchone()
    
    if not pump:
        conn.close()
        return []
    
    pump_id = pump['id']
    
    history = conn.execute('''
        SELECT action, event_time, reason, notes 
        FROM pump_history 
        WHERE pump_id = ? 
        ORDER BY event_time
    ''', (pump_id,)).fetchall()
    
    conn.close()
    
    events = []
    for event in history:
        events.append({
            'action': event['action'],
            'event_time': event['event_time'],
            'reason': event['reason'],
            'notes': event['notes'],
            'source': 'existing'
        })
    
    return events

# اضافه کردن این توابع به database/operations.py

def can_delete_record(record_id, user_id, user_role):
    """
    بررسی آیا کاربر می‌تواند رکورد را حذف کند
    """
    conn = get_db_connection()
    
    try:
        # دریافت اطلاعات رکورد
        record = conn.execute('''
            SELECT ph.*, p.pump_number, u.username as original_username
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            JOIN users u ON ph.user_id = u.id
            WHERE ph.id = ?
        ''', (record_id,)).fetchone()
        
        if not record:
            return False, "رکورد یافت نشد"
        
        # بررسی آخرین رکورد بودن
        last_record = conn.execute('''
            SELECT id FROM pump_history 
            WHERE pump_id = ? 
            ORDER BY event_time DESC, id DESC 
            LIMIT 1
        ''', (record['pump_id'],)).fetchone()
        
        if not last_record or last_record['id'] != record_id:
            return False, "فقط آخرین رکورد قابل حذف است"
        
        # بررسی دسترسی کاربر
        if user_role != 'admin' and record['user_id'] != user_id:
            return False, "شما فقط می‌توانید رکوردهای خود را حذف کنید"
        
        # بررسی محدودیت زمانی برای کاربران عادی
        if user_role != 'admin':
            from datetime import datetime, timedelta
            record_time = datetime.strptime(record['recorded_time'], '%Y-%m-%d %H:%M:%S')
            time_diff = datetime.now() - record_time
            
            if time_diff > timedelta(hours=48):
                return False, "فقط رکوردهای ۴۸ ساعت گذشته قابل حذف هستند"
        
        return True, "قابل حذف"
        
    except Exception as e:
        return False, f"خطا در بررسی: {str(e)}"
    finally:
        conn.close()

def delete_pump_record(record_id, deletion_reason, deleted_by_user_id):
    """
    حذف رکورد و بروزرسانی وضعیت پمپ
    """
    conn = get_db_connection()
    
    try:
        # شروع تراکنش
        conn.execute('BEGIN TRANSACTION')
        
        # ۱. دریافت اطلاعات کامل رکورد قبل از حذف
        record = conn.execute('''
            SELECT ph.*, p.pump_number, u.username as original_username,
                   u2.username as deleted_by_username
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            JOIN users u ON ph.user_id = u.id
            JOIN users u2 ON u2.id = ?
            WHERE ph.id = ?
        ''', (deleted_by_user_id, record_id)).fetchone()
        
        if not record:
            raise Exception("رکورد یافت نشد")
        
        # ۲. ذخیره در لاگ حذف
        conn.execute('''
            INSERT INTO deletion_logs 
            (deleted_record_id, pump_id, pump_number, original_action, 
             original_event_time, original_reason, original_notes,
             original_user_id, original_user_name, deleted_by_user_id,
             deleted_by_user_name, deletion_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_id, record['pump_id'], record['pump_number'],
            record['action'], record['event_time'], record['reason'],
            record['notes'] or '', record['user_id'], record['original_username'],
            deleted_by_user_id, record['deleted_by_username'], deletion_reason
        ))
        
        # ۳. حذف رکورد از تاریخچه
        conn.execute('DELETE FROM pump_history WHERE id = ?', (record_id,))
        
        # ۴. بروزرسانی وضعیت پمپ
        update_pump_current_status()
        
        # تأیید تراکنش
        conn.commit()
        
        return True, "رکورد با موفقیت حذف شد"
        
    except Exception as e:
        conn.rollback()
        return False, f"خطا در حذف رکورد: {str(e)}"
    finally:
        conn.close()

def get_pump_records_with_pagination(pump_id, page=1, per_page=20):
    """
    دریافت رکوردهای یک پمپ با صفحه‌بندی
    """
    conn = get_db_connection()
    
    try:
        offset = (page - 1) * per_page
        
        # دریافت رکوردها
        records = conn.execute('''
            SELECT ph.*, p.pump_number, p.name as pump_name,
                   u.username, u.full_name,
                   (SELECT COUNT(*) FROM pump_history WHERE pump_id = p.id) as total_records
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            JOIN users u ON ph.user_id = u.id
            WHERE p.id = ?
            ORDER BY ph.event_time DESC, ph.id DESC
            LIMIT ? OFFSET ?
        ''', (pump_id, per_page, offset)).fetchall()
        
        # تعداد کل رکوردها
        total = conn.execute(
            'SELECT COUNT(*) FROM pump_history WHERE pump_id = ?', 
            (pump_id,)
        ).fetchone()[0]
        
        return {
            'records': records,
            'total_records': total,
            'total_pages': (total + per_page - 1) // per_page,
            'current_page': page,
            'per_page': per_page
        }
        
    except Exception as e:
        return {'records': [], 'total_records': 0, 'total_pages': 0, 'error': str(e)}
    finally:
        conn.close()

def get_pump_history_from_db(pump_number):
    """دریافت تاریخچه یک پمپ خاص از دیتابیس"""
    conn = get_db_connection()
    
    try:
        # پیدا کردن pump_id از pump_number
        pump = conn.execute(
            'SELECT id FROM pumps WHERE pump_number = ?', (pump_number,)
        ).fetchone()
        
        if not pump:
            return []
        
        pump_id = pump['id']
        
        # دریافت تاریخچه پمپ
        history = conn.execute('''
            SELECT action, event_time, reason, notes 
            FROM pump_history 
            WHERE pump_id = ? 
            ORDER BY event_time
        ''', (pump_id,)).fetchall()
        
        events = []
        for event in history:
            events.append({
                'action': event['action'],
                'event_time': event['event_time'],
                'reason': event['reason'],
                'notes': event['notes'],
                'source': 'existing'
            })
        
        return events
        
    except Exception as e:
        print(f"Error getting pump history: {e}")
        return []
    finally:
        conn.close()