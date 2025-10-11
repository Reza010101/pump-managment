import jdatetime
from datetime import datetime

def gregorian_to_jalali(gregorian_date):
    """
    Convert Gregorian date to Jalali
    Input: Gregorian date string (YYYY-MM-DD HH:MM:SS)
    Output: Jalali date string (YYYY/MM/DD HH:MM:SS)
    """
    try:
        if isinstance(gregorian_date, str):
            if ' ' in gregorian_date:
                date_part, time_part = gregorian_date.split(' ')
                year, month, day = map(int, date_part.split('-'))
                hour, minute, second = map(int, time_part.split(':'))
                greg_date = datetime(year, month, day, hour, minute, second)
            else:
                year, month, day = map(int, gregorian_date.split('-'))
                greg_date = datetime(year, month, day)
        else:
            greg_date = gregorian_date
        
        jalali_date = jdatetime.datetime.fromgregorian(datetime=greg_date)
        return jalali_date.strftime('%Y/%m/%d %H:%M:%S')
    
    except Exception as e:
        print(f"Error converting to Jalali: {e}")
        return gregorian_date

def jalali_to_gregorian(jalali_date_str):
    """
    Convert Jalali date to Gregorian
    Input: Jalali date string (YYYY/MM/DD HH:MM:SS)
    Output: Gregorian date string (YYYY-MM-DD HH:MM:SS)
    """
    try:
        if ' ' in jalali_date_str:
            date_part, time_part = jalali_date_str.split(' ')
            year, month, day = map(int, date_part.split('/'))
            hour, minute, second = map(int, time_part.split(':'))
            jalali_date = jdatetime.datetime(year, month, day, hour, minute, second)
        else:
            year, month, day = map(int, jalali_date_str.split('/'))
            jalali_date = jdatetime.datetime(year, month, day)
        
        greg_date = jalali_date.togregorian()
        return greg_date.strftime('%Y-%m-%d %H:%M:%S')
    
    except Exception as e:
        print(f"Error converting to Gregorian: {e}")
        return jalali_date_str

def get_current_jalali():
    """Get current Jalali date and time"""
    now = jdatetime.datetime.now()
    return now.strftime('%Y/%m/%d %H:%M:%S')

def get_current_gregorian():
    """Get current Gregorian date and time"""
    now = datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S')