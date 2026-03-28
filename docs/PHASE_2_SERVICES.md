# Phase 2 — Services & Cache Synchronization

## ✅ What Was Completed

Phase 2 implements the entire service layer for GOLDEN API integration and cache management:

### 1. Enhanced GOLDEN API Service
**services/golden_api.py** — Robust wrapper for all GOLDEN API operations
- Error handling with custom `GoldenAPIException`
- HTTP error code translation (401, 403, 404, 429, 5xx)
- Request validation and response parsing
- Methods:
  - `get_packages()` — Fetch available packages
  - `get_all_lines()` — Fetch all lines
  - `get_line(id)` — Get specific line details
  - `create_line(username, password, package_id)` — Create new line
  - `extend_line(id, days)` — Extend expiration
  - `refund_line(id)` — Refund and close line
  - `test_connection()` — Test API connectivity

### 2. Cache Synchronization Service
**services/cache_service.py** — Smart cache sync with logging
- **Full sync strategy**: Sync packages first, then lines (dependencies)
- **Date parsing**: Handles ISO 8601 and YYYY-MM-DD formats
- **Atomic operations**: Uses transactions to ensure data consistency
- **Methods**:
  - `sync_packages()` — Sync all packages from GOLDEN API
  - `sync_lines()` — Sync all lines from GOLDEN API
  - `sync_all()` — Complete synchronization with logging
  - `invalidate_line(golden_id)` — Invalidate specific line cache
  - `invalidate_all_lines()` — Force refresh all lines
  - `get_cache_status()` — Return cache statistics and status

### 3. Statistics & Analytics Service
**services/stats_service.py** — Comprehensive statistics and insights
- Dashboard metrics
- Line expiration analysis
- User distribution
- Activity tracking
- Cache performance monitoring
- **Methods**:
  - `get_dashboard_stats()` — Main KPIs
  - `get_line_stats()` — Expiration timeline, package breakdown
  - `get_activity_stats(days)` — User actions per time period
  - `get_cache_stats()` — Sync performance metrics
  - `get_full_stats()` — Combined all statistics

### 4. Notification Service
**services/notification_service.py** — Line expiry monitoring and messaging
- Track lines expiring within N days (default: 7 days)
- Message template variable substitution
- Statistics about expiring/expired lines
- Template management
- **Methods**:
  - `get_expiring_lines(days)` — Lines expiring soon
  - `get_expired_lines()` — Overdue lines
  - `should_notify_line(line)` — Check if notification needed
  - `format_message(template, line)` — Substitute variables
  - `get_expiry_stats()` — Overall expiry status
  - `get_message_template(slug, lang)` — Get template

### 5. Internal API Endpoints
**routes/api_internal.py** — AJAX endpoints for admin dashboard
```
POST   /app/api/cache/refresh          — Trigger manual cache sync
GET    /app/api/cache/status           — Get cache status
GET    /app/api/stats/summary          — Dashboard statistics
GET    /app/api/stats/full             — Complete analytics
GET    /app/api/api/test               — Test GOLDEN API connection
GET    /app/api/lines/search           — Search & filter lines
```

All endpoints require authentication and permission checks.

### 6. Background Scripts
Four executable cron scripts for automation:

#### sync_cache.py (Run every 15 minutes)
```bash
*/15 * * * * /path/to/sync_cache.py
```
- Syncs all data from GOLDEN API to local database
- Creates CacheSyncLog entry for monitoring
- Exits with status code 0 on success, 1 on failure

#### send_expiry_notifs.py (Run daily at 9 AM)
```bash
0 9 * * * /path/to/send_expiry_notifs.py
```
- Identifies lines expiring within 7 days
- Prepares notifications (Telegram implementation in Phase 6)
- Tracks expiry statistics

#### cleanup_logs.py (Run monthly on 1st at midnight)
```bash
0 0 1 * * /path/to/cleanup_logs.py
```
- Removes activity logs older than 90 days
- Maintains database performance
- Reports cleanup statistics

