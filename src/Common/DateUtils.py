"""
Date utilities module
=====================

Date and time handling functions for financial calculations.
"""

from datetime import datetime, timedelta
from typing import Optional

# Season report release schedule
SEASON_RP_TIME_MONTH = [5, 8, 11, 3]
SEASON_RP_TIME_DAY = [15, 31, 14, 31]


def change_date_month(date: datetime, change_month: int) -> datetime:
    """
    Change date by specified number of months, adjusting for valid days and weekends.
    
    Args:
        date: Original date
        change_month: Number of months to add (positive) or subtract (negative)
        
    Returns:
        Adjusted datetime object
    """
    temp_month = date.month + change_month
    
    if temp_month >= 13:
        year = temp_month // 12
        month = temp_month % 12
        if month == 0:
            month = 12
        new_date = datetime(
            year=date.year + year,
            month=month,
            day=check_month_date(month, date.day)
        )
    elif temp_month <= 0:
        temp_month = abs(temp_month)
        year = temp_month // 12
        month = temp_month % 12
        year = -1 - year
        if month == 0:
            month = 12
        else:
            month = 12 - month
        new_date = datetime(
            year=date.year + year,
            month=month,
            day=check_month_date(month, date.day)
        )
    else:
        new_date = datetime(
            year=date.year,
            month=temp_month,
            day=check_month_date(temp_month, date.day)
        )
    
    # Adjust for weekend
    while new_date.isoweekday() in [6, 7]:
        if new_date.day < 15:
            new_date = back_work_days(new_date, -1)
        else:
            new_date = back_work_days(new_date, 1)
    
    return new_date


def check_month_date(month: int, day: int) -> int:
    """
    Validate and adjust day for given month (e.g., 31 Feb becomes 28).
    
    Args:
        month: Month number (1-12)
        day: Day number
        
    Returns:
        Valid day number for the month
    """
    result_day = day
    if day > 28:
        if month == 2:
            result_day = 28
        elif month in [4, 6, 9, 11] and day == 31:
            result_day = 30
    return result_day


def back_work_days(date, days: int) -> datetime:
    """
    Calculate date by moving specified number of working days (skipping weekends).
    
    Args:
        date: Starting date (datetime or string in "%Y-%m-%d" format)
        days: Number of working days to move back (positive) or forward (negative)
        
    Returns:
        Calculated datetime object
    """
    if isinstance(date, str):
        input_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        input_date = date
    
    input_days = abs(days)
    
    while input_days > 0:
        if days < 0:
            input_date += timedelta(days=1)
        else:
            input_date -= timedelta(days=1)
        
        if input_date.isoweekday() in [6, 7]:
            continue
        
        input_days -= 1
    
    return input_date


def qt_date_to_datetime(date) -> datetime:
    """Convert Qt QDate object to Python datetime."""
    return datetime(date.year(), date.month(), date.day())


def datetime_to_string(date: datetime) -> str:
    """Convert datetime object to "YYYY-MM-DD" string format."""
    return f"{date.year}-{date.month}-{date.day}"


def check_fs_season(date: datetime, base_today: Optional[datetime] = None) -> bool:
    """
    Check if financial statement for given season date is available.
    
    Args:
        date: Season date to check
        base_today: Reference date (defaults to current datetime)
        
    Returns:
        True if report should be available
    """
    if base_today is None:
        base_today = datetime.now()
    
    season = ((date.month - 1) // 3) + 1
    year = date.year
    
    if season == 4:
        return base_today >= datetime(
            year + 1,
            SEASON_RP_TIME_MONTH[season - 1],
            SEASON_RP_TIME_DAY[season - 1]
        )
    else:
        return base_today >= datetime(
            year,
            SEASON_RP_TIME_MONTH[season - 1],
            SEASON_RP_TIME_DAY[season - 1]
        )


def have_month_rp(date: datetime, base_today: Optional[datetime] = None) -> bool:
    """
    Check if monthly revenue report is available for given date.
    
    Args:
        date: Month date to check
        base_today: Reference date (defaults to current datetime)
        
    Returns:
        True if report should be available
    """
    if base_today is None:
        base_today = datetime.now()
    
    # Current month data not yet available
    if date.month == base_today.month and date.year == base_today.year:
        return False
    
    # Previous month data available after 15th
    previous_month = change_date_month(base_today, -1)
    if (date.year == base_today.year and 
        date.month == previous_month.month and 
        base_today.day < 15):
        return False
    
    return True


def have_day_rp(date: datetime, base_today: Optional[datetime] = None) -> bool:
    """
    Check if daily report data is available for given date.
    
    Args:
        date: Date to check
        base_today: Reference date (defaults to current datetime)
        
    Returns:
        True if data should be available
    """
    if base_today is None:
        base_today = datetime.now()
    
    return not (
        date.year >= base_today.year and
        date.month >= base_today.month and
        date.day >= base_today.day
    )


def get_latest_season_report_date(now_day: datetime, base_today: Optional[datetime] = None) -> datetime:
    """Find latest available season report date starting from given date."""
    check_date = now_day
    while not check_fs_season(check_date, base_today):
        check_date = change_date_month(check_date, -3)
    return check_date


def get_latest_monthly_report_date(now_day: datetime, base_today: Optional[datetime] = None) -> datetime:
    """Find latest available monthly report date starting from given date."""
    check_date = now_day.replace(day=1)
    while not have_month_rp(check_date, base_today):
        check_date = change_date_month(check_date, -1)
    return check_date


def get_latest_daily_report_date(now_day: datetime, base_today: Optional[datetime] = None) -> datetime:
    """Find latest available daily report date starting from given date."""
    check_date = now_day
    while not have_day_rp(check_date, base_today):
        check_date = back_work_days(check_date, 1)
    return check_date