import pandas as pd
import io
from flask import send_file
from database.reports import get_operating_hours_report, get_status_at_time_report, get_full_history_report

def export_operating_hours_to_excel(date_jalali, month_jalali, report_type):
    """خروجی اکسل برای گزارش ساعات کارکرد"""
    results = get_operating_hours_report(date_jalali, month_jalali, report_type)
    
    if not results:
        from flask import flash, redirect
        flash('هیچ داده‌ای برای دانلود وجود ندارد', 'warning')
        return redirect('/report/operating-hours')
    
    df = pd.DataFrame(results)
    
    if report_type == 'daily':
        period_title = f"گزارش ساعات کارکرد روزانه - تاریخ: {date_jalali}"
        filename = f'operating_hours_daily_{date_jalali.replace("/", "-")}.xlsx'
    else:
        period_title = f"گزارش ساعات کارکرد ماهانه - ماه: {month_jalali}"
        filename = f'operating_hours_monthly_{month_jalali.replace("/", "-")}.xlsx'
    
    output = create_excel_with_title(df, period_title, 'گزارش ساعات کارکرد')
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def export_status_report_to_excel(date_jalali, time, display_type):
    """خروجی اکسل برای گزارش وضعیت در زمان خاص"""
    results = get_status_at_time_report(date_jalali, time, display_type)
    
    if not results:
        from flask import flash, redirect
        flash('هیچ داده‌ای برای دانلود وجود ندارد', 'warning')
        return redirect('/report/status-at-time')
    
    df = pd.DataFrame(results)
    period_title = f"گزارش وضعیت پمپ‌ها - تاریخ: {date_jalali} - ساعت: {time}"
    filename = f'status_report_{date_jalali}_{time}.xlsx'.replace('/', '-').replace(':', '-')
    
    output = create_excel_with_title(df, period_title, 'گزارش وضعیت')
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def export_full_history_to_excel(from_date_jalali, to_date_jalali, pump_id):
    """خروجی اکسل برای گزارش تاریخچه کامل"""
    results = get_full_history_report(from_date_jalali, to_date_jalali, pump_id)
    
    if not results:
        from flask import flash, redirect
        flash('هیچ داده‌ای برای دانلود وجود ندارد', 'warning')
        return redirect('/report/full-history')
    
    data = []
    for row in results:
        data.append({
            'شماره پمپ': row['pump_number'],
            'نام پمپ': row['name'],
            'وضعیت': row['action_persian'],
            'تاریخ': row['action_date'],
            'ساعت': row['action_time'],
            'علت': row['reason'],
            'توضیحات': row['notes'] or '',
            'کاربر': row['user_name']
        })
    
    df = pd.DataFrame(data)
    period_title = f"تاریخچه تغییرات - از {from_date_jalali} تا {to_date_jalali}"
    filename = f'full_history_{from_date_jalali}_to_{to_date_jalali}.xlsx'.replace('/', '-')
    
    output = create_excel_with_title(df, period_title, 'تاریخچه تغییرات')
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def create_excel_with_title(df, title, sheet_name):
    """ایجاد فایل اکسل با عنوان"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # اضافه کردن عنوان
        worksheet.insert_rows(1)
        worksheet['A1'] = title
        worksheet.merge_cells('A1:H1')
        
        # تنظیم عرض ستون‌ها
        worksheet.column_dimensions['A'].width = 15
        worksheet.column_dimensions['B'].width = 20
        worksheet.column_dimensions['C'].width = 12
        worksheet.column_dimensions['D'].width = 12
        worksheet.column_dimensions['E'].width = 10
        worksheet.column_dimensions['F'].width = 20
        worksheet.column_dimensions['G'].width = 25
        worksheet.column_dimensions['H'].width = 15
    
    return output

def create_sample_excel_file():
    """ایجاد فایل نمونه برای آپلود"""
    sample_data = {
        'Pump_Number': [1, 1, 2, 3],
        'Action': ['ON', 'OFF', 'ON', 'OFF'],
        'Date_Jalali': ['1403/07/10', '1403/07/10', '1403/07/11', '1403/07/11'],
        'Time_Jalali': ['08:00', '12:30', '09:15', '17:45'],
        'Reason': ['برنامه ریزی شده', 'قطع برق', 'تعمیرات', 'پایان شیفت'],
        'Notes': ['', 'قطع ۲ ساعته', 'تعویض قطعه', '']
    }
    
    df = pd.DataFrame(sample_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sample', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='pump_history_sample.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )