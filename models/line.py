"""Line and Package cache models"""
from config.database import db
from datetime import datetime

class LineCache(db.Model):
    """Cache of GOLDEN API lines (M3U subscriptions)"""
    __tablename__ = 'line_cache'

    id = db.Column(db.Integer, primary_key=True)
    golden_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    password = db.Column(db.String(100), nullable=True)
    full_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    package_id = db.Column(db.Integer, nullable=True)
    package_name = db.Column(db.String(200), nullable=True)
    is_trial = db.Column(db.Boolean, default=False, nullable=False, index=True)
    exp_date = db.Column(db.DateTime, nullable=True, index=True)
    enabled = db.Column(db.Boolean, default=True, index=True)
    max_connections = db.Column(db.SmallInteger, default=1)
    note = db.Column(db.Text, nullable=True)
    dns_link = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    cached_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def is_expired(self):
        """Check if line is expired"""
        if not self.exp_date:
            return False
        return datetime.utcnow() > self.exp_date

    def days_remaining(self):
        """Get days remaining until expiration"""
        if not self.exp_date:
            return None
        delta = self.exp_date - datetime.utcnow()
        return max(0, delta.days)

    def __repr__(self):
        return f'<LineCache {self.username}>'


class PackageCache(db.Model):
    """Cache of GOLDEN API packages"""
    __tablename__ = 'packages_cache'

    id = db.Column(db.Integer, primary_key=True)
    golden_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    package_name = db.Column(db.String(200), nullable=False)
    is_trial = db.Column(db.Boolean, default=False, nullable=False)
    duration_days = db.Column(db.Integer, nullable=True)
    credits_cost = db.Column(db.Float, nullable=True)
    cached_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<PackageCache {self.package_name}>'
