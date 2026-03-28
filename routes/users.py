"""User management routes"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import db
from models.user import User, Permission
from models.logs import ActivityLog
from security.decorators import superadmin_required, require_permission

users_bp = Blueprint('users', __name__, url_prefix='/app/users')

# ===== HELPER FUNCTIONS =====

def log_action(action, user_id, detail=None):
    """Log user action"""
    activity = ActivityLog(
        user_id=current_user.id,
        action=action,
        target_type='user',
        target_id=user_id,
        detail=detail or {},
        ip_address=request.remote_addr
    )
    db.session.add(activity)
    db.session.commit()

# ===== USERS LIST =====

@users_bp.route('/', methods=['GET'])
@login_required
@require_permission('users', 'read')
@superadmin_required
def index():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    paginated = User.query.order_by(User.created_at.desc()).paginate(
        page=page,
        per_page=per_page
    )

    return render_template('app/users/index.html',
        users=paginated.items,
        total=paginated.total,
        pages=paginated.pages,
        current_page=page,
        per_page=per_page,
        now=datetime.utcnow
    )

# ===== CREATE USER =====

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('users.create', 'write')
@superadmin_required
def create():
    """Create new user"""
    if request.method == 'GET':
        return render_template('app/users/create.html', roles=['superadmin', 'admin', 'operator'])

    # POST: Create user
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'operator').strip()

        # Validate required fields
        if not username or not email or not password:
            flash('Veuillez remplir tous les champs requis', 'danger')
            return redirect(url_for('users.create'))

        # Validate password length
        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères', 'danger')
            return redirect(url_for('users.create'))

        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Cet utilisateur existe déjà', 'danger')
            return redirect(url_for('users.create'))

        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('users.create'))

        # Validate role
        if role not in ['superadmin', 'admin', 'operator']:
            flash('Rôle invalide', 'danger')
            return redirect(url_for('users.create'))

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            is_active=True,
            created_by=current_user.id
        )
        db.session.add(user)
        db.session.commit()

        log_action('user_create', user.id, {
            'username': username,
            'email': email,
            'role': role
        })

        flash(f'✅ Utilisateur créé: {username}', 'success')
        return redirect(url_for('users.edit', user_id=user.id))

    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('users.create'))

# ===== EDIT USER =====

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('users.edit', 'write')
@superadmin_required
def edit(user_id):
    """Edit user"""
    user = User.query.get(user_id)
    if not user:
        flash('Utilisateur non trouvé', 'danger')
        return redirect(url_for('users.index'))

    if request.method == 'GET':
        return render_template('app/users/edit.html',
            user=user,
            roles=['superadmin', 'admin', 'operator']
        )

    # POST: Update user
    try:
        email = request.form.get('email', '').strip()
        role = request.form.get('role', user.role).strip()
        is_active = request.form.get('is_active') == 'on'

        # Validate email
        if not email:
            flash('L\'email est requis', 'danger')
            return redirect(url_for('users.edit', user_id=user_id))

        # Check if email changed and is unique
        if email != user.email:
            if User.query.filter_by(email=email).first():
                flash('Cet email est déjà utilisé', 'danger')
                return redirect(url_for('users.edit', user_id=user_id))

        # Validate role
        if role not in ['superadmin', 'admin', 'operator']:
            flash('Rôle invalide', 'danger')
            return redirect(url_for('users.edit', user_id=user_id))

        # Update user
        user.email = email
        user.role = role
        user.is_active = is_active

        db.session.commit()

        log_action('user_edit', user_id, {
            'email': email,
            'role': role,
            'is_active': is_active
        })

        flash('✅ Utilisateur mis à jour', 'success')
        return redirect(url_for('users.edit', user_id=user_id))

    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('users.edit', user_id=user_id))

# ===== CHANGE PASSWORD =====

@users_bp.route('/<int:user_id>/password', methods=['POST'])
@login_required
@require_permission('users.edit', 'write')
@superadmin_required
def change_password(user_id):
    """Change user password"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404

        password = request.form.get('password', '').strip()
        if not password or len(password) < 8:
            return jsonify({'success': False, 'message': 'Le mot de passe doit contenir au moins 8 caractères'}), 400

        user.password_hash = generate_password_hash(password)
        db.session.commit()

        log_action('user_password_change', user_id, {'by_admin': True})

        return jsonify({
            'success': True,
            'message': f'Mot de passe changé pour {user.username}'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== DELETE USER =====

@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@require_permission('users.delete', 'write')
@superadmin_required
def delete(user_id):
    """Delete user (soft delete by deactivating)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404

        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Vous ne pouvez pas supprimer votre propre compte'}), 400

        # Soft delete
        user.is_active = False
        db.session.commit()

        log_action('user_delete', user_id, {'username': user.username})

        return jsonify({
            'success': True,
            'message': f'Utilisateur désactivé: {user.username}'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== PERMISSIONS =====

@users_bp.route('/<int:user_id>/permissions', methods=['GET', 'POST'])
@login_required
@require_permission('users.permissions', 'write')
@superadmin_required
def permissions(user_id):
    """Manage user permissions"""
    user = User.query.get(user_id)
    if not user:
        flash('Utilisateur non trouvé', 'danger')
        return redirect(url_for('users.index'))

    if request.method == 'GET':
        # Get all available permissions
        all_perms = Permission.query.filter_by(user_id=user_id).all()

        # Standard permission resources
        resources = [
            ('lines', ['read', 'write']),
            ('lines.testers', ['read', 'write']),
            ('lines.subscribers', ['read', 'write']),
            ('lines.create', ['write']),
            ('lines.extend', ['write']),
            ('lines.refund', ['write']),
            ('stats', ['read']),
            ('telegram.config', ['write']),
            ('telegram.templates', ['read', 'write']),
            ('telegram.conversations', ['read', 'write']),
            ('users', ['read']),
            ('users.create', ['write']),
            ('users.edit', ['write']),
            ('users.delete', ['write']),
            ('users.permissions', ['write']),
            ('seo', ['read', 'write']),
            ('settings', ['read', 'write']),
        ]

        return render_template('app/users/permissions.html',
            user=user,
            resources=resources,
            current_permissions=all_perms
        )

    # POST: Update permissions
    try:
        # Clear existing permissions
        Permission.query.filter_by(user_id=user_id).delete()

        # Add new permissions
        for key, value in request.form.items():
            if key.startswith('perm_'):
                parts = key.replace('perm_', '').split('_')
                resource = '_'.join(parts[:-1])
                action = parts[-1]

                perm = Permission(
                    user_id=user_id,
                    resource=resource,
                    can_read=(action == 'read'),
                    can_write=(action == 'write')
                )
                db.session.add(perm)

        db.session.commit()

        log_action('user_permissions_update', user_id, {'username': user.username})

        flash('✅ Permissions mises à jour', 'success')
        return redirect(url_for('users.permissions', user_id=user_id))

    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('users.permissions', user_id=user_id))

# ===== ACTIVITY LOG =====

@users_bp.route('/<int:user_id>/activity', methods=['GET'])
@login_required
@require_permission('users', 'read')
@superadmin_required
def activity(user_id):
    """View user activity log"""
    user = User.query.get(user_id)
    if not user:
        flash('Utilisateur non trouvé', 'danger')
        return redirect(url_for('users.index'))

    page = request.args.get('page', 1, type=int)
    per_page = 50

    paginated = ActivityLog.query.filter_by(user_id=user_id).order_by(
        ActivityLog.created_at.desc()
    ).paginate(page=page, per_page=per_page)

    return render_template('app/users/activity.html',
        user=user,
        activities=paginated.items,
        total=paginated.total,
        pages=paginated.pages,
        current_page=page
    )
