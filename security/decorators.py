"""Custom decorators for permission checking"""
from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def require_permission(resource, action='read'):
    """Decorator to check if user has permission to resource"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            if not current_user.has_permission(resource, action):
                flash('Vous n\'avez pas la permission d\'accéder à cette ressource.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def superadmin_required(f):
    """Decorator to require superadmin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if current_user.role != 'superadmin':
            flash('Vous devez être superadmin pour accéder à cette page.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function
