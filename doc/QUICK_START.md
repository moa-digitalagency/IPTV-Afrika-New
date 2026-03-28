# Quick Start Guide — Mon IPTV Africa Admin Dashboard

## 🚀 Getting Started (5 minutes)

### Prerequisites
- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)
- pip packages (see requirements.txt)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```bash
SUPERADMIN_USERNAME=admin
SUPERADMIN_EMAIL=admin@moniptvafrica.com
SUPERADMIN_PASSWORD=changeme123456
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db  # For development
```

### 3. Initialize Database
```bash
python3 init_db.py
```

This will:
- Create all database tables
- Set up the superadmin user
- Initialize default app settings with GOLDEN API credentials
- Create default Telegram templates

### 4. Start the Application
```bash
python3 app.py
```

Application will be available at: http://localhost:5000

### 5. Login
- **URL:** http://localhost:5000/app/
- **Username:** admin (or your SUPERADMIN_USERNAME)
- **Password:** changeme123456 (or your SUPERADMIN_PASSWORD)
- **First login:** ⚠️ Change your password immediately!

## 📋 Main Features

### Dashboard (`/app/`)
- **Overview Statistics**
  - Total active subscribers
  - Active trial testers
  - Expiring soon (next 7 days)
  - Recently converted

- **Quick Actions**
  - Add new subscriber
  - Convert tester to paid
  - View detailed statistics

### Lines Management (`/app/lines/`)

**Four Views:**
1. **Testers - Active** — Trial subscribers who haven't expired
2. **Testers - Expired** — Trial subscribers past expiration
3. **Subs - Active** — Paid subscribers still active
4. **Subs - Expired** — Paid subscribers past expiration

**Actions per line:**
- View details (username, password, M3U link with options)
- Extend subscription
- Convert tester to paid
- Refund/disable line
- Add notes

### Convert Tester Flow
1. Click "Convert Tester" on any trial subscriber
2. Modal loads real packages from GOLDEN API
3. Packages display with intelligent formatting:
   - "📅 30 Jours" (1-30 days)
   - "📅 3 Mois" (31-364 days)
   - "📅 1.0 Année(s)" (365+ days)
4. Select package duration
5. Click "Convert"
6. Line updated: `is_trial=False`, expiration extended

## 🔄 Package Management

### Automatic Sync
Packages sync automatically from GOLDEN API every time you:
- Open the dashboard
- Access the Lines section
- Click "Refresh Cache" in Settings

### Manual Cache Refresh
```bash
python3 scripts/sync_cache.py
```

Or via dashboard: Settings → GOLDEN API → Refresh Cache

### Current Packages (from GOLDEN API)
```
Trial (5):      1 Month, 72H, 24H, 12H, 6H
Paid (6):       1 Month, 3 Months, 6 Months, 1 Year, 2 Years, 3 Years
```

## 📊 M3U Link Options

When viewing subscriber details, M3U link has options:

**Quality:**
- Auto (default)
- 720p
- 1080p (4K)
- 480p

**Format:**
- Default (M3U)
- HLS (Streaming)
- HTTP (Direct)

Example:
```
Base: http://stream.example.com/user=john&pass=secret
With options: http://stream.example.com/user=john&pass=secret?quality=1080p&format=hls
```

## 🔐 Security Features

✅ **User Authentication**
- Username/password login
- Session-based authentication with Flask-Login
- Password hashing with werkzeug.security

✅ **Permission System**
- Role-based: superadmin, admin, operator
- Resource-based: lines, users, telegram, settings, cache
- Action-based: read, write, delete

✅ **CSRF Protection**
- All forms protected with Flask-WTF CSRF tokens
- API endpoints validate CSRF

✅ **Rate Limiting**
- Login: 5 attempts per minute per IP
- Prevents brute force attacks

✅ **Activity Logging**
- All actions logged to ActivityLog table
- Records: user, action, target, timestamp, IP address
- Useful for auditing and debugging

