"""Statistics routes"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from services.stats_service import StatsService
from security.decorators import require_permission

stats_bp = Blueprint('stats', __name__, url_prefix='/app/stats')

# ===== STATS PAGE =====

@stats_bp.route('/', methods=['GET'])
@login_required
@require_permission('stats', 'read')
def index():
    """Statistics dashboard"""
    try:
        # Get all stats
        dashboard_stats = StatsService.get_dashboard_stats()
        line_stats = StatsService.get_line_stats()
        activity_stats = StatsService.get_activity_stats(days=30)
        cache_stats = StatsService.get_cache_stats()

        return render_template('app/stats/index.html',
            dashboard_stats=dashboard_stats,
            line_stats=line_stats,
            activity_stats=activity_stats,
            cache_stats=cache_stats,
            now=datetime.utcnow
        )
    except Exception as e:
        return render_template('app/stats/index.html',
            dashboard_stats={},
            line_stats={},
            activity_stats={},
            cache_stats={},
            error=str(e),
            now=datetime.utcnow
        )

# ===== AJAX ENDPOINTS =====

@stats_bp.route('/api/summary', methods=['GET'])
@login_required
@require_permission('stats', 'read')
def api_summary():
    """Get summary stats for dashboard"""
    try:
        stats = StatsService.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/api/charts/expiry', methods=['GET'])
@login_required
@require_permission('stats', 'read')
def api_expiry_chart():
    """Get expiry distribution data"""
    try:
        from models.line import LineCache
        from config.database import db

        # Distribution by days remaining
        now = datetime.utcnow()

        # Count by ranges
        expired = db.session.query(db.func.count(LineCache.id)).filter(
            LineCache.exp_date < now,
            LineCache.enabled == True
        ).scalar() or 0

        expiring_week = db.session.query(db.func.count(LineCache.id)).filter(
            LineCache.exp_date >= now,
            LineCache.exp_date < now + timedelta(days=7),
            LineCache.enabled == True
        ).scalar() or 0

        expiring_month = db.session.query(db.func.count(LineCache.id)).filter(
            LineCache.exp_date >= now + timedelta(days=7),
            LineCache.exp_date < now + timedelta(days=30),
            LineCache.enabled == True
        ).scalar() or 0

        active = db.session.query(db.func.count(LineCache.id)).filter(
            LineCache.exp_date >= now + timedelta(days=30),
            LineCache.enabled == True
        ).scalar() or 0

        return jsonify({
            'labels': ['Expiré', 'Expiration < 7j', 'Expiration 7-30j', 'Actif > 30j'],
            'data': [expired, expiring_week, expiring_month, active],
            'colors': ['#E74C3C', '#F39C12', '#D4A574', '#27AE60']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/api/charts/trial-vs-paid', methods=['GET'])
@login_required
@require_permission('stats', 'read')
def api_trial_vs_paid():
    """Get trial vs paid subscription breakdown"""
    try:
        from models.line import LineCache
        from config.database import db

        now = datetime.utcnow()

        trial_active = db.session.query(db.func.count(LineCache.id)).filter(
            LineCache.is_trial == True,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).scalar() or 0

        trial_expired = db.session.query(db.func.count(LineCache.id)).filter(
            LineCache.is_trial == True,
            LineCache.exp_date <= now,
            LineCache.enabled == True
        ).scalar() or 0

        paid_active = db.session.query(db.func.count(LineCache.id)).filter(
            LineCache.is_trial == False,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).scalar() or 0

        paid_expired = db.session.query(db.func.count(LineCache.id)).filter(
            LineCache.is_trial == False,
            LineCache.exp_date <= now,
            LineCache.enabled == True
        ).scalar() or 0

        return jsonify({
            'labels': ['Testeurs Actifs', 'Testeurs Expirés', 'Abonnés Actifs', 'Abonnés Expirés'],
            'data': [trial_active, trial_expired, paid_active, paid_expired],
            'colors': ['#D4A574', '#E74C3C', '#27AE60', '#95A5A6']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/api/charts/activity', methods=['GET'])
@login_required
@require_permission('stats', 'read')
def api_activity_chart():
    """Get activity timeline (last 30 days)"""
    try:
        from models.logs import ActivityLog
        from config.database import db
        from sqlalchemy import func

        # Daily activity count
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        activity = db.session.query(
            func.date(ActivityLog.created_at).label('date'),
            func.count(ActivityLog.id).label('count')
        ).filter(
            ActivityLog.created_at >= thirty_days_ago
        ).group_by(
            func.date(ActivityLog.created_at)
        ).order_by('date').all()

        dates = []
        counts = []
        for date, count in activity:
            dates.append(date.strftime('%d/%m') if date else 'N/A')
            counts.append(count or 0)

        return jsonify({
            'labels': dates,
            'data': counts,
            'color': '#D4A574'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/api/charts/packages', methods=['GET'])
@login_required
@require_permission('stats', 'read')
def api_packages_chart():
    """Get breakdown by package"""
    try:
        from models.line import LineCache
        from config.database import db
        from sqlalchemy import func

        packages = db.session.query(
            LineCache.package_name,
            func.count(LineCache.id).label('count')
        ).filter(
            LineCache.enabled == True
        ).group_by(
            LineCache.package_name
        ).order_by(db.desc('count')).limit(10).all()

        labels = [pkg[0] or 'N/A' for pkg in packages]
        data = [pkg[1] or 0 for pkg in packages]

        # Generate colors
        colors = ['#D4A574', '#E67E22', '#C1440E', '#27AE60', '#3498DB', '#9B59B6', '#E74C3C', '#F39C12', '#1ABC9C', '#34495E']

        return jsonify({
            'labels': labels,
            'data': data,
            'colors': colors[:len(labels)]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
