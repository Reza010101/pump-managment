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
                ORDER BY w.well_number
            ''').fetchall()
        else:
            # دریافت فقط اطلاعات چاه‌ها
            wells = conn.execute('''
                SELECT * FROM wells 
                ORDER BY well_number
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

def update_well(well_id, well_data):
    """
    بروزرسانی اطلاعات چاه
    """
    conn = get_db_connection()
    
    try:
        # فیلدهای قابل بروزرسانی
        update_fields = {
            'name': well_data.get('name'),
            'location': well_data.get('location'),
            'total_depth': well_data.get('total_depth'),
            'pump_installation_depth': well_data.get('pump_installation_depth'),
            'well_diameter': well_data.get('well_diameter'),
            'current_pump_brand': well_data.get('current_pump_brand'),
            'current_pump_model': well_data.get('current_pump_model'),
            'current_pump_power': well_data.get('current_pump_power'),
            'current_pump_phase': well_data.get('current_pump_phase'),
            'current_pipe_material': well_data.get('current_pipe_material'),
            'current_pipe_specs': well_data.get('current_pipe_specs'),
            'current_pipe_diameter': well_data.get('current_pipe_diameter'),
            'current_pipe_length_m': well_data.get('current_pipe_length_m'),
            'main_cable_specs': well_data.get('main_cable_specs'),
            'well_cable_specs': well_data.get('well_cable_specs'),
            'current_panel_specs': well_data.get('current_panel_specs'),
            'status': well_data.get('status', 'active'),
            'notes': well_data.get('notes'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # ساخت query داینامیک
        set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
        values = list(update_fields.values())
        values.append(well_id)
        
        query = f"UPDATE wells SET {set_clause} WHERE id = ?"
        
        conn.execute(query, values)
        conn.commit()
        
        return {'success': True, 'message': 'اطلاعات چاه با موفقیت بروزرسانی شد'}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': f'خطا در بروزرسانی چاه: {str(e)}'}
    finally:
        conn.close()

def create_maintenance_operation(operation_data):
    """
    ثبت عملیات تعمیر و نگهداری برای چاه
    """
    conn = get_db_connection()

    try:
        # minimal validation
        if not operation_data.get('well_id') or not operation_data.get('recorded_by_user_id'):
            return {'success': False, 'error': 'فیلد well_id و recorded_by_user_id الزامی است'}

        user_id = operation_data['recorded_by_user_id']
        # check user role/permission
        user = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return {'success': False, 'error': 'کاربر ثبت‌کننده یافت نشد'}
        role = user['role']
        if role not in ALLOWED_MAINTENANCE_ROLES:
            return {'success': False, 'error': 'شما مجوز ثبت تعمیرات را ندارید'}

        # start transaction
        conn.execute('BEGIN')

        # read current well values
        well_id = operation_data['well_id']
        old_well = conn.execute('SELECT * FROM wells WHERE id = ?', (well_id,)).fetchone()
        if not old_well:
            conn.execute('ROLLBACK')
            return {'success': False, 'error': 'چاه مورد نظر یافت نشد'}

        # handle well field updates if provided
        well_updates = operation_data.get('well_updates', {}) or {}

        allowed_fields = [
            'name', 'location', 'total_depth', 'pump_installation_depth', 'well_diameter',
            'current_pump_brand', 'current_pump_model', 'current_pump_power', 'current_pump_phase',
            'current_pipe_material', 'current_pipe_specs', 'current_pipe_diameter',
            'current_pipe_length_m', 'main_cable_specs', 'well_cable_specs', 'current_panel_specs',
            'status', 'notes'
        ]

        # changed_fields will be a list of field names; changed_values maps field -> [old, new]
        changed_fields = []
        changed_values = {}
        updates_to_apply = {}
        for key in allowed_fields:
            if key in well_updates:
                old_val = old_well[key] if key in old_well.keys() else None
                new_val = well_updates.get(key)
                # normalize for comparison
                old_s = '' if old_val is None else str(old_val)
                new_s = '' if new_val is None else str(new_val)
                if old_s != new_s:
                    changed_fields.append(key)
                    changed_values[key] = [old_val, new_val]
                    updates_to_apply[key] = new_val

        # if there are updates, perform update on wells
        if updates_to_apply:
            updates_to_apply['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            set_clause = ', '.join([f"{k} = ?" for k in updates_to_apply.keys()])
            values = list(updates_to_apply.values())
            values.append(well_id)
            conn.execute(f'UPDATE wells SET {set_clause} WHERE id = ?', values)

        # fetch snapshot of well after potential update
        new_well = conn.execute('SELECT * FROM wells WHERE id = ?', (well_id,)).fetchone()

        # prepare history metadata
        # recorded_date: prefer explicit operation_date, otherwise use today's date
        recorded_date = operation_data.get('operation_date') or datetime.now().strftime('%Y-%m-%d')
        reason = operation_data.get('operation_type') or operation_data.get('reason') or ''
        description = operation_data.get('description')
        parts_used = operation_data.get('parts_used')
        duration_minutes = operation_data.get('duration_minutes')
        new_status = operation_data.get('status')

        wh_changed_fields = json.dumps(changed_fields, ensure_ascii=False) if changed_fields else json.dumps([], ensure_ascii=False)
        wh_changed_values = json.dumps(changed_values, ensure_ascii=False) if changed_values else None
        # full snapshot as JSON (values from new_well)
        full_snapshot = json.dumps(dict(new_well) if new_well else {}, ensure_ascii=False)

        cur = conn.execute('''
            INSERT INTO wells_history (
                well_id, changed_by_user_id, change_type, changed_fields,
                changed_values, full_snapshot, description, parts_used, duration_minutes, new_status, recorded_time, recorded_date, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
        ''', (
            operation_data['well_id'],
            operation_data['recorded_by_user_id'],
            reason,
            wh_changed_fields,
            wh_changed_values,
            full_snapshot,
            description,
            parts_used,
            duration_minutes,
            new_status,
            recorded_date,
            reason
        ))

        maintenance_id = cur.lastrowid

        conn.execute('COMMIT')

        result = {'success': True, 'message': 'عملیات تعمیرات با موفقیت ثبت شد', 'maintenance_id': maintenance_id}
        if changed_fields:
            result['changed_fields'] = json.dumps(changed_fields, ensure_ascii=False)

        return result

    except Exception as e:
        try:
            conn.execute('ROLLBACK')
        except:
            pass
        return {'success': False, 'error': f'خطا در ثبت عملیات تعمیرات: {str(e)}'}
    finally:
        conn.close()

def get_well_maintenance_operations(well_id, limit=50):
    """
    دریافت تاریخچه عملیات تعمیرات یک چاه
    """
    conn = get_db_connection()
    
    try:
        operations = conn.execute('''
            SELECT 
                wh.*, wh.recorded_time as operation_date, NULL as operation_time,
                u.full_name as recorded_by_name,
                w.well_number,
                w.name as well_name
            FROM wells_history wh
            JOIN wells w ON wh.well_id = w.id
            JOIN users u ON wh.changed_by_user_id = u.id
            WHERE wh.well_id = ?
            ORDER BY wh.recorded_time DESC, wh.id DESC
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
                wh.*, wh.recorded_time as operation_date, NULL as operation_time,
                u.full_name as recorded_by_name,
                w.well_number,
                w.name as well_name
            FROM wells_history wh
            JOIN wells w ON wh.well_id = w.id
            JOIN users u ON wh.changed_by_user_id = u.id
            ORDER BY wh.recorded_time DESC, wh.id DESC
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
            SELECT change_type as operation_type, recorded_time as operation_date, description 
            FROM wells_history 
            WHERE well_id = ? 
            ORDER BY recorded_time DESC 
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