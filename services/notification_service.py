"""Notification service for sending alerts and messages"""
from datetime import datetime, timedelta
from models.line import LineCache
from models.telegram import TelegramConfig, TelegramMessageTemplate

class NotificationService:
    """Service to handle notifications for expiring lines"""

    EXPIRY_WARNING_DAYS = 7  # Warn 7 days before expiry

    @staticmethod
    def get_expiring_lines(days=EXPIRY_WARNING_DAYS):
        """Get lines expiring within N days"""
        now = datetime.utcnow()
        expiry_date = now + timedelta(days=days)

        lines = LineCache.query.filter(
            LineCache.exp_date > now,
            LineCache.exp_date <= expiry_date,
            LineCache.enabled == True
        ).all()

        return lines

    @staticmethod
    def get_expired_lines():
        """Get lines that have already expired"""
        now = datetime.utcnow()
        lines = LineCache.query.filter(
            LineCache.exp_date < now,
            LineCache.enabled == True
        ).all()

        return lines

    @staticmethod
    def should_notify_line(line):
        """Check if we should notify about a line"""
        if not line or not line.exp_date:
            return False

        days_remaining = (line.exp_date - datetime.utcnow()).days
        return 0 < days_remaining <= NotificationService.EXPIRY_WARNING_DAYS

    @staticmethod
    def format_message(template, line):
        """Format message template with line variables"""
        if not template or not line:
            return None

        message = template.body
        message = message.replace('{username}', line.username or 'N/A')
        message = message.replace('{package}', line.package_name or 'N/A')
        message = message.replace('{dns_link}', line.dns_link or 'N/A')

        if line.exp_date:
            formatted_date = line.exp_date.strftime('%d/%m/%Y')
            message = message.replace('{exp_date}', formatted_date)

        return message

    @staticmethod
    def get_expiry_stats():
        """Get statistics about line expiry"""
        now = datetime.utcnow()

        total_active = LineCache.query.filter_by(enabled=True).count()
        expired = LineCache.query.filter(
            LineCache.exp_date < now,
            LineCache.enabled == True
        ).count()
        expiring_soon = LineCache.query.filter(
            LineCache.exp_date > now,
            LineCache.exp_date <= (now + timedelta(days=NotificationService.EXPIRY_WARNING_DAYS)),
            LineCache.enabled == True
        ).count()

        return {
            'total_active': total_active,
            'expired': expired,
            'expiring_soon': expiring_soon,
            'healthy': total_active - expired - expiring_soon
        }

    @staticmethod
    def get_telegram_config():
        """Get Telegram bot configuration"""
        config = TelegramConfig.query.first()
        return config if config and config.is_active else None

    @staticmethod
    def get_message_template(slug, lang='fr'):
        """Get message template by slug"""
        template = TelegramMessageTemplate.query.filter_by(
            slug=slug,
            lang=lang,
            is_active=True
        ).first()

        if not template:
            # Fallback to default language
            template = TelegramMessageTemplate.query.filter_by(
                slug=slug,
                is_active=True
            ).first()

        return template
