"""Telegram bot configuration and conversation models"""
from config.database import db
from datetime import datetime

class TelegramConfig(db.Model):
    """Telegram bot configuration"""
    __tablename__ = 'telegram_config'

    id = db.Column(db.Integer, primary_key=True)
    bot_token = db.Column(db.String(256), nullable=False)
    webhook_url = db.Column(db.String(512), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    chat_id_admin = db.Column(db.String(50), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return '<TelegramConfig>'


class TelegramMessageTemplate(db.Model):
    """Telegram message templates"""
    __tablename__ = 'telegram_message_templates'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)  # Supports {username}, {exp_date}, {package}, {dns_link}
    is_active = db.Column(db.Boolean, default=True)
    lang = db.Column(db.String(5), default='fr')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TelegramMessageTemplate {self.slug}>'


class TelegramConversation(db.Model):
    """Telegram user conversations"""
    __tablename__ = 'telegram_conversations'

    id = db.Column(db.Integer, primary_key=True)
    telegram_user_id = db.Column(db.String(50), nullable=False, index=True)
    telegram_username = db.Column(db.String(100), nullable=True)
    line_golden_id = db.Column(db.Integer, db.ForeignKey('line_cache.golden_id'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, active, validated, closed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    line = db.relationship('LineCache', backref='telegram_conversations')
    validator = db.relationship('User', backref='validated_conversations')

    def __repr__(self):
        return f'<TelegramConversation {self.telegram_user_id}>'
