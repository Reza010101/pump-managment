# database/wells_operations.py
"""
عملیات دیتابیس برای مدیریت چاه‌ها
"""

from .models import get_db_connection
from datetime import datetime
import json

# Roles allowed to register maintenance. Adjust as needed.
ALLOWED_MAINTENANCE_ROLES = ('admin', 'maintenance', 'technician')

def get_all_wells(include_pump_info=True):
    """
    دریافت لیست تمام چاه‌ها
    """
    conn = get_db_connection()
    
    try:
        if include_pump_info:
            # دریافت چاه‌ها به همراه اطلاعات پمپ مربوطه
            wells = conn.execute('''
                SELECT 
                    w.*,
                    p.pump_number,
                    p.status as pump_status,
                    p.last_change as pump_last_change,
                    (SELECT action FROM pump_history 
                     WHERE pump_id = p.id 
                     ORDER BY event_time DESC LIMIT 1) as last_pump_action
                FROM wells w
                LEFT JOIN pumps p ON w.pump_id = p.id
                ORDER BY CAST(w.well_number AS INTEGER) ASC, w.well_number ASC
            ''').fetchall()
        else:
            # دریافت فقط اطلاعات چاه‌ها
            wells = conn.execute('''
                SELECT * FROM wells 
                ORDER BY CAST(well_number AS INTEGER) ASC, well_number ASC
            ''').fetchall()
        
        return wells
        
    except Exception as e:
        print(f"Error in get_all_wells: {e}")
        return []
    finally:
        conn.close()

def get_well_by_id(well_id, include_pump_info=True):
    """
    دریافت اطلاعات یک چاه بر اساس ID
    """
    conn = get_db_connection()
    
    try:
        if include_pump_info:
            well = conn.execute('''
                SELECT 
                    w.*,
                    p.pump_number,
                    p.status as pump_status,
                    p.last_change as pump_last_change,
                    p.name as pump_name,
                    p.location as pump_location
                FROM wells w
                LEFT JOIN pumps p ON w.pump_id = p.id
                WHERE w.id = ?
            ''', (well_id,)).fetchone()
        else:
            well = conn.execute('''
                SELECT * FROM wells 
                WHERE id = ?
            ''', (well_id,)).fetchone()
        
        return well
        
    except Exception as e:
        print(f"Error in get_well_by_id: {e}")
        return None
    finally:
        conn.close()

def get_well_by_pump_id(pump_id):
    """
    دریافت اطلاعات چاه بر اساس pump_id
    """
    conn = get_db_connection()
    
    try:
        well = conn.execute('''
            SELECT w.*, p.pump_number, p.status as pump_status
            FROM wells w
            JOIN pumps p ON w.pump_id = p.id
            WHERE w.pump_id = ?
        ''', (pump_id,)).fetchone()
        
        return well
        
    except Exception as e:
        print(f"Error in get_well_by_pump_id: {e}")
        return None
    finally:
        conn.close()

def get_well_by_well_number(well_number):
    """
    دریافت اطلاعات چاه بر اساس شماره چاه
    """
    conn = get_db_connection()
    
    try:
        well = conn.execute('''
            SELECT w.*, p.pump_number, p.status as pump_status
            FROM wells w
            LEFT JOIN pumps p ON w.pump_id = p.id
            WHERE w.well_number = ?
        ''', (well_number,)).fetchone()
        
        return well
        
    except Exception as e:
        print(f"Error in get_well_by_well_number: {e}")
        return None
    finally:
        conn.close()

