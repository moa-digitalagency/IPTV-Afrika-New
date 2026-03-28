# Phase 1 — Fondations (Setup Guide)

## ✅ What Was Completed

Phase 1 implementation includes the complete foundation for the IPTV Afrika admin webapp:

### 1. Configuration System
- **config/base.py** — Base configuration class with Flask settings
- **config/development.py** — Development configuration (DEBUG=True)
- **config/production.py** — Production configuration (DEBUG=False)
- **config/database.py** — SQLAlchemy database instance (singleton)

### 2. Database Models (11 tables)
- **models/user.py** — User and Permission models with role-based access control
- **models/line.py** — LineCache and PackageCache models for GOLDEN API data sync
- **models/telegram.py** — TelegramConfig, TelegramMessageTemplate, TelegramConversation
- **models/settings.py** — AppSetting and SeoSetting key-value stores
- **models/logs.py** — ActivityLog (audit trail) and CacheSyncLog (sync monitoring)

### 3. Security & Authentication
- **security/auth.py** — Flask-Login configuration with user loader
- **security/decorators.py** — Custom decorators (@require_permission, @superadmin_required)
- **routes/auth.py** — Login/Logout routes (/auth/login, /auth/logout)

### 4. Admin Routes & Blueprints
- **routes/auth.py** — Authentication blueprint
- **routes/dashboard.py** — Dashboard blueprint (/app/)
- **routes/__init__.py** — Blueprint registration function

### 5. Templates
- **templates/auth/login.html** — Luxurious login page matching design system
- **templates/app/dashboard.html** — Basic dashboard with navbar and stat cards

### 6. Database Initialization
- **init_db.py** — Script to create all tables and initialize superadmin user
  - Creates default AppSettings (golden_api_key, golden_api_base_url, cache TTL)
  - Creates default Telegram message templates
  - Initializes superadmin user (username: admin, password: change_me_in_production)

### 7. Configuration Files
- **.env.example** — Environment variables template
- **requirements.txt** — Updated with 11 dependencies (Flask-Login, Flask-SQLAlchemy, psycopg2, etc.)

### 8. Utilities & Services
- **utils/date_helpers.py** — Date formatting and expiry checking
- **utils/formatters.py** — Currency, password masking, role formatting
- **utils/validators.py** — Username, email, phone, password validation
- **services/golden_api.py** — GOLDEN API wrapper (template for Phase 2)
- **scripts/sync_cache.py** — Cache sync script (template for Phase 2)
- **lang/fr.json** — French translation strings

### 9. App Configuration
- **app.py** — Enhanced with database, Flask-Login, and blueprint registration
  - Maintains all existing routes (/, /catalog, /api/channels)
  - Adds new admin routes (/auth/login, /app/)

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

### 3. Initialize Database
```bash
python init_db.py
```

This will:
- Create all 11 database tables
- Create a superadmin user (username: `admin`, password: `change_me_in_production`)
- Add default application settings
- Add default Telegram message templates

### 4. Run the Application
```bash
python app.py
```

### 5. Access the App
- **Landing Pages**: http://localhost:5000/
- **Admin Login**: http://localhost:5000/auth/login
- **Admin Dashboard**: http://localhost:5000/app/ (after login)

---

## 📋 Database Tables

All tables are created automatically by `init_db.py`:

| Table | Purpose |
|-------|---------|
| users | Admin users with roles (superadmin, admin, operator) |
| permissions | Granular resource-based permissions |
| line_cache | Cached GOLDEN API M3U subscription data |
| packages_cache | Cached GOLDEN API packages |
| telegram_config | Telegram bot settings |
| telegram_message_templates | Message templates with variable substitution |
| telegram_conversations | User conversations for Telegram bot |
| app_settings | Key-value configuration store |
| seo_settings | SEO metadata for pages |
| activity_logs | Audit trail of user actions |
| cache_sync_logs | Monitoring of cache synchronization |

---

## 🔒 Security Setup

- **Flask-Login**: Session-based authentication with user_loader
- **Custom Decorators**:
  - `@require_permission(resource, action)` — Check granular permissions
  - `@superadmin_required` — Restrict to superadmin role
- **Password Hashing**: Werkzeug generate_password_hash for secure storage
- **CSRF Protection**: Ready for Flask-WTF (Phase 9)

