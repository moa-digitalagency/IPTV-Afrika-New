# Phase 6 — Telegram Bot Integration

**Status**: ✅ Completed
**Date**: 2026-03-28

---

## Overview

Phase 6 implements complete Telegram Bot integration for notifications and user management. Admins can now:
- Configure bot token and webhook URL
- Send test messages to verify connectivity
- Create and customize message templates with variable substitution
- Manage user conversations and validate/close interactions
- Receive messages from Telegram users via webhook
- Track conversation status (pending → active → validated → closed)
- Log all Telegram interactions for audit

All features include proper error handling, permission checks, and activity logging.

---

## Files Created

### Service — `services/telegram_service.py`
Core Telegram integration service with 13 methods:

| Method | Purpose |
|--------|---------|
| `get_config()` | Retrieve active Telegram configuration |
| `set_webhook(webhook_url, token)` | Configure Telegram webhook |
| `test_bot_token(token)` | Validate bot token |
| `send_message(chat_id, text, parse_mode)` | Send message via Telegram API |
| `get_template(slug, lang)` | Fetch message template by slug |
| `format_message(template, line, user)` | Substitute variables in template |
| `create_conversation(telegram_user_id, username, line_id)` | Start new conversation |
| `update_conversation_status(id, status, validator_id, notes)` | Update conversation state |
| `send_expiry_notification(line, days_before, lang)` | Send line expiry warning |
| `send_batch_notifications(days_before, lang)` | Send bulk notifications |
| `get_or_create_admin_chat()` | Get admin chat ID |

**Error Handling:**
- Custom `TelegramException` for API errors
- 10-second timeout on all requests
- Proper HTTP error messages from Telegram
- Fallback to French templates if language not found

### Routes — `routes/telegram.py`
8 endpoints for bot management and conversations:

| Route | Method | Purpose | Permission |
|-------|--------|---------|-----------|
| `/app/telegram/config` | GET, POST | Bot configuration page | `telegram.config:write` |
| `/app/telegram/webhook/set` | POST | Set webhook URL | `telegram.config:write` |
| `/app/telegram/templates` | GET | List message templates | `telegram.templates:read` |
| `/app/telegram/templates/<slug>/edit` | GET, POST | Edit template | `telegram.templates:write` |
| `/app/telegram/conversations` | GET | List conversations | `telegram.conversations:read` |
| `/app/telegram/conversations/<id>/validate` | POST | Validate conversation | `telegram.conversations:write` |
| `/app/telegram/conversations/<id>/close` | POST | Close conversation | `telegram.conversations:write` |
| `/app/telegram/webhook` | POST | Receive Telegram messages | Exempt CSRF |
| `/app/telegram/test-message` | POST | Send test message | `telegram.config:write` |

**Key Features:**
- `@superadmin_required` for sensitive operations (config, test)
- `@require_permission` for granular access control
- Activity logging with `log_action()` helper
- Webhook route exempterom CSRF for Telegram compatibility
- JSON responses for AJAX operations
- Proper form validation and error messages

### Templates

#### `templates/app/telegram/config.html`
Bot configuration page:

**Sections:**
1. **Setup Guide**
   - Step-by-step instructions for creating bot via @BotFather
   - Variable substitution guide (6 variables)

2. **Configuration Form**
   - Bot Token input (password field, double-click to reveal)
   - Webhook URL input (HTTPS required)
   - Admin Chat ID input (supports group chats with -100 prefix)
   - Save button

3. **Status Panel** (if bot configured)
   - Status indicator (green if active)
   - Webhook configuration status
   - Admin chat ID display
   - Last update timestamp

4. **Action Buttons**
   - Configure Webhook button (AJAX)
   - Send Test Message button (AJAX)

#### `templates/app/telegram/templates.html`
Message template management:

**Sections:**
1. **Variable Reference**
   - 6 available variables in grid cards
   - {username}, {package}, {exp_date}, {days_left}, {dns_link}, {max_connections}

2. **Template Cards**
   - Template title and slug
   - Language indicator (🇫🇷 French, 🇬🇧 English)
   - Active/Inactive badge
   - Message preview
   - Edit button per template

3. **Empty State**
   - Message when no templates available

#### `templates/app/telegram/template_edit.html`
Template editor with live preview:

**Layout:** 2-column (form | preview)

**Left Column:**
- Title input
- Message textarea with variable hints
- Active checkbox

**Right Column:**
1. **Variable Reference Table**
   - 6 mock values displayed
   - username, package, exp_date, days_left, dns_link, max_connections

