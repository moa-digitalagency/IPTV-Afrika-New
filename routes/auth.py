"""Authentication routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from config.database import db
from models.user import User
from models.security_audit import SecurityAudit
from security.validators import Validator
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route with rate limiting and security logging"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        ip_address = request.remote_addr or '0.0.0.0'
        user_agent = request.headers.get('User-Agent', '')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Check for excessive failed login attempts
        failed_count = SecurityAudit.count_failed_logins(ip_address, minutes=5)
        if failed_count >= 5:
            flash('⚠️ Trop de tentatives échouées. Compte temporairement verrouillé (5 min).', 'danger')
            SecurityAudit.log_event(
                event_type='rate_limit_triggered',
                ip_address=ip_address,
                severity='warning',
                username=username,
                endpoint='/auth/login',
                message=f'Login rate limit exceeded: {failed_count} attempts in 5 minutes',
                http_method='POST',
                user_agent=user_agent
            )
            return render_template('auth/login.html'), 429

        if not username or not password:
            flash('Veuillez entrer le nom d\'utilisateur et le mot de passe.', 'danger')
            return render_template('auth/login.html')

        # Validate input format
        if not Validator.validate_username(username) or not Validator.validate_password(password)[0]:
            flash('Nom d\'utilisateur ou mot de passe invalide.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            # Successful login
            login_user(user, remember=request.form.get('remember', False))
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Log successful login
            SecurityAudit.log_event(
                event_type='successful_login',
                ip_address=ip_address,
                severity='info',
                user_id=user.id,
                username=user.username,
                endpoint='/auth/login',
                message=f'User {user.username} logged in successfully',
                http_method='POST',
                user_agent=user_agent
            )

            return redirect(url_for('dashboard.index'))

        # Failed login attempt
        SecurityAudit.log_event(
            event_type='failed_login',
            ip_address=ip_address,
            severity='warning',
            username=username,
            endpoint='/auth/login',
            message=f'Failed login attempt for user: {username}',
            http_method='POST',
            user_agent=user_agent,
            detail={'reason': 'invalid_credentials'}
        )

        flash('Nom d\'utilisateur ou mot de passe invalide.', 'danger')
        return render_template('auth/login.html')

    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout route"""
    logout_user()
    flash('Vous avez été déconnecté.', 'success')
    return redirect(url_for('index'))