---

## ⚙️ Environment Variables

The app reads from `.env` file with these keys:

```
FLASK_ENV=development              # development or production
SECRET_KEY=your-secret-key         # Change in production!
DATABASE_URL=postgresql://...      # PostgreSQL connection string
GOLDEN_API_KEY=                    # GOLDEN API authentication key
GOLDEN_API_BASE_URL=               # GOLDEN API endpoint
CACHE_TTL_LINES=900                # Cache TTL in seconds (15 min)
CACHE_TTL_PACKAGES=3600            # Cache TTL in seconds (1 hour)
TELEGRAM_BOT_TOKEN=                # Telegram bot token
TELEGRAM_SECRET_TOKEN=             # Telegram webhook secret
```

---

## 📁 Project Structure

```
IPTV-Afrika-New/
├── config/
│   ├── __init__.py
│   ├── base.py
│   ├── database.py          (SQLAlchemy singleton)
│   ├── development.py
│   └── production.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── line.py
│   ├── telegram.py
│   ├── settings.py
│   └── logs.py
├── routes/
│   ├── __init__.py          (register_blueprints)
│   ├── auth.py
│   └── dashboard.py
├── security/
│   ├── __init__.py
│   ├── auth.py              (Flask-Login setup)
│   └── decorators.py        (Permission checking)
├── services/
│   ├── __init__.py
│   └── golden_api.py        (API wrapper — to implement)
├── utils/
│   ├── __init__.py
│   ├── date_helpers.py
│   ├── formatters.py
│   └── validators.py
├── scripts/
│   ├── __init__.py
│   └── sync_cache.py        (Cron task — to implement)
├── templates/
│   ├── index.html           (existing landing page)
│   ├── catalog.html         (existing)
│   ├── auth/
│   │   └── login.html       (NEW)
│   └── app/
│       └── dashboard.html   (NEW)
├── statics/                 (CSS, JS, images)
├── app.py                   (ENHANCED)
├── init_db.py               (NEW)
├── requirements.txt         (UPDATED)
├── .env.example             (NEW)
└── docs/
    └── PHASE_1_SETUP.md     (this file)
```

---

## 🔍 Verification Steps

After setup, verify everything works:

```bash
# 1. Check database tables were created
python -c "from config.database import db; from flask import Flask; app = Flask(__name__); app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'; db.init_app(app); print('✅ Database OK')"

# 2. Test login route
curl http://localhost:5000/auth/login

# 3. Test existing routes still work
curl http://localhost:5000/           # Should serve index.html
curl http://localhost:5000/api/channels  # Should return channel data

# 4. Check superadmin user exists
python -c "from config.database import db; from models.user import User; from flask import Flask; from config.development import DevelopmentConfig; app = Flask(__name__); app.config.from_object(DevelopmentConfig); db.init_app(app); app.app_context().push(); admin = User.query.filter_by(username='admin').first(); print('✅ Admin user exists' if admin else '❌ Admin not found')"
```

---

## 📚 Next Steps (Phase 2)

Phase 2 will implement:
- GoldenAPIService full implementation
- CacheService for synchronizing GOLDEN API → local database
- Cache invalidation logic
- Background sync scripts with cron integration

To continue: See [Phase 2 documentation] (coming soon)

---

## 🐛 Troubleshooting

### Database Connection Error
```
psycopg2.OperationalError: could not connect to server
```
**Solution**: Check `DATABASE_URL` in `.env` and ensure PostgreSQL is running.

### Module Import Errors
```
ModuleNotFoundError: No module named 'config'
```
**Solution**: Ensure you're running from the project root directory.

### Superadmin Password
The default password is `change_me_in_production`. Change it immediately in production!

```bash
# To change password:
python -c "
from config.database import db
from models.user import User
from flask import Flask
from config.development import DevelopmentConfig

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db.init_app(app)

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('your-new-password')
    db.session.commit()
    print('Password updated!')
"
```

---

## 📞 Support

For issues or questions about Phase 1:
1. Check the error message carefully
2. Review database connection settings
3. Ensure all dependencies are installed
4. Check `.env` file configuration

---

**Phase 1 Status**: ✅ COMPLETE
**Next Phase**: Phase 2 — Service Layer & Cache Sync
