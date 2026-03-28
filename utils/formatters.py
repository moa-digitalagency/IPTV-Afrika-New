"""Data formatting utilities"""

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return '0.00 €'
    return f"{amount:.2f} €"

def mask_password(password, show_chars=3):
    """Mask password for display"""
    if not password:
        return '****'
    if len(password) <= show_chars:
        return '*' * len(password)
    return password[:show_chars] + '*' * (len(password) - show_chars)

def format_username(username):
    """Format username for display"""
    if not username:
        return 'N/A'
    return username

def format_role(role):
    """Format user role for display"""
    roles = {
        'superadmin': 'Super Admin',
        'admin': 'Admin',
        'operator': 'Opérateur'
    }
    return roles.get(role, role)

def format_status(is_active):
    """Format status badge"""
    return 'Actif' if is_active else 'Inactif'