def record_well_event(event_data):
    """
    Records a single event for a well, which can be a maintenance operation,
    a data update, or both. This is the new single source of truth for well history.
    """
    conn = get_db_connection()
    try:
        # --- 1. Validation ---
        well_id = event_data.get('well_id')
        user_id = event_data.get('recorded_by_user_id')
        operation_type = event_data.get('operation_type')
        operation_date = event_data.get('operation_date')

        if not all([well_id, user_id, operation_type, operation_date]):
            return {'success': False, 'error': 'اطلاعات ضروری (شناسه چاه، کاربر، نوع و تاریخ عملیات) ناقص است.'}

        # Check user permissions
        user = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user or user['role'] not in ALLOWED_MAINTENANCE_ROLES:
            return {'success': False, 'error': 'شما مجوز ثبت رویداد برای چاه را ندارید.'}

        conn.execute('BEGIN')

        # --- 2. Process Well Updates ---
        old_well = conn.execute('SELECT * FROM wells WHERE id = ?', (well_id,)).fetchone()
        if not old_well:
            conn.execute('ROLLBACK')
            return {'success': False, 'error': 'چاه مورد نظر یافت نشد.'}

        well_updates = event_data.get('well_updates', {})
        changed_fields = []
        changed_values = {}
        updates_to_apply = {}

        allowed_fields = [
            'name', 'location', 'total_depth', 'pump_installation_depth', 'well_diameter',
            'current_pump_brand', 'current_pump_model', 'current_pump_power',
            'current_pipe_material', 'current_pipe_diameter', 'current_pipe_length_m',
            'main_cable_specs', 'well_cable_specs', 'current_panel_specs', 'status'
        ]


        for key in allowed_fields:
            if key in well_updates:
                old_val = old_well[key]
                new_val = well_updates[key]
                # Compare values, treating None and empty strings as potentially different
                if str(old_val or '') != str(new_val or ''):
                    changed_fields.append(key)
                    changed_values[key] = {'old': old_val, 'new': new_val}
                    updates_to_apply[key] = new_val
        
        if updates_to_apply:
            updates_to_apply['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            set_clause = ', '.join([f"{k} = ?" for k in updates_to_apply])
            values = list(updates_to_apply.values())
            values.append(well_id)
            conn.execute(f'UPDATE wells SET {set_clause} WHERE id = ?', values)

        # --- 3. Record the Event in wells_history ---
        new_well = conn.execute('SELECT * FROM wells WHERE id = ?', (well_id,)).fetchone()
        full_snapshot = json.dumps(dict(new_well), ensure_ascii=False) if new_well else '{}'

        history_params = {
            'well_id': well_id,
            'changed_by_user_id': user_id,
            'operation_type': operation_type,
            'operation_date': operation_date,
            'performed_by': event_data.get('performed_by'),
            'changed_fields': json.dumps(changed_fields, ensure_ascii=False),
            'changed_values': json.dumps(changed_values, ensure_ascii=False) if changed_values else None,
            'full_snapshot': full_snapshot,
            'recorded_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'reason': event_data.get('notes') # Using notes field as the reason/description
        }

        # The 'change_type' column can be repurposed or be the same as operation_type
        history_params['change_type'] = operation_type

        sql = """
            INSERT INTO wells_history (
                well_id, changed_by_user_id, operation_type, operation_date, performed_by,
                change_type, changed_fields, changed_values, full_snapshot, recorded_time, reason
            ) VALUES (
                :well_id, :changed_by_user_id, :operation_type, :operation_date, :performed_by,
                :change_type, :changed_fields, :changed_values, :full_snapshot, :recorded_time, :reason
            )
        """
        cursor = conn.execute(sql, history_params)
        history_id = cursor.lastrowid

        conn.execute('COMMIT')

        return {
            'success': True, 
            'message': 'عملیات با موفقیت در تاریخچه چاه ثبت شد.', 
            'history_id': history_id
        }

    except Exception as e:
        if conn:
            conn.execute('ROLLBACK')
        return {'success': False, 'error': f'خطا در ثبت رویداد چاه: {str(e)}'}
    finally:
        if conn:
            conn.close()


def get_well_maintenance_operations(well_id, limit=50):
    """
    دریافت تاریخچه عملیات تعمیرات یک چاه
    """
    conn = get_db_connection()
    
    try:
        operations = conn.execute('''
            SELECT 
                wh.*,
                u.full_name as changed_by_user_name
            FROM wells_history wh
            JOIN users u ON wh.changed_by_user_id = u.id
            WHERE wh.well_id = ?
            ORDER BY wh.operation_date DESC, wh.id DESC
            LIMIT ?
        ''', (well_id, limit)).fetchall()
        
        return operations
        
    except Exception as e:
        print(f"Error in get_well_maintenance_operations: {e}")
        return []
    finally:
        conn.close()

def get_all_maintenance_operations(limit=100):
    """
    دریافت تمام عملیات تعمیرات
    """
    conn = get_db_connection()
    
    try:
        operations = conn.execute('''
            SELECT 
                wh.*,
                u.full_name as changed_by_user_name,
                w.well_number,
                w.name as well_name
            FROM wells_history wh
            JOIN users u ON wh.changed_by_user_id = u.id
            JOIN wells w ON wh.well_id = w.id
            ORDER BY wh.operation_date DESC, wh.id DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        
        return operations
        
    except Exception as e:
        print(f"Error in get_all_maintenance_operations: {e}")
        return []
    finally:
        conn.close()

def get_well_statistics(well_id):
    """
    دریافت آمار و اطلاعات آماری برای یک چاه
    """
    conn = get_db_connection()
    
    try:
        # تعداد عملیات تعمیرات
        maintenance_count = conn.execute(
            'SELECT COUNT(*) FROM wells_history WHERE well_id = ?',
            (well_id,)
        ).fetchone()[0]
        
        # آخرین عملیات تعمیرات (از wells_history)
        last_maintenance = conn.execute('''
            SELECT operation_type, operation_date
            FROM wells_history 
            WHERE well_id = ? 
            ORDER BY operation_date DESC 
            LIMIT 1
        ''', (well_id,)).fetchone()
        
        # اطلاعات پمپ مرتبط
        pump_info = conn.execute('''
            SELECT p.status, p.last_change
            FROM pumps p
            JOIN wells w ON w.pump_id = p.id
            WHERE w.id = ?
        ''', (well_id,)).fetchone()
        
        return {
            'maintenance_count': maintenance_count,
            'last_maintenance': dict(last_maintenance) if last_maintenance else None,
            'pump_status': pump_info['status'] if pump_info else None,
            'last_status_change': pump_info['last_change'] if pump_info else None
        }
        
    except Exception as e:
        print(f"Error in get_well_statistics: {e}")
        return {}
    finally:
        conn.close()

def search_wells(search_term):
    """
    جستجو در چاه‌ها
    """
    conn = get_db_connection()
    
    try:
        search_pattern = f'%{search_term}%'
        
        wells = conn.execute('''
            SELECT 
                w.*,
                p.pump_number,
                p.status as pump_status
            FROM wells w
            LEFT JOIN pumps p ON w.pump_id = p.id
            WHERE w.well_number LIKE ? 
               OR w.name LIKE ? 
               OR w.location LIKE ?
               OR w.current_pump_brand LIKE ?
               OR w.current_pump_model LIKE ?
            ORDER BY w.well_number
        ''', (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern)).fetchall()
        
        return wells
        
    except Exception as e:
        print(f"Error in search_wells: {e}")
        return []
    finally:
        conn.close()