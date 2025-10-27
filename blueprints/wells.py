# blueprints/wells.py
from flask import Blueprint, render_template, request, session, redirect, flash, jsonify
from database.wells_operations import (
    get_all_wells, get_well_by_id, 
    record_well_event, get_well_maintenance_operations,
    get_well_statistics, search_wells
)
from database.models import get_db_connection
import json
from utils.date_utils import gregorian_to_jalali
from utils.export_utils import export_wells_to_excel

wells_bp = Blueprint('wells', __name__)

@wells_bp.route('/wells')
def wells_management():
    """صفحه اصلی مدیریت چاه‌ها"""
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')
    
    # دریافت لیست چاه‌ها
    wells = get_all_wells()
    
     # محاسبه آمار
    total_wells = len(wells)
    active_wells = len([w for w in wells if w['status'] == 'active'])
    inactive_wells = len([w for w in wells if w['status'] == 'inactive'])
    maintenance_wells = len([w for w in wells if w['status'] == 'maintenance'])

    # تبدیل تاریخ‌ها به شمسی
    wells_with_jalali = []
    for well in wells:
        well_dict = dict(well)
        if well['created_at']:
            jalali_datetime = gregorian_to_jalali(well['created_at'])
            parts = jalali_datetime.split(' ')
            well_dict['created_at_jalali'] = parts[0]
        wells_with_jalali.append(well_dict)
    
    return render_template('wells_management.html', 
                         wells=wells_with_jalali,
                         stats={
                             'total': total_wells,
                             'active': active_wells,
                             'inactive': inactive_wells,
                             'maintenance': maintenance_wells
                         })


@wells_bp.route('/wells/<int:well_id>/edit', methods=['GET', 'POST'])
def edit_well(well_id):
    """ویرایش اطلاعات چاه"""
    # We no longer allow direct editing via a separate edit page.
    # Redirect users to the maintenance page which is the single source of truth for updates.
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')

    flash('ویرایش مستقیم اطلاعات چاه حذف شده است. برای ثبت تغییرات از صفحه مدیریت تعمیرات استفاده کنید.', 'info')
    return redirect(f'/wells/{well_id}/maintenance')

@wells_bp.route('/wells/<int:well_id>/maintenance', methods=['GET', 'POST'])
def well_maintenance(well_id):
    """Manages well maintenance, serving as the single point for updates."""
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')
    
    well = get_well_by_id(well_id)
    if not well:
        flash('چاه مورد نظر یافت نشد', 'error')
        return redirect('/wells')
    
    if request.method == 'POST':
        # Consolidate all form data into a single event dictionary
        event_data = {
            'well_id': well_id,
            'recorded_by_user_id': session['user_id'],
            'operation_type': request.form.get('operation_type'),
            'operation_date': request.form.get('operation_date'),
            'performed_by': request.form.get('performed_by'),
            'notes': request.form.get('notes'),
            'well_updates': {
                'name': request.form.get('name'),
                'location': request.form.get('location'),
                'total_depth': request.form.get('total_depth'),
                'pump_installation_depth': request.form.get('pump_installation_depth'),
                'well_diameter': request.form.get('well_diameter'),
                'current_pump_brand': request.form.get('current_pump_brand'),
                'current_pump_model': request.form.get('current_pump_model'),
                'current_pump_power': request.form.get('current_pump_power'),
                'current_pipe_material': request.form.get('current_pipe_material'),
                'current_pipe_diameter': request.form.get('current_pipe_diameter'),
                'current_pipe_length_m': request.form.get('current_pipe_length_m'),
                'main_cable_specs': request.form.get('main_cable_specs'),
                'well_cable_specs': request.form.get('well_cable_specs'),
                'current_panel_specs': request.form.get('current_panel_specs'),
                'status': request.form.get('status'),
                'notes': request.form.get('notes')
            }
        }
        
        # Use the new unified function to record the event
        result = record_well_event(event_data)
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(f'/wells/{well_id}/maintenance')
        else:
            flash(result.get('error', 'یک خطای ناشناخته رخ داد'), 'error')
    
    # Fetch history using the updated operations function
    maintenance_operations = get_well_maintenance_operations(well_id)
    
    # Convert dates to Jalali for display
    maintenance_with_jalali = []
    for operation in maintenance_operations:
        op_dict = dict(operation)
        # Use 'operation_date' from the history record
        if op_dict.get('operation_date'):
            try:
                # Ensure it's treated as a date string
                date_str = str(op_dict['operation_date']).split(' ')[0]
                jalali_date = gregorian_to_jalali(date_str + ' 00:00:00')
                op_dict['operation_date_jalali'] = jalali_date.split(' ')[0]
            except Exception:
                op_dict['operation_date_jalali'] = op_dict['operation_date']
        maintenance_with_jalali.append(op_dict)
    
    return render_template('well_maintenance.html', 
                         well=dict(well),
                         maintenance_operations=maintenance_with_jalali)