#### test_api.py (Manual testing)
```bash
python scripts/test_api.py
```
- Validates API credentials are configured
- Tests connectivity to GOLDEN API
- Helps diagnose configuration issues

---

## 🎯 How It Works

### Cache Synchronization Flow

```
┌─────────────────────────────────────────────────────────┐
│         Manual: POST /app/api/cache/refresh             │
│         Automatic: cron */15 * * * *                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
          ┌───────────────────┐
          │  CacheService     │
          │    .sync_all()    │
          └─────────┬─────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   ┌─────────────┐      ┌──────────────┐
   │  Packages   │      │    Lines     │
   │   Sync      │      │    Sync      │
   └──────┬──────┘      └──────┬───────┘
          │                    │
          └─────────┬──────────┘
                    │
        ┌───────────▼──────────┐
        │  PackageCache &      │
        │  LineCache Tables    │
        │  (PostgreSQL)        │
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────┐
        │ CacheSyncLog Entry  │
        │ (success/error/time)│
        └─────────────────────┘
```

### Service Interaction

```
┌──────────────────────────────────────┐
│     Admin Dashboard (Phase 3)        │
└────────────┬─────────────────────────┘
             │
      ┌──────▼────────┐
      │ Internal API  │
      │  (api_bp)     │
      └──┬───────┬───┬┘
         │       │   │
    ┌────▼────┐ │   └──────────────────┐
    │  Cache  │ │                      │
    │ Service │ │                      │
    └────┬────┘ │        ┌─────────────▼──┐
         │      │        │ Stats Service  │
         │      │        └────────────────┘
         │      │
    ┌────▼──────▼─────────────────┐
    │   GOLDEN API Service        │
    │   (exception handling)      │
    └──────────────┬──────────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  GOLDEN API Server  │
        │  (External)         │
        └─────────────────────┘
```

---

## 🚀 Usage Examples

### Triggering Manual Cache Sync
```bash
# Via HTTP from admin dashboard
curl -X POST http://localhost:5000/app/api/cache/refresh \
  -H "Authorization: Bearer <token>"

# Via command line
python scripts/sync_cache.py
```

### Checking Cache Status
```bash
curl http://localhost:5000/app/api/cache/status
```

Response:
```json
{
  "total_lines": 150,
  "total_packages": 8,
  "active_lines": 120,
  "trial_lines": 30,
  "last_sync": "2025-03-28T10:15:00",
  "last_sync_status": "success",
  "last_sync_duration_ms": 2341
}
```

### Getting Dashboard Statistics
```bash
curl http://localhost:5000/app/api/stats/summary
```

Response:
```json
{
  "lines": {
    "total": 150,
    "active": 120,
    "expired": 10,
    "trial": 30,
    "paid": 120
  },
  "users": {
    "total": 5,
    "superadmins": 1,
    "admins": 2,
    "operators": 2
  }
}
```

### Testing API Credentials
```bash
python scripts/test_api.py
```

Output:
```
============================================================
🧪 GOLDEN API Connection Test
============================================================

📋 Checking configuration...
✅ API Key configured: abcd1234...
✅ API URL: https://api.goldentv.com

🔌 Testing connection...
✅ GOLDEN API connection successful
```

### Searching Lines with Filters
```bash
# Search by username/email
curl "http://localhost:5000/app/api/lines/search?q=john&type=active"

# Get expired lines with pagination
curl "http://localhost:5000/app/api/lines/search?type=expired&page=2&per_page=50"
```

---

## ⚙️ Configuration

All services use settings from the database `app_settings` table:

| Key | Default | Purpose |
|-----|---------|---------|
| `golden_api_key` | (empty) | GOLDEN API authentication |
| `golden_api_base_url` | https://api.goldentv.com | API endpoint |
| `cache_ttl_lines` | 900 | Line cache timeout (seconds) |
| `cache_ttl_packages` | 3600 | Package cache timeout (seconds) |