## 🛠️ Common Tasks

### Add New Subscriber
1. Dashboard → "Add Subscriber" button
2. Enter username, password, full name, email
3. Select package (1 month, 3 months, etc.)
4. Click "Create"
5. Line created in GOLDEN API and synced to local database

### Convert Trial Tester to Paid
1. Lines → Testers (Active)
2. Click "Convert Tester" on the line
3. Select duration/package
4. Click "Convert"
5. Line updated: is_trial becomes false, days extended

### View Detailed Subscriber Info
1. Click on subscriber name in any Lines view
2. View complete details:
   - Username/password
   - M3U streaming link (with quality/format options)
   - Expiration date
   - Package history
   - Refund policies
   - Notes
3. Options to extend, refund, or edit notes

### Check Cache Status
1. Dashboard → "Cache Status" card
2. View:
   - Last sync time
   - Number of packages cached
   - Number of lines cached
   - Sync duration

### Troubleshooting

**Issue:** Login returns "Invalid credentials"
- **Solution:** Check SUPERADMIN_PASSWORD in .env matches what you entered

**Issue:** Packages not loading in Convert modal
- **Solution:** Click "Refresh Cache" in Settings to sync from GOLDEN API

**Issue:** "Permission denied" error
- **Solution:** Ensure you're using the superadmin account
- Check user role in database: `SELECT * FROM users WHERE username='admin'`

**Issue:** GOLDEN API connection error
- **Solution:** Verify API key is correct in Settings
- Test connection: Dashboard → Settings → "Test API Connection"

## 📞 API Endpoints (for developers)

### Public Routes
- `GET /` — Landing page
- `GET /catalog` — Service catalog
- `GET /robots.txt` — SEO robots file
- `GET /sitemap.xml` — SEO sitemap

### Admin Routes (require login)
- `GET /app/` — Dashboard
- `GET /app/lines/testers/active` — Active testers
- `GET /app/lines/testers/expired` — Expired testers
- `GET /app/lines/subs/active` — Active subscribers
- `GET /app/lines/subs/expired` — Expired subscribers

### Internal API (AJAX endpoints, require login)
- `GET /app/api/packages/list` — Get available packages
- `GET /app/api/testers/active` — Get active testers for modal
- `GET /app/api/cache/status` — Cache sync status
- `POST /app/api/cache/refresh` — Trigger cache sync
- `GET /app/api/stats/summary` — Dashboard statistics

### Line Operations
- `POST /app/lines/create` — Create new line
- `GET /app/lines/<id>` — View line details
- `POST /app/lines/<id>/extend` — Extend expiration
- `POST /app/lines/<id>/convert` — Convert trial to paid
- `POST /app/lines/<id>/refund` — Refund and disable

## 📚 Documentation Files

- **GOLDEN_API_INTEGRATION.md** — Complete API integration report
- **SETUP_GOLDEN_API.md** — API configuration details
- **README.md** — Original project documentation

## ✨ Key Features

✅ Dynamic package loading from GOLDEN API
✅ Real-time subscriber management
✅ M3U streaming links with options
✅ Trial-to-paid conversion workflow
✅ Permission-based access control
✅ Activity logging and auditing
✅ Cache synchronization
✅ Responsive dashboard UI
✅ SEO-friendly landing page
✅ Telegram bot integration (optional)

## 🎯 Next Steps

1. **Development Testing**
   - Start the app locally
   - Create test subscribers
   - Test convert tester flow

2. **QA Testing**
   - Test with real GOLDEN API
   - Verify all scenarios work
   - Check edge cases

3. **Production Deployment**
   - Set up PostgreSQL database
   - Configure environment variables
   - Run init_db.py
   - Test all features
   - Set up cron job for cache sync

---

**Version:** 1.0
**Last Updated:** 2026-03-28
**Status:** ✅ Production Ready
