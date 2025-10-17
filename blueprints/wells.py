# blueprints/wells.py
from flask import Blueprint, render_template, request, session, redirect, flash, jsonify
from database.wells_operations import (
    get_all_wells, get_well_by_id, update_well, 
    create_maintenance_operation, get_well_maintenance_operations,
    get_well_statistics, search_wells
)
from database.models import get_db_connection
from utils.date_utils import gregorian_to_jalali

wells_bp = Blueprint('wells', __name__)

@wells_bp.route('/wells')
def wells_management():
    """صفحه اصلی مدیریت چاه‌ها"""
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')
    
    # دریافت لیست چاه‌ها
    wells = get_all_wells()
    
    # تبدیل تاریخ‌ها به شمسی
    wells_with_jalali = []
    for well in wells:
        well_dict = dict(well)
        if well['created_at']:
            jalali_datetime = gregorian_to_jalali(well['created_at'])
            parts = jalali_datetime.split(' ')
            well_dict['created_at_jalali'] = parts[0]
        wells_with_jalali.append(well_dict)
    
    return render_template('wells_management.html', wells=wells_with_jalali)

@wells_bp.route('/wells/<int:well_id>')
def well_details(well_id):
    """صفحه جزئیات چاه"""
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')
    
    # دریافت اطلاعات چاه
    well = get_well_by_id(well_id)
    if not well:
        flash('چاه مورد نظر یافت نشد', 'error')
        return redirect('/wells')
    
    # دریافت تاریخچه تعمیرات
    maintenance_operations = get_well_maintenance_operations(well_id)
    
    # دریافت آمار چاه
    statistics = get_well_statistics(well_id)
    
    # تبدیل تاریخ‌ها به شمسی
    well_data = dict(well)
    if well['created_at']:
        jalali_datetime = gregorian_to_jalali(well['created_at'])
        parts = jalali_datetime.split(' ')
        well_data['created_at_jalali'] = parts[0]
    
    if well['updated_at']:
        jalali_datetime = gregorian_to_jalali(well['updated_at'])
        parts = jalali_datetime.split(' ')
        well_data['updated_at_jalali'] = parts[0]
    
    # تبدیل تاریخ‌های تعمیرات
    maintenance_with_jalali = []
    for operation in maintenance_operations:
        op_dict = dict(operation)
        if operation['operation_date']:
            # فرض می‌کنیم operation_date در فرمت Gregorian هست
            try:
                jalali_date = gregorian_to_jalali(operation['operation_date'] + ' 00:00:00')
                op_dict['operation_date_jalali'] = jalali_date.split(' ')[0]
            except:
                op_dict['operation_date_jalali'] = operation['operation_date']
        maintenance_with_jalali.append(op_dict)
    
    return render_template('well_details.html', 
                         well=well_data,
                         maintenance_operations=maintenance_with_jalali,
                         statistics=statistics)

@wells_bp.route('/wells/<int:well_id>/edit', methods=['GET', 'POST'])
def edit_well(well_id):
    """ویرایش اطلاعات چاه"""
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')
    
    well = get_well_by_id(well_id)
    if not well:
        flash('چاه مورد نظر یافت نشد', 'error')
        return redirect('/wells')
    
    if request.method == 'POST':
        # جمع‌آوری داده‌های فرم
        well_data = {
            'name': request.form.get('name'),
            'location': request.form.get('location'),
            'total_depth': request.form.get('total_depth'),
            'pump_installation_depth': request.form.get('pump_installation_depth'),
            'well_diameter': request.form.get('well_diameter'),
            'casing_type': request.form.get('casing_type'),
            'current_pump_brand': request.form.get('current_pump_brand'),
            'current_pump_model': request.form.get('current_pump_model'),
            'current_pump_power': request.form.get('current_pump_power'),
            'current_pump_phase': request.form.get('current_pump_phase'),
            'current_cable_specs': request.form.get('current_cable_specs'),
            'current_pipe_material': request.form.get('current_pipe_material'),
            'current_pipe_specs': request.form.get('current_pipe_specs'),
            'current_panel_specs': request.form.get('current_panel_specs'),
            'well_installation_date': request.form.get('well_installation_date'),
            'current_equipment_installation_date': request.form.get('current_equipment_installation_date'),
            'status': request.form.get('status', 'active'),
            'notes': request.form.get('notes')
        }
        
        # بروزرسانی چاه
        result = update_well(well_id, well_data)
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(f'/wells/{well_id}')
        else:
            flash(result['error'], 'error')
    
    return render_template('edit_well.html', well=dict(well))

@wells_bp.route('/wells/<int:well_id>/maintenance', methods=['GET', 'POST'])
def well_maintenance(well_id):
    """مدیریت تعمیرات چاه"""
    if 'user_id' not in session:
        flash('لطفا ابتدا وارد شوید', 'error')
        return redirect('/login')
    
    well = get_well_by_id(well_id)
    if not well:
        flash('چاه مورد نظر یافت نشد', 'error')
        return redirect('/wells')
    
    if request.method == 'POST':
        # جمع‌آوری داده‌های فرم تعمیرات
        operation_data = {
            'well_id': well_id,
            'recorded_by_user_id': session['user_id'],
            'operation_type': request.form.get('operation_type'),
            'operation_date': request.form.get('operation_date'),
            'operation_time': request.form.get('operation_time'),
            'description': request.form.get('description'),
            'parts_used': request.form.get('parts_used'),
            'duration_minutes': request.form.get('duration_minutes'),
            'performed_by': request.form.get('performed_by'),
            'status': request.form.get('status', 'completed'),
            'notes': request.form.get('notes')
        }
        
        # ثبت عملیات تعمیرات
        result = create_maintenance_operation(operation_data)
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(f'/wells/{well_id}')
        else:
            flash(result['error'], 'error')
    
    # دریافت تاریخچه تعمیرات
    maintenance_operations = get_well_maintenance_operations(well_id)
    
    # تبدیل تاریخ‌ها به شمسی
    maintenance_with_jalali = []
    for operation in maintenance_operations:
        op_dict = dict(operation)
        if operation['operation_date']:
            try:
                jalali_date = gregorian_to_jalali(operation['operation_date'] + ' 00:00:00')
                op_dict['operation_date_jalali'] = jalali_date.split(' ')[0]
            except:
                op_dict['operation_date_jalali'] = operation['operation_date']
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