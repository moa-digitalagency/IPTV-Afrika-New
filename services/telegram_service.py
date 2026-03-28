"""Telegram Bot Service"""
import requests
import json
from datetime import datetime
from config.database import db
from models.telegram import TelegramConfig, TelegramConversation, TelegramMessageTemplate
from models.line import LineCache
from utils.date_helpers import days_remaining


class TelegramException(Exception):
    """Telegram service exception"""
    pass


class TelegramService:
    """Service for Telegram Bot integration"""

    BASE_URL = "https://api.telegram.org"
    TIMEOUT = 10

    @staticmethod
    def get_config():
        """Get active Telegram config"""
        return TelegramConfig.query.filter_by(is_active=True).first()

    @staticmethod
    def set_webhook(webhook_url, token=None):
        """Set Telegram webhook URL"""
        config = TelegramService.get_config()
        if not config and not token:
            raise TelegramException("Aucune configuration Telegram active")

        if not token:
            token = config.bot_token

        try:
            url = f"{TelegramService.BASE_URL}/bot{token}/setWebhook"
            response = requests.post(
                url,
                json={"url": webhook_url},
                timeout=TelegramService.TIMEOUT
            )
            result = response.json()

            if not result.get('ok'):
                raise TelegramException(f"Erreur Telegram: {result.get('description', 'Erreur inconnue')}")

            if config:
                config.webhook_url = webhook_url
                db.session.commit()

            return True
        except requests.exceptions.RequestException as e:
            raise TelegramException(f"Erreur réseau: {str(e)}")

    @staticmethod
    def test_bot_token(token):
        """Test if bot token is valid"""
        try:
            url = f"{TelegramService.BASE_URL}/bot{token}/getMe"
            response = requests.get(url, timeout=TelegramService.TIMEOUT)
            result = response.json()

            if not result.get('ok'):
                return False

            return result.get('result', {}).get('username')
        except:
            return False

    @staticmethod
    def send_message(chat_id, text, parse_mode='HTML'):
        """Send message to Telegram user"""
        config = TelegramService.get_config()
        if not config:
            raise TelegramException("Aucune configuration Telegram active")

        try:
            url = f"{TelegramService.BASE_URL}/bot{config.bot_token}/sendMessage"
            response = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=TelegramService.TIMEOUT
            )
            result = response.json()

            if not result.get('ok'):
                raise TelegramException(f"Erreur Telegram: {result.get('description', 'Erreur inconnue')}")

            return result.get('result', {}).get('message_id')
        except requests.exceptions.RequestException as e:
            raise TelegramException(f"Erreur réseau: {str(e)}")

    @staticmethod
    def get_template(slug, lang='fr'):
        """Get message template by slug"""
        template = TelegramMessageTemplate.query.filter_by(
            slug=slug,
            lang=lang,
            is_active=True
        ).first()

        if not template:
            # Fallback to French if lang not found
            if lang != 'fr':
                return TelegramService.get_template(slug, 'fr')
            return None

        return template

    @staticmethod
    def format_message(template, line, user=None):
        """Format template with line data"""
        if not template:
            return None

        variables = {
            'username': line.username,
            'package': line.package_name or 'N/A',
            'exp_date': line.exp_date.strftime('%d/%m/%Y') if line.exp_date else 'N/A',
            'days_left': str(days_remaining(line.exp_date)) if line.exp_date else 'N/A',
            'dns_link': line.dns_link or 'N/A',
            'max_connections': str(line.max_connections),
            'created_at': line.created_at.strftime('%d/%m/%Y') if line.created_at else 'N/A'
        }

        text = template.body
        for key, value in variables.items():
            text = text.replace(f'{{{key}}}', str(value))

        return text

    @staticmethod
    def create_conversation(telegram_user_id, telegram_username, line_golden_id):
        """Start a new conversation"""
        existing = TelegramConversation.query.filter_by(
            telegram_user_id=telegram_user_id,
            line_golden_id=line_golden_id
        ).first()

        if existing:
            return existing

        conversation = TelegramConversation(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            line_golden_id=line_golden_id,
            status='pending'
        )
        db.session.add(conversation)
        db.session.commit()

        return conversation

    @staticmethod
    def update_conversation_status(conversation_id, status, validator_id=None, notes=None):
        """Update conversation status"""
        conversation = TelegramConversation.query.get(conversation_id)
        if not conversation:
            raise TelegramException("Conversation non trouvée")

        conversation.status = status
        if validator_id:
            conversation.validated_by = validator_id
        if notes:
            conversation.notes = notes
        conversation.last_message_at = datetime.utcnow()

        db.session.commit()
        return conversation

    @staticmethod
    def send_expiry_notification(line, days_before=7, lang='fr'):
        """Send expiry warning notification"""
        config = TelegramService.get_config()
        if not config or not config.chat_id_admin:
            return False

        template = TelegramService.get_template('expiry_warning', lang)
        if not template:
            return False

        message = TelegramService.format_message(template, line)
        if not message:
            return False

        try:
            TelegramService.send_message(config.chat_id_admin, message)
            return True
        except TelegramException:
            return False

    @staticmethod
    def send_batch_notifications(days_before=7, lang='fr'):
        """Send notifications for lines expiring soon"""
        config = TelegramService.get_config()
        if not config or not config.is_active:
            return 0

        now = datetime.utcnow()
        expiry_date = now + timedelta(days=days_before)

        lines = LineCache.query.filter(
            LineCache.exp_date >= now,
            LineCache.exp_date <= expiry_date,
            LineCache.enabled == True
        ).all()

        sent_count = 0
        for line in lines:
            if TelegramService.send_expiry_notification(line, days_before, lang):
                sent_count += 1

        return sent_count

    @staticmethod
    def get_or_create_admin_chat():
        """Get admin chat ID or return None"""
        config = TelegramService.get_config()
        return config.chat_id_admin if config else None


from datetime import timedelta
