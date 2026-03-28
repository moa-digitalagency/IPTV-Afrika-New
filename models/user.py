"""User and Permission models"""
from config.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for admin authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='operator', nullable=False)  # superadmin, admin, operator
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    permissions = db.relationship('Permission', backref='user', lazy=True, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)

    def has_permission(self, resource, action='read'):
        """Check if user has specific permission"""
        if self.role == 'superadmin':
            return True

        perm = Permission.query.filter_by(user_id=self.id, resource=resource).first()
        if not perm:
            return False

        if action == 'read':
            return perm.can_read
        elif action == 'write':
            return perm.can_write
        elif action == 'delete':
            return perm.can_delete

        return False

    def __repr__(self):
        return f'<User {self.username}>'


class Permission(db.Model):
    """Permission model for granular access control"""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    resource = db.Column(db.String(50), nullable=False)  # e.g., 'lines.create', 'telegram.config'
    can_read = db.Column(db.Boolean, default=True)
    can_write = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'resource', name='uq_user_resource'),
    )

    def __repr__(self):
        return f'<Permission {self.user_id}:{self.resource}>'
