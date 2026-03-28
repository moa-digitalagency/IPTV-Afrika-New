"""Date and time helper functions"""
from datetime import datetime, timedelta

def is_expired(exp_date):
    """Check if a date is expired"""
    if not exp_date:
        return False
    return datetime.utcnow() > exp_date

def days_remaining(exp_date):
    """Get number of days remaining until expiration"""
    if not exp_date:
        return None
    delta = exp_date - datetime.utcnow()
    return max(0, delta.days)

def format_date_fr(date_obj):
    """Format date to French format (dd/mm/yyyy)"""
    if not date_obj:
        return 'N/A'
    return date_obj.strftime('%d/%m/%Y')

def format_datetime_fr(date_obj):
    """Format datetime to French format (dd/mm/yyyy HH:mm)"""
    if not date_obj:
        return 'N/A'
    return date_obj.strftime('%d/%m/%Y %H:%M')

def add_days(date_obj, days):
    """Add days to a date"""
    return date_obj + timedelta(days=days)
