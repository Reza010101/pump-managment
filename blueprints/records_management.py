from flask import Blueprint, render_template, request, session, redirect, flash, jsonify
from database.models import get_db_connection, get_all_pumps
from database.operations import (
    update_pump_current_status
)

# توابع جدید را مستقیماً در این فایل تعریف می‌کنیم
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
    حذف رکورد - نسخه ساده‌تر برای جلوگیری از lock
    """
    try:
        # ۱. ابتدا اطلاعات رکورد را بگیریم
        conn1 = get_db_connection()
        record = conn1.execute('''
            SELECT ph.*, p.pump_number, u.username as original_username,
                   u2.full_name as deleted_by_name
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            JOIN users u ON ph.user_id = u.id
            JOIN users u2 ON u2.id = ?
            WHERE ph.id = ?
        ''', (deleted_by_user_id, record_id)).fetchone()
        conn1.close()
        
        if not record:
            return False, "رکورد یافت نشد"
        
        # ۲. عملیات حذف در یک connection جداگانه
        conn2 = get_db_connection()
        
        # ذخیره در لاگ حذف
        conn2.execute('''
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
            deleted_by_user_id, record['deleted_by_name'], deletion_reason
        ))
        
        # حذف رکورد از تاریخچه
        conn2.execute('DELETE FROM pump_history WHERE id = ?', (record_id,))
        
        conn2.commit()
        conn2.close()
        
        # ۳. بروزرسانی وضعیت پمپ
        update_pump_current_status()
        
        return True, "رکورد با موفقیت حذف شد"
        
    except Exception as e:
        return False, f"خطا در حذف رکورد: {str(e)}"

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
                   u.username, u.full_name
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

# ایجاد Blueprint
records_bp = Blueprint('records', __name__)

@records_bp.route('/manage-records')
def manage_records():
    """صفحه اصلی مدیریت رکوردها"""
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')
    
    pumps = get_all_pumps()
    return render_template('manage_records.html', pumps=pumps)

@records_bp.route('/api/records/pump/<int:pump_id>')
def get_pump_records(pump_id):
    """API دریافت رکوردهای یک پمپ با صفحه‌بندی"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'لطفا ابتدا وارد شوید'})
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20  # ثابت - 20 رکورد در هر صفحه
        
        result = get_pump_records_with_pagination(pump_id, page, per_page)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']})
        
        # تبدیل رکوردها به فرمت قابل نمایش
        records_data = []
        for record in result['records']:
            records_data.append({
                'id': record['id'],
                'event_time': record['event_time'],
                'action': record['action'],
                'reason': record['reason'],
                'notes': record['notes'] or '',
                'user_full_name': record['full_name'],
                'user_username': record['username'],
                'pump_number': record['pump_number'],
                'pump_name': record['pump_name'],
                'recorded_time': record['recorded_time']
            })
        
        return jsonify({
            'success': True,
            'records': records_data,
            'pagination': {
                'total_records': result['total_records'],
                'total_pages': result['total_pages'],
                'current_page': page,
                'per_page': per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'خطا در دریافت داده‌ها: {str(e)}'})

@records_bp.route('/api/records/check-delete/<int:record_id>')
def check_delete_permission(record_id):
    """API بررسی امکان حذف رکورد"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'لطفا ابتدا وارد شوید'})
    
    try:
        can_delete, message = can_delete_record(
            record_id, 
            session['user_id'], 
            session['role']
        )
        
        return jsonify({
            'success': True,
            'can_delete': can_delete,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'خطا در بررسی: {str(e)}'})

@records_bp.route('/api/records/delete', methods=['POST'])
def delete_record():
    """API حذف رکورد"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'لطفا ابتدا وارد شوید'})
    
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        deletion_reason = data.get('deletion_reason', '').strip()
        
        if not record_id:
            return jsonify({'success': False, 'error': 'شناسه رکورد الزامی است'})
        
        if not deletion_reason or len(deletion_reason) < 10:
            return jsonify({'success': False, 'error': 'دلیل حذف باید حداقل ۱۰ کاراکتر باشد'})
        
        # بررسی مجدد امکان حذف
        can_delete, message = can_delete_record(
            record_id, 
            session['user_id'], 
            session['role']
        )
        
        if not can_delete:
            return jsonify({'success': False, 'error': message})
        
        # اجرای حذف
        success, result_message = delete_pump_record(
            record_id, 
            deletion_reason, 
            session['user_id']
        )
        
        if success:
            return jsonify({
                'success': True, 
                'message': result_message
            })
        else:
            return jsonify({
                'success': False, 
                'error': result_message
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'خطا در حذف رکورد: {str(e)}'})

@records_bp.route('/admin/deletion-logs')
def view_deletion_logs():
    """صفحه مشاهده لاگ‌های حذف (فقط ادمین)"""
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز', 'error')
        return redirect('/')
    
    conn = get_db_connection()
    logs = conn.execute('''
        SELECT dl.*, u.username as deleted_by_username
        FROM deletion_logs dl
        JOIN users u ON dl.deleted_by_user_id = u.id
        ORDER BY dl.deleted_at DESC
        LIMIT 100
    ''').fetchall()
    conn.close()
    
    return render_template('deletion_logs.html', logs=logs)