2. **Live Preview Box**
   - Shows message with variables substituted
   - Updates on each keystroke
   - Uses mock data for demonstration
   - Min-height 200px, full formatting applied

**Features:**
- Real-time preview with JavaScript
- Form submission saves changes
- Back button returns to template list

#### `templates/app/telegram/conversations.html`
Conversation management interface:

**Sections:**
1. **Status Filter**
   - 5 filter buttons: All, Pending ⏳, Active 💬, Validated ✅, Closed ❌
   - Active filter button highlighted

2. **Conversations Table**
   - Username @handle + Telegram User ID
   - M3U username + Package name
   - Current status (color-coded)
   - Started date and last activity date
   - Action buttons: Validate (✅), Close (❌)

3. **Pagination**
   - 20 conversations per page
   - First/Previous/Next/Last navigation
   - Page number indicators

4. **Validate Modal**
   - Confirmation dialog
   - Optional notes textarea
   - Validator automatically set to current_user
   - AJAX submission with reload on success

5. **Close Modal**
   - Warning message about permanent closure
   - Simple confirmation form
   - AJAX submission with reload on success

6. **Empty State**
   - "No conversations" message with icon

---

## Database Models (Already Defined)

### `TelegramConfig`
| Field | Type | Constraint |
|-------|------|-----------|
| id | SERIAL | PK |
| bot_token | VARCHAR(256) | NOT NULL |
| webhook_url | VARCHAR(512) | |
| is_active | BOOLEAN | DEFAULT TRUE |
| chat_id_admin | VARCHAR(50) | |
| updated_at | TIMESTAMP | DEFAULT NOW() |
| updated_by | INTEGER | FK users.id |

### `TelegramMessageTemplate`
| Field | Type | Constraint |
|-------|------|-----------|
| id | SERIAL | PK |
| slug | VARCHAR(50) | UNIQUE NOT NULL |
| title | VARCHAR(200) | NOT NULL |
| body | TEXT | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| lang | VARCHAR(5) | DEFAULT 'fr' |
| UNIQUE(slug, lang) | | |

### `TelegramConversation`
| Field | Type | Constraint |
|-------|------|-----------|
| id | SERIAL | PK |
| telegram_user_id | BIGINT | NOT NULL |
| telegram_username | VARCHAR(100) | |
| line_golden_id | INTEGER | FK line_cache.golden_id |
| status | VARCHAR(20) | DEFAULT 'pending' — pending/active/validated/closed |
| started_at | TIMESTAMP | DEFAULT NOW() |
| last_message_at | TIMESTAMP | |
| validated_by | INTEGER | FK users.id |
| notes | TEXT | |

---

## API Endpoints

### Telegram Bot API

**Set Webhook:**
```
POST https://api.telegram.org/bot{TOKEN}/setWebhook
Body: {"url": "https://example.com/app/telegram/webhook"}
```

**Send Message:**
```
POST https://api.telegram.org/bot{TOKEN}/sendMessage
Body: {
    "chat_id": 123456,
    "text": "Your message",
    "parse_mode": "HTML"
}
```

**Get Bot Info:**
```
GET https://api.telegram.org/bot{TOKEN}/getMe
```

### Internal AJAX

**Test Message:**
```
POST /app/telegram/test-message
Returns: {"success": bool, "message": str}
```

**Validate Conversation:**
```
POST /app/telegram/conversations/{id}/validate
Body: notes=optional_text
Returns: {"success": bool, "message": str}
```

**Close Conversation:**
```
POST /app/telegram/conversations/{id}/close
Returns: {"success": bool, "message": str}
```

---

## Message Template Variables

All templates support these placeholders:

| Variable | Example | Source |
|----------|---------|--------|
| `{username}` | `user_test123` | `line_cache.username` |
| `{package}` | `Premium 4K` | `line_cache.package_name` |
| `{exp_date}` | `15/04/2026` | `line_cache.exp_date` formatted |
| `{days_left}` | `18` | `days_remaining(exp_date)` |
| `{dns_link}` | `http://example.com/m3u/...` | `line_cache.dns_link` |
| `{max_connections}` | `4` | `line_cache.max_connections` |
| `{created_at}` | `28/03/2026` | `line_cache.created_at` formatted |

**Substitution:**
- Case-sensitive matching on variable names
- Safe string replacement using `replace()`
- No escaping needed (Telegram handles HTML)
- Missing variables replaced with "N/A"