Update via:
```python
from models.settings import AppSetting
from config.database import db

setting = AppSetting.query.filter_by(key='golden_api_key').first()
setting.value = 'your-new-key'
db.session.commit()
```

---

## 🔍 Monitoring & Logging

All sync operations are logged in `cache_sync_logs` table:

| Column | Description |
|--------|-------------|
| `sync_type` | 'lines', 'packages', or 'all' |
| `status` | 'success', 'error', 'pending' |
| `lines_synced` | Count of synced records |
| `error_msg` | Error description if failed |
| `duration_ms` | Execution time in milliseconds |
| `started_at` | Timestamp when sync started |
| `finished_at` | Timestamp when sync completed |

Query recent syncs:
```python
from models.logs import CacheSyncLog
from datetime import datetime, timedelta

recent = CacheSyncLog.query.filter(
    CacheSyncLog.started_at >= datetime.utcnow() - timedelta(days=1)
).order_by(CacheSyncLog.started_at.desc()).all()

for log in recent:
    print(f"{log.sync_type}: {log.status} in {log.duration_ms}ms")
```

---

## 🐛 Error Handling

Services use custom exceptions for graceful error handling:

```python
from services.golden_api import GoldenAPIException

try:
    packages = GoldenAPIService.get_packages()
except GoldenAPIException as e:
    # Handle API error (401, 403, 404, 429, 5xx, timeout, etc.)
    print(f"API Error: {e}")
```

All errors are caught and logged:
- **Invalid credentials** → GoldenAPIException("Unauthorized: Invalid API key")
- **Network timeout** → GoldenAPIException("Request timeout")
- **Connection refused** → GoldenAPIException("Connection error: Cannot reach GOLDEN API")
- **Invalid JSON** → GoldenAPIException("Invalid JSON response")

---

## 📊 Analytics Examples

### Check expiring lines
```python
from services.notification_service import NotificationService

stats = NotificationService.get_expiry_stats()
print(f"Total active: {stats['total_active']}")
print(f"Expiring soon: {stats['expiring_soon']}")
print(f"Healthy: {stats['healthy']}")
```

### Get activity by user
```python
from services.stats_service import StatsService

stats = StatsService.get_activity_stats(days=30)
for action in stats['by_action']:
    print(f"{action['action']}: {action['count']}")
```

### Cache performance
```python
from services.stats_service import StatsService

stats = StatsService.get_cache_stats()
print(f"Average sync time: {stats['average_duration_ms']}ms")
print(f"Recent syncs: {stats['recent_syncs']}")
print(f"Success rate: {stats['successful']}/{stats['recent_syncs']}")
```

---

## 🔐 Security

- **API Credentials**: Stored encrypted in database, never logged
- **Rate Limiting**: Phase 9 will add request throttling
- **Audit Logging**: All operations logged with user ID and IP
- **Error Messages**: Safe error messages (no credential leaks)

---

## 📈 Performance Tips

1. **Cron Scheduling**: Run sync every 15 minutes (optimal balance)
2. **Batch Processing**: Services handle large datasets efficiently
3. **Database Indexes**: Queries use indexes on `is_trial`, `exp_date`, `enabled`
4. **Connection Pooling**: SQLAlchemy manages connection pool
5. **Timeout**: 10-second timeout prevents hanging requests

---

## 🔄 Next Steps (Phase 3)

Phase 3 will implement:
- Admin dashboard layout with sidebar navigation
- Real-time cache status widget
- Integration of stats services with UI
- Enhanced dashboard with analytics

---

## 📚 Related Documentation

- [Phase 1 Setup](PHASE_1_SETUP.md)
- [GOLDEN API Docs](https://api.goldentv.com/docs) (external)

---

**Phase 2 Status**: ✅ COMPLETE
**Next Phase**: Phase 3 — Admin Dashboard & Layout
