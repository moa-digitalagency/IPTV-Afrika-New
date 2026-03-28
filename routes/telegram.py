"""Telegram Bot routes"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from config.database import db
from models.telegram import TelegramConfig, TelegramMessageTemplate, TelegramConversation
from models.logs import ActivityLog
from services.telegram_service import TelegramService, TelegramException
from security.decorators import require_permission, superadmin_required

telegram_bp = Blueprint('telegram', __name__, url_prefix='/app/telegram')

# ===== HELPER FUNCTIONS =====

def log_action(action, detail=None):
    """Log user action"""
    activity = ActivityLog(
        user_id=current_user.id,
        action=action,
        target_type='telegram',
        target_id=None,
        detail=detail or {},
        ip_address=request.remote_addr
    )
    db.session.add(activity)
    db.session.commit()

# ===== BOT CONFIGURATION =====

@telegram_bp.route('/config', methods=['GET', 'POST'])
@login_required
@require_permission('telegram.config', 'write')
@superadmin_required
def config():
    """Telegram bot configuration"""
    if request.method == 'GET':
        config = TelegramService.get_config()
        return render_template('app/telegram/config.html', config=config)

    # POST: Update config
    try:
        bot_token = request.form.get('bot_token', '').strip()
        webhook_url = request.form.get('webhook_url', '').strip()
        chat_id_admin = request.form.get('chat_id_admin', '').strip()

        if not bot_token:
            flash('Le token du bot est requis', 'danger')
            return redirect(url_for('telegram.config'))

        # Test bot token
        bot_username = TelegramService.test_bot_token(bot_token)
        if not bot_username:
            flash('Token du bot invalide', 'danger')
            return redirect(url_for('telegram.config'))

        # Get or create config
        config = TelegramService.get_config()
        if not config:
            config = TelegramConfig()
            db.session.add(config)

        config.bot_token = bot_token
        config.webhook_url = webhook_url
        config.chat_id_admin = chat_id_admin
        config.is_active = True
        config.updated_at = datetime.utcnow()
        config.updated_by = current_user.id

        db.session.commit()

        log_action('telegram_config_update', {
            'bot_username': bot_username,
            'has_webhook': bool(webhook_url)
        })

        flash(f'✅ Configuration sauvegardée (@{bot_username})', 'success')
        return redirect(url_for('telegram.config'))

    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('telegram.config'))

# ===== WEBHOOK SETUP =====

@telegram_bp.route('/webhook/set', methods=['POST'])
@login_required
@require_permission('telegram.config', 'write')
@superadmin_required
def webhook_set():
    """Set webhook URL"""
    try:
        webhook_url = request.form.get('webhook_url', '').strip()
        if not webhook_url:
            return jsonify({'success': False, 'message': 'URL du webhook requise'}), 400

        TelegramService.set_webhook(webhook_url)

        log_action('telegram_webhook_set', {'webhook_url': webhook_url})

        return jsonify({
            'success': True,
            'message': 'Webhook configuré avec succès'
        })

    except TelegramException as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== MESSAGE TEMPLATES =====

@telegram_bp.route('/templates', methods=['GET'])
@login_required
@require_permission('telegram.templates', 'read')
def templates():
    """List message templates"""
    templates = TelegramMessageTemplate.query.all()
    return render_template('app/telegram/templates.html', templates=templates)

@telegram_bp.route('/templates/<slug>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('telegram.templates', 'write')
@superadmin_required
def template_edit(slug):
    """Edit message template"""
    template = TelegramMessageTemplate.query.filter_by(slug=slug).first()
    if not template:
        flash('Template non trouvé', 'danger')
        return redirect(url_for('telegram.templates'))

    if request.method == 'GET':
        return render_template('app/telegram/template_edit.html', template=template)

    # POST: Update template
    try:
        title = request.form.get('title', '').strip()
        body = request.form.get('body', '').strip()
        is_active = request.form.get('is_active') == 'on'

        if not title or not body:
            flash('Tous les champs sont requis', 'danger')
            return redirect(url_for('telegram.template_edit', slug=slug))

        template.title = title
        template.body = body
        template.is_active = is_active

        db.session.commit()

        log_action('telegram_template_update', {
            'slug': slug,
            'is_active': is_active
        })

        flash('✅ Template sauvegardé', 'success')
        return redirect(url_for('telegram.templates'))

    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('telegram.template_edit', slug=slug))

# ===== CONVERSATIONS =====

@telegram_bp.route('/conversations', methods=['GET'])
@login_required
@require_permission('telegram.conversations', 'read')
def conversations():
    """List conversations"""
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = TelegramConversation.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    paginated = query.order_by(TelegramConversation.started_at.desc()).paginate(
        page=page,
        per_page=per_page
    )

    return render_template('app/telegram/conversations.html',
        conversations=paginated.items,
        total=paginated.total,
        pages=paginated.pages,
        current_page=page,
        status_filter=status_filter,
        statuses=['pending', 'active', 'validated', 'closed']
    )

@telegram_bp.route('/conversations/<int:conversation_id>/validate', methods=['POST'])
@login_required
@require_permission('telegram.conversations', 'write')
def conversation_validate(conversation_id):
    """Validate conversation"""
    try:
        conversation = TelegramConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'success': False, 'message': 'Conversation non trouvée'}), 404

        notes = request.form.get('notes', '').strip()

        TelegramService.update_conversation_status(
            conversation_id,
            'validated',
            validator_id=current_user.id,
            notes=notes
        )

        log_action('telegram_conversation_validate', {
            'conversation_id': conversation_id,
            'telegram_user_id': conversation.telegram_user_id
        })

        return jsonify({
            'success': True,
            'message': 'Conversation validée'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@telegram_bp.route('/conversations/<int:conversation_id>/close', methods=['POST'])
@login_required
@require_permission('telegram.conversations', 'write')
def conversation_close(conversation_id):
    """Close conversation"""
    try:
        conversation = TelegramConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'success': False, 'message': 'Conversation non trouvée'}), 404

        TelegramService.update_conversation_status(conversation_id, 'closed')

        log_action('telegram_conversation_close', {
            'conversation_id': conversation_id
        })

        return jsonify({
            'success': True,
            'message': 'Conversation fermée'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== WEBHOOK RECEIVER =====

@telegram_bp.route('/webhook', methods=['POST'])
def webhook_receiver():
    """Receive messages from Telegram (exempté CSRF)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'ok': True}), 200

        # Extract message data
        message = data.get('message', {})
        telegram_user_id = message.get('from', {}).get('id')
        telegram_username = message.get('from', {}).get('username')
        text = message.get('text', '')

        if not telegram_user_id:
            return jsonify({'ok': True}), 200

        # Log incoming message
        activity = ActivityLog(
            user_id=None,  # Telegram user, not system user
            action='telegram_message_received',
            target_type='telegram',
            target_id=telegram_user_id,
            detail={
                'telegram_username': telegram_username,
                'text': text[:100]  # Truncate for storage
            },
            ip_address=request.remote_addr
        )
        db.session.add(activity)
        db.session.commit()

        # TODO: Implement message parsing and conversation logic
        # For now, just acknowledge receipt

        return jsonify({'ok': True}), 200

    except Exception as e:
        # Don't expose errors to Telegram, just log and return ok
        db.session.add(ActivityLog(
            user_id=None,
            action='telegram_webhook_error',
            target_type='telegram',
            detail={'error': str(e)},
            ip_address=request.remote_addr
        ))
        db.session.commit()
        return jsonify({'ok': True}), 200

# ===== TEST MESSAGE =====

@telegram_bp.route('/test-message', methods=['POST'])
@login_required
@require_permission('telegram.config', 'write')
@superadmin_required
def test_message():
    """Send test message to admin chat"""
    try:
        config = TelegramService.get_config()
        if not config or not config.chat_id_admin:
            return jsonify({'success': False, 'message': 'Configuration Telegram non trouvée'}), 400

        TelegramService.send_message(
            config.chat_id_admin,
            '✅ <b>Test Message</b>\n\nCe message confirme que votre bot Telegram fonctionne correctement!'
        )

        return jsonify({
            'success': True,
            'message': f'Message test envoyé au chat {config.chat_id_admin}'
        })

    except TelegramException as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
