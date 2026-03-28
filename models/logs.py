"""Logging models for auditing and monitoring"""
from config.database import db
from datetime import datetime
import json

class ActivityLog(db.Model):
    """User activity audit log"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)  # create, update, delete, extend, refund
    target_type = db.Column(db.String(50), nullable=False)  # line, user, settings
    target_id = db.Column(db.Integer, nullable=True)
    detail = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f'<ActivityLog {self.action}:{self.target_type}>'


class CacheSyncLog(db.Model):
    """Cache synchronization log"""
    __tablename__ = 'cache_sync_logs'

    id = db.Column(db.Integer, primary_key=True)
    sync_type = db.Column(db.String(50), nullable=False)  # lines, packages
    status = db.Column(db.String(20), default='pending')  # pending, success, error
    lines_synced = db.Column(db.Integer, default=0)
    error_msg = db.Column(db.Text, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<CacheSyncLog {self.sync_type}:{self.status}>'
