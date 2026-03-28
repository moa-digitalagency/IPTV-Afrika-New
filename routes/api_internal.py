"""Internal API endpoints for admin dashboard (AJAX)"""
from flask import Blueprint, jsonify, request
from flask_login import login_required
from config.database import db
from services.cache_service import CacheService
from services.stats_service import StatsService
from services.golden_api import GoldenAPIService, GoldenAPIException
from models.logs import ActivityLog
from security.decorators import require_permission

api_bp = Blueprint('api', __name__, url_prefix='/app/api')

@api_bp.route('/cache/status', methods=['GET'])
@login_required
@require_permission('cache', 'read')
def get_cache_status():
    """Get cache synchronization status"""
    try:
        status = CacheService.get_cache_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cache/refresh', methods=['POST'])
@login_required
@require_permission('cache', 'write')
def refresh_cache():
    """Manually trigger cache synchronization"""
    from flask_login import current_user
    try:
        success, message = CacheService.sync_all()

        # Log this action
        activity = ActivityLog(
            user_id=current_user.id,
            action='cache_refresh',
            target_type='cache',
            detail={'message': message},
            ip_address=request.remote_addr
        )
        db.session.add(activity)
        db.session.commit()

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats/summary', methods=['GET'])
@login_required
@require_permission('stats', 'read')
def get_stats_summary():
    """Get dashboard statistics summary"""
    try:
        stats = StatsService.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats/full', methods=['GET'])
@login_required
@require_permission('stats', 'read')
def get_full_stats():
    """Get complete statistics"""
    try:
        stats = StatsService.get_full_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/test', methods=['GET'])
@login_required
@require_permission('settings', 'write')
def test_api_connection():
    """Test GOLDEN API connection"""
    try:
        success, message = GoldenAPIService.test_connection()

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except GoldenAPIException as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/lines/search', methods=['GET'])
@login_required
@require_permission('lines', 'read')
def search_lines():
    """Search lines with filters"""
    from models.line import LineCache
    from datetime import datetime

    try:
        query = request.args.get('q', '').strip().lower()
        line_type = request.args.get('type', 'all')  # all, active, expired, trial, paid
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        q = LineCache.query

        # Filter by type
        now = datetime.utcnow()
        if line_type == 'active':
            q = q.filter(LineCache.enabled == True, LineCache.exp_date > now)
        elif line_type == 'expired':
            q = q.filter(LineCache.exp_date < now, LineCache.enabled == True)
        elif line_type == 'trial':
            q = q.filter(LineCache.is_trial == True)
        elif line_type == 'paid':
            q = q.filter(LineCache.is_trial == False)

        # Search by username or email
        if query:
            q = q.filter(
                (LineCache.username.ilike(f'%{query}%')) |
                (LineCache.email.ilike(f'%{query}%')) |
                (LineCache.full_name.ilike(f'%{query}%'))
            )

        # Paginate
        paginated = q.paginate(page=page, per_page=per_page)

        results = [{
            'id': line.golden_id,
            'username': line.username,
            'full_name': line.full_name,
            'email': line.email,
            'package': line.package_name,
            'is_trial': line.is_trial,
            'exp_date': line.exp_date.isoformat() if line.exp_date else None,
            'enabled': line.enabled
        } for line in paginated.items]

        return jsonify({
            'results': results,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/testers/active', methods=['GET'])
@login_required
@require_permission('lines', 'read')
def get_active_testers():
    """Get all active testers for modal selection"""
    from models.line import LineCache
    from datetime import datetime
    from utils.date_helpers import format_date_fr

    try:
        now = datetime.utcnow()
        testers = LineCache.query.filter(
            LineCache.is_trial == True,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).order_by(LineCache.exp_date.asc()).all()

        results = [{
            'golden_id': tester.golden_id,
            'username': tester.username,
            'exp_date_formatted': format_date_fr(tester.exp_date) if tester.exp_date else 'N/A',
            'package_name': tester.package_name or 'N/A'
        } for tester in testers]

        return jsonify({'testers': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/packages/list', methods=['GET'])
@login_required
@require_permission('lines', 'read')
def get_packages_list():
    """Get available packages from GOLDEN API for conversion modal"""
    from models.line import PackageCache

    try:
        # First try to get from cache
        packages = PackageCache.query.all()

        if not packages:
            # If cache is empty, fetch from GOLDEN API
            try:
                api_result = GoldenAPIService.get_packages()
                if api_result and 'packages' in api_result:
                    packages_data = api_result['packages']
                else:
                    return jsonify({'packages': [], 'message': 'No packages available'}), 200
            except GoldenAPIException as e:
                return jsonify({'packages': [], 'message': f'API Error: {str(e)}'}), 200

            # Convert API packages to response format
            results = []
            for pkg in (packages_data if isinstance(packages_data, list) else []):
                results.append({
                    'package_id': pkg.get('id'),
                    'name': pkg.get('name'),
                    'duration_days': pkg.get('duration_days') or pkg.get('days'),
                    'duration_months': round((pkg.get('duration_days') or pkg.get('days', 30)) / 30),
                    'is_trial': pkg.get('is_trial', False)
                })
            return jsonify({'packages': results})

        # Convert cache packages to response format
        results = []
        for pkg in packages:
            results.append({
                'package_id': pkg.golden_id,
                'name': pkg.package_name,
                'duration_days': pkg.duration_days or 30,
                'duration_months': round((pkg.duration_days or 30) / 30),
                'is_trial': pkg.is_trial
            })

        return jsonify({'packages': results})

    except Exception as e:
        return jsonify({'error': str(e), 'packages': []}), 200

@api_bp.route('/lines/all', methods=['GET'])
@login_required
@require_permission('lines', 'read')
def get_all_lines():
    """Get all lines data from cache"""
    from models.line import LineCache
    from datetime import datetime
    from utils.date_helpers import format_date_fr, days_remaining

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        filters = request.args.get('filters', 'all')  # all, active, expired, trial, paid, enabled, disabled

        q = LineCache.query

        now = datetime.utcnow()
        if filters == 'active':
            q = q.filter(LineCache.enabled == True, LineCache.exp_date > now)
        elif filters == 'expired':
            q = q.filter(LineCache.exp_date < now)
        elif filters == 'trial':
            q = q.filter(LineCache.is_trial == True)
        elif filters == 'paid':
            q = q.filter(LineCache.is_trial == False)
        elif filters == 'enabled':
            q = q.filter(LineCache.enabled == True)
        elif filters == 'disabled':
            q = q.filter(LineCache.enabled == False)

        paginated = q.order_by(LineCache.exp_date.desc()).paginate(page=page, per_page=per_page)

        results = []
        for line in paginated.items:
            results.append({
                'id': line.golden_id,
                'username': line.username,
                'password': line.password,
                'full_name': line.full_name,
                'email': line.email,
                'phone': line.phone,
                'package_id': line.package_id,
                'package_name': line.package_name,
                'is_trial': line.is_trial,
                'enabled': line.enabled,
                'exp_date': line.exp_date.isoformat() if line.exp_date else None,
                'exp_date_formatted': format_date_fr(line.exp_date) if line.exp_date else 'N/A',
                'days_left': days_remaining(line.exp_date) if line.exp_date else None,
                'max_connections': line.max_connections,
                'dns_link': line.dns_link,
                'note': line.note,
                'cached_at': line.cached_at.isoformat() if line.cached_at else None
            })

        return jsonify({
            'lines': results,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page,
            'per_page': per_page
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