@wells_bp.route('/api/wells/search')
def api_search_wells():
    """API جستجوی چاه‌ها"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'لطفا ابتدا وارد شوید'})
    
    search_term = request.args.get('q', '')
    if not search_term or len(search_term) < 2:
        return jsonify({'success': False, 'error': 'حداقل ۲ کاراکتر برای جستجو نیاز است'})
    
    wells = search_wells(search_term)
    
    # تبدیل به فرمت مناسب
    results = []
    for well in wells:
        results.append({
            'id': well['id'],
            'well_number': well['well_number'],
            'name': well['name'],
            'location': well['location'],
            'pump_status': well['pump_status']
        })
    
    return jsonify({'success': True, 'results': results})

# ثبت بلوپرینت در app.py
def register_wells_blueprint(app):
    app.register_blueprint(wells_bp)


@wells_bp.route('/wells/export')
def wells_export():
    """Export wells list to Excel file."""
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')

    # Delegate to export utility which returns a Flask response
    return export_wells_to_excel()


# API: get a single wells_history record by id (used by the maintenance details modal)
@wells_bp.route('/api/wells/history/<int:history_id>')
def api_get_wells_history(history_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'لطفا ابتدا وارد شوید'})

    # import here to avoid circular imports
    from database.wells_operations import get_history_by_id

    record = get_history_by_id(history_id)
    if not record:
        return jsonify({'success': False, 'error': 'رکورد مورد نظر یافت نشد'})

    # changed_fields is stored as JSON list, changed_values as JSON mapping
    try:
        changed_fields = json.loads(record.get('changed_fields') or '[]')
    except Exception:
        changed_fields = []
    try:
        changed_values = json.loads(record.get('changed_values') or '{}')
    except Exception:
        changed_values = {}

    # human readable labels for fields
    field_labels = {
        'name': 'نام چاه',
        'location': 'موقعیت',
        'total_depth': 'عمق کل',
        'pump_installation_depth': 'عمق نصب',
        'well_diameter': 'قطر چاه',
        'current_pump_brand': 'برند پمپ',
        'current_pump_model': 'مدل پمپ',
        'current_pump_power': 'قدرت پمپ',
        'current_pipe_material': 'جنس لوله',
        'current_pipe_diameter': 'قطر لوله',
        'current_pipe_length_m': 'متراژ لوله',
        'main_cable_specs': 'کابل اصلی',
        'well_cable_specs': 'کابل چاه',
        'current_panel_specs': 'مشخصات تابلو',
        'status': 'وضعیت',
        'notes': 'یادداشت'
    }

    # build human readable changes
    changes_human = []
    for f in changed_fields:
        label = field_labels.get(f, f)
        val = changed_values.get(f)
        if val and isinstance(val, dict) and ('old' in val or 'new' in val):
            old = '' if val.get('old') is None else val.get('old')
            new = '' if val.get('new') is None else val.get('new')
            changes_human.append(f"{label} از {old} به {new} تغییر کرد")
        else:
            changes_human.append(label)

    payload = {
        'success': True,
        'record': {
            'id': record.get('id'),
            'operation_date': record.get('operation_date'),
            'operation_type': record.get('operation_type'),
            'performed_by': record.get('performed_by'),
            'reason': record.get('reason'),
            'changes': changes_human
        }
    }

    return jsonify(payload)