---

## Conversation Workflow

```
START (Telegram message received)
  ↓
[webhook] → log message → create conversation (pending)
  ↓
[admin] → review in /app/telegram/conversations
  ↓
[action] → validate → status = 'validated', set validator_id
  ↓
[or close] → status = 'closed'
```

**Statuses:**
- **pending**: New conversation, awaiting review
- **active**: Conversation in progress
- **validated**: User verified and approved
- **closed**: Conversation ended, archived

---

## Security Considerations

1. **Bot Token**: Stored in DB, shown as password field, double-click to reveal
2. **Webhook**: CSRF exemption required for Telegram POST requests
3. **Secret Token**: Telegram can sign requests (optional, not implemented in Phase 6)
4. **Permissions**: `@superadmin_required` for config, `@require_permission` for templates/conversations
5. **Activity Logging**: All actions logged with user, action, detail, IP
6. **Input Validation**: Template body and notes validated for length/content

---

## Testing Checklist

- [x] Bot token validation works
- [x] Webhook configuration sends to Telegram API
- [x] Test message sends to admin chat
- [x] Templates display with variable substitution
- [x] Template preview updates in real-time
- [x] Conversations load with pagination
- [x] Validate/close actions update status
- [x] Webhook receives Telegram messages
- [x] Permission checks prevent unauthorized access
- [x] Activity logged for all operations

---

## Configuration Example

**Environment Variables (if using .env):**
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_WEBHOOK_URL=https://example.com/app/telegram/webhook
TELEGRAM_ADMIN_CHAT_ID=-1001234567890
```

**Via Admin Panel:**
1. Go to `/app/telegram/` (redirects to config)
2. Enter bot token from @BotFather
3. Enter webhook URL (your domain + `/app/telegram/webhook`)
4. Enter admin chat ID (get from `/getUpdates`)
5. Click "Sauvegarder"
6. Click "Configurer Webhook"
7. Send test message to verify

---

## Webhook Implementation Details

**Route:** `POST /app/telegram/webhook` (CSRF exempt)

**Expected Telegram Payload:**
```json
{
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "date": 1234567890,
        "chat": {"id": 123456},
        "from": {
            "id": 987654321,
            "is_bot": false,
            "first_name": "John",
            "username": "johndoe"
        },
        "text": "User message text"
    }
}
```

**Processing:**
1. Extract message data
2. Get Telegram user ID and username
3. Log in ActivityLog (not linked to system user)
4. Create/update conversation if needed
5. Return `{"ok": true}` immediately to Telegram

**Error Handling:**
- All errors logged but return `ok: true` (prevents Telegram retries)
- No error details exposed to Telegram
- Failed payloads stored in ActivityLog

---

## Future Enhancements (Phase 6.1+)

- **Message Parsing**: Extract M3U username/password from user input
- **Conversation Commands**: `/start`, `/help`, `/status`, `/renew` commands
- **Automatic Validation**: Pre-validate conversations based on line ownership
- **Message Delivery**: Track failed message deliveries
- **Scheduled Notifications**: Cron job to send weekly/monthly reminders
- **Rich Media**: Support image/file attachments in templates
- **Multi-language**: Full i18n support for French/English
- **Telegram Groups**: Send summary reports to group chats
- **User Blocking**: Blacklist abusive users
- **Conversation Export**: Download conversation history as PDF

---

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `services/telegram_service.py` | 200 | Telegram API wrapper + business logic |
| `routes/telegram.py` | 280 | 8 endpoints for config/templates/conversations |
| `templates/app/telegram/config.html` | 180 | Bot configuration UI |
| `templates/app/telegram/templates.html` | 140 | Template management list |
| `templates/app/telegram/template_edit.html` | 230 | Template editor with preview |
| `templates/app/telegram/conversations.html` | 270 | Conversation manager with modals |
| `routes/__init__.py` | 14 | Register telegram blueprint |
| `templates/app/base.html` | 187 | Updated sidebar link |

**Total New Code**: ~1,500 lines
**External Dependencies**: python-telegram-bot (already in requirements)
**Database Tables**: 3 (TelegramConfig, TelegramMessageTemplate, TelegramConversation)

---

## Next Phase (Phase 7)

User Management:
- CRUD operations for user accounts
- Role assignment (superadmin, admin, operator)
- Permission management (granular resource-based)
- Password reset and account lockout
- User activity audit trail

See `PHASE_7_USER_MANAGEMENT.md` for details.
