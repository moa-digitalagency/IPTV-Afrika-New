"""Statistics and analytics service"""
from datetime import datetime, timedelta
from sqlalchemy import func
from models.line import LineCache, PackageCache
from models.user import User
from models.logs import ActivityLog, CacheSyncLog

class StatsService:
    """Service to calculate and retrieve statistics"""

    @staticmethod
    def get_dashboard_stats():
        """Get main dashboard statistics"""
        now = datetime.utcnow()

        # Line statistics
        total_lines = LineCache.query.count()
        active_lines = LineCache.query.filter(
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).count()
        expired_lines = LineCache.query.filter(
            LineCache.exp_date < now,
            LineCache.enabled == True
        ).count()
        trial_lines = LineCache.query.filter_by(is_trial=True).count()
        paid_lines = total_lines - trial_lines

        # User statistics
        total_users = User.query.filter_by(is_active=True).count()
        superadmins = User.query.filter_by(role='superadmin', is_active=True).count()
        admins = User.query.filter_by(role='admin', is_active=True).count()
        operators = User.query.filter_by(role='operator', is_active=True).count()

        return {
            'lines': {
                'total': total_lines,
                'active': active_lines,
                'expired': expired_lines,
                'trial': trial_lines,
                'paid': paid_lines
            },
            'users': {
                'total': total_users,
                'superadmins': superadmins,
                'admins': admins,
                'operators': operators
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    @staticmethod
    def get_line_stats():
        """Get detailed line statistics"""
        now = datetime.utcnow()

        # Expiration distribution
        expiring_7days = LineCache.query.filter(
            LineCache.exp_date > now,
            LineCache.exp_date <= now + timedelta(days=7),
            LineCache.enabled == True
        ).count()

        expiring_30days = LineCache.query.filter(
            LineCache.exp_date > now,
            LineCache.exp_date <= now + timedelta(days=30),
            LineCache.enabled == True
        ).count()

        expiring_90days = LineCache.query.filter(
            LineCache.exp_date > now,
            LineCache.exp_date <= now + timedelta(days=90),
            LineCache.enabled == True
        ).count()

        # By package
        by_package = LineCache.query.filter_by(enabled=True).with_entities(
            LineCache.package_name,
            func.count(LineCache.id).label('count')
        ).group_by(LineCache.package_name).all()

        # Trial vs Paid
        trial_active = LineCache.query.filter(
            LineCache.is_trial == True,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).count()

        paid_active = LineCache.query.filter(
            LineCache.is_trial == False,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).count()

        return {
            'expiration': {
                'next_7_days': expiring_7days,
                'next_30_days': expiring_30days,
                'next_90_days': expiring_90days
            },
            'by_package': [
                {'name': pkg, 'count': count} for pkg, count in by_package
            ],
            'subscription_type': {
                'trial_active': trial_active,
                'paid_active': paid_active
            }
        }

    @staticmethod
    def get_activity_stats(days=30):
        """Get activity statistics for last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)

        # Total actions
        total_actions = ActivityLog.query.filter(
            ActivityLog.created_at >= start_date
        ).count()

        # Actions by type
        by_action = ActivityLog.query.filter(
            ActivityLog.created_at >= start_date
        ).with_entities(
            ActivityLog.action,
            func.count(ActivityLog.id).label('count')
        ).group_by(ActivityLog.action).all()

        # Actions by user
        by_user = ActivityLog.query.filter(
            ActivityLog.created_at >= start_date
        ).with_entities(
            User.username,
            func.count(ActivityLog.id).label('count')
        ).join(User).group_by(User.username).all()

        return {
            'total_actions': total_actions,
            'by_action': [
                {'action': action, 'count': count} for action, count in by_action
            ],
            'by_user': [
                {'username': user, 'count': count} for user, count in by_user
            ]
        }

    @staticmethod
    def get_cache_stats():
        """Get cache synchronization statistics"""
        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(days=7)

        # Recent syncs
        recent_syncs = CacheSyncLog.query.filter(
            CacheSyncLog.started_at >= one_day_ago
        ).all()

        successful_syncs = len([s for s in recent_syncs if s.status == 'success'])
        failed_syncs = len([s for s in recent_syncs if s.status == 'error'])

        # Average duration
        avg_duration = CacheSyncLog.query.filter(
            CacheSyncLog.started_at >= one_week_ago,
            CacheSyncLog.status == 'success'
        ).with_entities(
            func.avg(CacheSyncLog.duration_ms).label('avg_duration')
        ).scalar() or 0

        # Last sync
        last_sync = CacheSyncLog.query.order_by(
            CacheSyncLog.finished_at.desc()
        ).first()

        return {
            'recent_syncs': len(recent_syncs),
            'successful': successful_syncs,
            'failed': failed_syncs,
            'average_duration_ms': int(avg_duration),
            'last_sync': {
                'timestamp': last_sync.finished_at.isoformat() if last_sync else None,
                'status': last_sync.status if last_sync else None,
                'duration_ms': last_sync.duration_ms if last_sync else None
            }
        }

    @staticmethod
    def get_full_stats():
        """Get all statistics combined"""
        return {
            'dashboard': StatsService.get_dashboard_stats(),
            'lines': StatsService.get_line_stats(),
            'activity': StatsService.get_activity_stats(),
            'cache': StatsService.get_cache_stats()
        }
