"""Lines management routes"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from config.database import db
from models.line import LineCache
from models.logs import ActivityLog
from services.golden_api import GoldenAPIService, GoldenAPIException
from services.cache_service import CacheService
from security.decorators import require_permission
from utils.date_helpers import days_remaining, format_date_fr

lines_bp = Blueprint('lines', __name__, url_prefix='/app/lines')

# ===== HELPER FUNCTIONS =====

def log_action(action, line_id, detail=None):
    """Log user action"""
    activity = ActivityLog(
        user_id=current_user.id,
        action=action,
        target_type='line',
        target_id=line_id,
        detail=detail or {},
        ip_address=request.remote_addr
    )
    db.session.add(activity)
    db.session.commit()

# ===== TESTERS ACTIVE =====

@lines_bp.route('/testers/active', methods=['GET'])
@login_required
@require_permission('lines.testers', 'read')
def testers_active():
    """List active testers"""
    now = datetime.utcnow()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = LineCache.query.filter(
        LineCache.is_trial == True,
        LineCache.enabled == True,
        LineCache.exp_date > now
    ).order_by(LineCache.exp_date.asc())

    paginated = query.paginate(page=page, per_page=per_page)

    return render_template('app/lines/testers_active.html',
        lines=paginated.items,
        total=paginated.total,
        pages=paginated.pages,
        current_page=page,
        per_page=per_page,
        now=datetime.utcnow
    )

# ===== TESTERS EXPIRED =====

@lines_bp.route('/testers/expired', methods=['GET'])
@login_required
@require_permission('lines.testers', 'read')
def testers_expired():
    """List expired testers"""
    now = datetime.utcnow()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = LineCache.query.filter(
        LineCache.is_trial == True,
        LineCache.exp_date < now,
        LineCache.enabled == True
    ).order_by(LineCache.exp_date.desc())

    paginated = query.paginate(page=page, per_page=per_page)

    return render_template('app/lines/testers_expired.html',
        lines=paginated.items,
        total=paginated.total,
        pages=paginated.pages,
        current_page=page,
        per_page=per_page,
        now=datetime.utcnow
    )

# ===== SUBSCRIBERS ACTIVE =====

@lines_bp.route('/subs/active', methods=['GET'])
@login_required
@require_permission('lines.subscribers', 'read')
def subs_active():
    """List active subscribers"""
    now = datetime.utcnow()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = LineCache.query.filter(
        LineCache.is_trial == False,
        LineCache.enabled == True,
        LineCache.exp_date > now
    ).order_by(LineCache.exp_date.asc())

    paginated = query.paginate(page=page, per_page=per_page)

    return render_template('app/lines/subs_active.html',
        lines=paginated.items,
        total=paginated.total,
        pages=paginated.pages,
        current_page=page,
        per_page=per_page,
        now=datetime.utcnow
    )

# ===== SUBSCRIBERS EXPIRED =====

@lines_bp.route('/subs/expired', methods=['GET'])
@login_required
@require_permission('lines.subscribers', 'read')
def subs_expired():
    """List expired subscribers"""
    now = datetime.utcnow()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = LineCache.query.filter(
        LineCache.is_trial == False,
        LineCache.exp_date < now,
        LineCache.enabled == True
    ).order_by(LineCache.exp_date.desc())

    paginated = query.paginate(page=page, per_page=per_page)

    return render_template('app/lines/subs_expired.html',
        lines=paginated.items,
        total=paginated.total,
        pages=paginated.pages,
        current_page=page,
        per_page=per_page,
        now=datetime.utcnow
    )

# ===== LINE DETAIL =====

@lines_bp.route('/<int:golden_id>', methods=['GET'])
@login_required
@require_permission('lines', 'read')
def line_detail(golden_id):
    """Get line details"""
    line = LineCache.query.filter_by(golden_id=golden_id).first()
    if not line:
        flash('Ligne non trouvée', 'danger')
        return redirect(url_for('lines.testers_active'))

    days_left = days_remaining(line.exp_date) if line.exp_date else None

    return render_template('app/lines/detail.html',
        line=line,
        days_left=days_left,
        now=datetime.utcnow
    )

# ===== CREATE LINE =====

@lines_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('lines.create', 'write')
def create_line():
    """Create new line"""
    if request.method == 'GET':
        # Get packages from cache or GOLDEN API
        from models.line import PackageCache

        packages = []
        try:
            # First try to get from cache
            cached_packages = PackageCache.query.all()

            if cached_packages:
                packages = [(p.golden_id, p.package_name) for p in cached_packages]
            else:
                # If cache is empty, fetch from GOLDEN API
                try:
                    api_result = GoldenAPIService.get_packages()
                    api_packages = api_result.get('packages', [])
                    packages = [(p.get('id'), p.get('name')) for p in api_packages]
                except GoldenAPIException as e:
                    print(f"Error fetching packages from API: {e}")
                    packages = []
        except Exception as e:
            print(f"Error loading packages: {e}")
            packages = []

        return render_template('app/lines/create.html', packages=packages)

    # POST: Create line
    try:
        import random
        import string

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        package_id = request.form.get('package_id', type=int)
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()

        # Auto-generate credentials if not provided
        if not username:
            # Username: 7-12 characters, letters and numbers only
            username = 'USER' + ''.join(random.choices(string.digits, k=4))  # USER + 4 digits = 8 chars

        if not password:
            # Password: Exactly 7 characters, uppercase letters and numbers only
            chars = string.ascii_uppercase + string.digits
            password = ''.join(random.choices(chars, k=7))

        # Validate required fields
        if not package_id:
            flash('Veuillez sélectionner un package', 'danger')
            return redirect(url_for('lines.create_line'))

        # Call GOLDEN API
        result = GoldenAPIService.create_line(username, password, package_id)
        if not result:
            flash('Erreur lors de la création de la ligne', 'danger')
            return redirect(url_for('lines.create_line'))

        line_id = result.get('id')

        # Log action
        log_action('create', line_id, {
            'username': username,
            'package_id': package_id
        })

        # Parse expiration date if provided
        exp_date = None
        exp_date_str = result.get('exp_date')
        if exp_date_str:
            try:
                if 'T' in exp_date_str:
                    exp_date = datetime.fromisoformat(exp_date_str.replace('Z', '+00:00'))
                else:
                    exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
            except (ValueError, TypeError):
                pass

        # Add the new line to cache immediately
        cache_line = LineCache(
            golden_id=line_id,
            username=result.get('username'),
            password=result.get('password'),
            full_name=full_name or None,
            email=email or None,
            package_id=result.get('package_id'),
            package_name=result.get('package_name'),
            is_trial=result.get('is_trial', False),
            exp_date=exp_date,
            enabled=result.get('enabled', True),
            max_connections=result.get('max_connections', 1),
            dns_link=result.get('dns_link'),
            created_at=datetime.utcnow(),
            cached_at=datetime.utcnow()
        )
        db.session.add(cache_line)
        db.session.commit()

        flash(f'Ligne créée avec succès: {username}', 'success')
        return redirect(url_for('lines.line_detail', golden_id=line_id))

    except GoldenAPIException as e:
        flash(f'Erreur API: {str(e)}', 'danger')
        return redirect(url_for('lines.create_line'))
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('lines.create_line'))

# ===== EXTEND LINE =====

@lines_bp.route('/<int:golden_id>/extend', methods=['POST'])
@login_required
@require_permission('lines.extend', 'write')
def extend_line(golden_id):
    """Extend line expiration"""
    try:
        days = request.form.get('days', type=int)
        if not days or days <= 0:
            return jsonify({'success': False, 'message': 'Nombre de jours invalide'}), 400

        # Call GOLDEN API
        result = GoldenAPIService.extend_line(golden_id, days)
        if not result:
            return jsonify({'success': False, 'message': 'Erreur lors de la prolongation'}), 400

        # Log action
        log_action('extend', golden_id, {'days': days})

        # Invalidate cache
        CacheService.invalidate_line(golden_id)

        return jsonify({
            'success': True,
            'message': f'Ligne prolongée de {days} jours',
            'new_exp_date': result.get('exp_date')
        })

    except GoldenAPIException as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== REFUND LINE =====

@lines_bp.route('/<int:golden_id>/refund', methods=['POST'])
@login_required
@require_permission('lines.refund', 'write')
def refund_line(golden_id):
    """Refund and close line"""
    try:
        line = LineCache.query.filter_by(golden_id=golden_id).first()
        if not line:
            return jsonify({'success': False, 'message': 'Ligne non trouvée'}), 404

        # Call GOLDEN API
        result = GoldenAPIService.refund_line(golden_id)
        if not result:
            return jsonify({'success': False, 'message': 'Erreur lors du remboursement'}), 400

        # Update local cache
        line.enabled = False
        db.session.commit()

        # Log action
        log_action('refund', golden_id, {'username': line.username})

        return jsonify({
            'success': True,
            'message': f'Ligne remboursée: {line.username}'
        })

    except GoldenAPIException as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== CONVERT TESTER TO SUBSCRIBER =====

@lines_bp.route('/<int:golden_id>/convert', methods=['POST'])
@login_required
@require_permission('lines.extend', 'write')
def convert_tester(golden_id):
    """Convert trial line to paid subscriber and extend"""
    try:
        line = LineCache.query.filter_by(golden_id=golden_id).first()
        if not line:
            return jsonify({'success': False, 'message': 'Ligne non trouvée'}), 404

        if not line.is_trial:
            return jsonify({'success': False, 'message': 'Cette ligne n\'est pas un testeur'}), 400

        # Get days from request
        days = request.form.get('days') or request.json.get('days', 30) if request.json else 30
        days = int(days) if days else 30

        if days <= 0:
            return jsonify({'success': False, 'message': 'Nombre de jours invalide'}), 400

        # Call GOLDEN API to extend
        result = GoldenAPIService.extend_line(golden_id, days)
        if not result:
            return jsonify({'success': False, 'message': 'Erreur lors de la prolongation'}), 400

        # Update local cache: convert to paid subscriber
        line.is_trial = False
        db.session.commit()

        # Log action
        log_action('convert_tester', golden_id, {
            'username': line.username,
            'days_extended': days,
            'new_exp_date': result.get('exp_date')
        })

        # Invalidate cache
        CacheService.invalidate_line(golden_id)

        return jsonify({
            'success': True,
            'message': f'Testeur {line.username} converti en abonné et prolongé de {days} jours',
            'new_exp_date': result.get('exp_date')
        })

    except GoldenAPIException as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== TOGGLE LINE =====

@lines_bp.route('/<int:golden_id>/toggle', methods=['POST'])
@login_required
@require_permission('lines.toggle', 'write')
def toggle_line(golden_id):
    """Enable/disable line"""
    try:
        line = LineCache.query.filter_by(golden_id=golden_id).first()
        if not line:
            return jsonify({'success': False, 'message': 'Ligne non trouvée'}), 404

        line.enabled = not line.enabled
        db.session.commit()

        log_action('toggle', golden_id, {'enabled': line.enabled})

        status = 'activée' if line.enabled else 'désactivée'
        return jsonify({
            'success': True,
            'message': f'Ligne {status}',
            'enabled': line.enabled
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
