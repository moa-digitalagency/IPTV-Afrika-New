"""
Security Audit Log Model
- Track security-related events
- Rate limit violations
- Failed logins
- Permission denials
- Suspicious activity
"""

from datetime import datetime
from config.database import db

class SecurityAudit(db.Model):
    """Security event audit log"""

    __tablename__ = 'security_audit'

    id = db.Column(db.Integer, primary_key=True)

    # Event type
    event_type = db.Column(db.String(50), nullable=False, index=True)
    # Examples: failed_login, rate_limit, permission_denied, suspicious_pattern,
    #           sql_injection_attempt, xss_attempt, csrf_violation

    # User info (nullable for public routes)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True)

    # Request info
    ip_address = db.Column(db.String(45), nullable=False)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    http_method = db.Column(db.String(10), nullable=True)  # GET, POST, etc.
    endpoint = db.Column(db.String(200), nullable=True)    # /app/lines/create, etc.

    # Details
    severity = db.Column(db.String(20), nullable=False)    # info, warning, critical
    message = db.Column(db.Text)                           # Description
    detail = db.Column(db.JSON)                            # Extra context (dict)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Status/Resolution
    reviewed = db.Column(db.Boolean, default=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    action_taken = db.Column(db.String(200), nullable=True)

    # Indexes
    __table_args__ = (
        db.Index('idx_event_type', 'event_type'),
        db.Index('idx_ip_address', 'ip_address'),
        db.Index('idx_severity', 'severity'),
        db.Index('idx_created_at', 'created_at'),
        db.Index('idx_user_id_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f'<SecurityAudit {self.event_type} from {self.ip_address} at {self.created_at}>'

    @staticmethod
    def log_event(event_type, ip_address, severity='info', user_id=None,
                  username=None, endpoint=None, message=None, detail=None,
                  http_method=None, user_agent=None):
        """
        Log a security event

        Args:
            event_type: Type of security event
            ip_address: Source IP address
            severity: info, warning, critical
            user_id: User ID (optional)
            username: Username (optional)
            endpoint: Flask route/endpoint
            message: Description of event
            detail: Dict with extra details
            http_method: GET, POST, etc.
            user_agent: Browser user agent

        Returns:
            SecurityAudit instance
        """
        try:
            audit = SecurityAudit(
                event_type=event_type,
                ip_address=ip_address,
                severity=severity,
                user_id=user_id,
                username=username,
                endpoint=endpoint,
                message=message,
                detail=detail or {},
                http_method=http_method,
                user_agent=user_agent
            )
            db.session.add(audit)
            db.session.commit()
            return audit
        except Exception as e:
            print(f"Error logging security event: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def get_recent_events(limit=50, severity=None, user_id=None):
        """
        Get recent security events

        Args:
            limit: Max results
            severity: Filter by severity (info, warning, critical)
            user_id: Filter by user

        Returns:
            List of SecurityAudit instances
        """
        query = SecurityAudit.query.order_by(SecurityAudit.created_at.desc())

        if severity:
            query = query.filter_by(severity=severity)

        if user_id:
            query = query.filter_by(user_id=user_id)

        return query.limit(limit).all()

    @staticmethod
    def get_events_by_ip(ip_address, hours=24):
        """
        Get security events from specific IP in recent hours

        Args:
            ip_address: IP to query
            hours: Look back N hours

        Returns:
            List of SecurityAudit instances
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        return SecurityAudit.query.filter(
            SecurityAudit.ip_address == ip_address,
            SecurityAudit.created_at >= cutoff
        ).order_by(SecurityAudit.created_at.desc()).all()

    @staticmethod
    def count_failed_logins(ip_address, minutes=5):
        """
        Count failed login attempts from IP in recent minutes

        Args:
            ip_address: IP to query
            minutes: Look back N minutes

        Returns:
            Count of failed login attempts
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        return SecurityAudit.query.filter(
            SecurityAudit.event_type == 'failed_login',
            SecurityAudit.ip_address == ip_address,
            SecurityAudit.created_at >= cutoff
        ).count()

    @staticmethod
    def count_critical_events(hours=24):
        """
        Count critical security events in recent hours

        Args:
            hours: Look back N hours

        Returns:
            Count of critical events
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        return SecurityAudit.query.filter(
            SecurityAudit.severity == 'critical',
            SecurityAudit.created_at >= cutoff
        ).count()

    @staticmethod
    def export_csv(filepath, days=30):
        """
        Export security audit log to CSV

        Args:
            filepath: Path to save CSV
            days: Export last N days

        Returns:
            True if successful
        """
        import csv
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)

        events = SecurityAudit.query.filter(
            SecurityAudit.created_at >= cutoff
        ).order_by(SecurityAudit.created_at.desc()).all()

        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp', 'Event Type', 'Severity', 'IP Address',
                    'User ID', 'Username', 'Endpoint', 'Method', 'Message'
                ])

                for event in events:
                    writer.writerow([
                        event.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        event.event_type,
                        event.severity,
                        event.ip_address,
                        event.user_id or '',
                        event.username or '',
                        event.endpoint or '',
                        event.http_method or '',
                        event.message or ''
                    ])

            return True
        except Exception as e:
            print(f"Error exporting security audit: {e}")
            return False
