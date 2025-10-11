from flask import Blueprint, render_template, request, session, redirect, send_file
from database.reports import get_operating_hours_report, get_status_at_time_report, get_full_history_report
from utils.export_utils import export_operating_hours_to_excel, export_status_report_to_excel, export_full_history_to_excel

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
def reports_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('reports.html')

@reports_bp.route('/report/operating-hours')
def operating_hours_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    date_jalali = request.args.get('date')
    month_jalali = request.args.get('month')
    report_type = request.args.get('report_type', 'daily')
    
    results = get_operating_hours_report(date_jalali, month_jalali, report_type)
    
    return render_template('operating_hours_report.html', 
                         results=results,
                         date_jalali=date_jalali,
                         month_jalali=month_jalali,
                         report_type=report_type)

@reports_bp.route('/report/operating-hours/export')
def export_operating_hours():
    if 'user_id' not in session:
        return redirect('/login')
    
    date_jalali = request.args.get('date')
    month_jalali = request.args.get('month')
    report_type = request.args.get('report_type', 'daily')
    
    return export_operating_hours_to_excel(date_jalali, month_jalali, report_type)

@reports_bp.route('/report/status-at-time')
def status_at_time_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    date_jalali = request.args.get('date')
    time = request.args.get('time')
    display_type = request.args.get('display_type', 'off')
    
    results = get_status_at_time_report(date_jalali, time, display_type)
    
    return render_template('status_at_time_report.html', 
                         results=results, 
                         date_jalali=date_jalali, 
                         time=time, 
                         display_type=display_type)

@reports_bp.route('/report/status-at-time/export')
def export_status_at_time():
    if 'user_id' not in session:
        return redirect('/login')
    
    date_jalali = request.args.get('date')
    time = request.args.get('time')
    display_type = request.args.get('display_type', 'off')
    
    return export_status_report_to_excel(date_jalali, time, display_type)

@reports_bp.route('/report/full-history')
def full_history_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    from_date_jalali = request.args.get('from_date')
    to_date_jalali = request.args.get('to_date')
    pump_id = request.args.get('pump_id', 'all')
    
    results = get_full_history_report(from_date_jalali, to_date_jalali, pump_id)
    
    return render_template('full_history_report.html',
                         results=results,
                         from_date_jalali=from_date_jalali,
                         to_date_jalali=to_date_jalali,
                         pump_id=pump_id)

@reports_bp.route('/report/full-history/export')
def export_full_history():
    if 'user_id' not in session:
        return redirect('/login')
    
    from_date_jalali = request.args.get('from_date')
    to_date_jalali = request.args.get('to_date')
    pump_id = request.args.get('pump_id', 'all')
    
    return export_full_history_to_excel(from_date_jalali, to_date_jalali, pump_id)