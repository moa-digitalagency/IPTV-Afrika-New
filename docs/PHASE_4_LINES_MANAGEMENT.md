# Phase 4 — Gestion des Lignes (Lines Management)

**Status**: ✅ Completed
**Date**: 2026-03-28

---

## Overview

Phase 4 implements complete CRUD operations for M3U subscription management. Users can now:
- **View** active/expired testers and subscribers
- **Create** new subscriptions with package selection
- **Extend** expiration dates for active lines
- **Refund** and deactivate expired or problematic lines
- **Toggle** line status (enable/disable)
- **Search** subscriptions by username with client-side filtering
- **Paginate** through large datasets (20 items per page)

All operations integrate with the GOLDEN API backend and maintain activity logs.

---

## Files Created

### Routes — `routes/lines.py`
8 endpoints handling subscription management:

| Route | Method | Purpose | Permission |
|-------|--------|---------|-----------|
| `/app/lines/testers/active` | GET | List active trial lines | `lines.testers:read` |
| `/app/lines/testers/expired` | GET | List expired trial lines | `lines.testers:read` |
| `/app/lines/subs/active` | GET | List active paid subscriptions | `lines.subscribers:read` |
| `/app/lines/subs/expired` | GET | List expired paid subscriptions | `lines.subscribers:read` |
| `/app/lines/<golden_id>` | GET | View line details | `lines:read` |
| `/app/lines/create` | GET, POST | Create new line | `lines.create:write` |
| `/app/lines/<golden_id>/extend` | POST | Extend expiration | `lines.extend:write` |
| `/app/lines/<golden_id>/refund` | POST | Refund and deactivate | `lines.refund:write` |
| `/app/lines/<golden_id>/toggle` | POST | Enable/disable line | `lines.toggle:write` |

#### Key Features
- `@login_required` protects all routes
- `@require_permission` enforces granular access control
- Activity logging via `log_action()` helper
- Cache invalidation after write operations
- Proper error handling with user-facing messages
- JSON responses for AJAX operations

### Templates

#### `templates/app/lines/testers_active.html`
Displays active trial subscriptions with:
- Search input for username filtering
- Stats card showing total count
- Table: Username | Full Name | Email | Package | Days Remaining | Connections | Actions
- Extend modal for adding days to subscription
- Pagination (5-10 page buttons)
- Empty state when no active testers

#### `templates/app/lines/testers_expired.html`
Displays expired trial subscriptions:
- Similar layout to active testers
- Shows expiration date and days elapsed
- Refund modal for removing/deactivating lines
- Color-coded danger badge for package display

#### `templates/app/lines/subs_active.html`
Displays active paid subscriptions:
- Full name and email columns
- Color-coded expiration status:
  - 🟢 Green: >30 days remaining
  - 🟡 Gold: 7-30 days remaining
  - 🟠 Orange: ≤7 days remaining
- Same extend/refund functionality as testers

#### `templates/app/lines/subs_expired.html`
Displays expired paid subscriptions:
- Mirrors testers_expired.html
- Branded for subscriber context
- Refund action for cleanup

#### `templates/app/lines/create.html`
Form for creating new subscriptions:
- Text input: Username (required)
- Password input: Password (required, ≥8 chars)
- Select dropdown: Package (required, populated from DB)
- Text input: Full Name (optional)
- Email input: Email (optional)
- Submit/Cancel buttons
- Info panel explaining sync behavior

#### `templates/app/lines/detail.html`
Comprehensive single-line detail view:

**Sections:**
1. **Informations Principales** (Main Info)
   - Username (monospace, highlighted)
   - Password (masked, toggle visibility)
   - Full Name, Email, Phone
   - Package badge, Connections max

2. **Statut et Expiration**
   - Type: Trial (🧪) or Subscriber (💳)
   - Status: Active (🟢) or Inactive (🔴)
   - Expiration date
   - Days remaining/elapsed (color-coded)

3. **Informations Additionnelles**
   - Notes (if present)
   - M3U DNS link (copyable)
   - Creation and cache timestamps

4. **Actions**
   - ⏱️ Extend: Add days to active subscriptions
   - 🔴/🟢 Toggle: Enable/disable line
   - 🗑️ Refund: Deactivate and close

**Modals:**
- Extend Modal: Date picker (1-365 days, default 30)
- Refund Modal: Confirmation with warning text

---

## JavaScript Features

### Client-Side Search
All list templates include live search filtering:
```javascript
document.getElementById('searchInput').addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    document.querySelectorAll('table tbody tr').forEach(row => {
        const username = row.querySelector('td').textContent.toLowerCase();
        row.style.display = username.includes(term) ? '' : 'none';
    });
});
```

### Modal Management
Safe DOM manipulation for modals:
- `extendLine(golden_id, username)`: Opens extend modal
- `refundLine(golden_id, username)`: Opens refund modal
- Click-outside-to-close for both modals
- Form reset on modal close

### AJAX Operations
Modal forms submit via fetch with:
- CSRF token extraction from meta tag
- Form data serialization
- JSON response handling
- Auto-reload on success
- User alerts for success/error messages

---

## Data Integration

### Database Tables Used
- **line_cache**: Primary source for all line data
  - Columns: golden_id, username, password, full_name, email, phone, package_id, package_name, is_trial, exp_date, enabled, max_connections, note, dns_link, created_at, cached_at

### GOLDEN API Integration
Routes call `GoldenAPIService` methods:
- `create_line(username, password, package_id)` → stores result ID
- `extend_line(golden_id, days)` → returns updated exp_date
- `refund_line(golden_id)` → marks as refunded
- Error handling includes proper HTTP status codes

### Cache Management
- `CacheService.invalidate_line(golden_id)` called after extend/refund
- `CacheService.invalidate_all_lines()` called after create
- Ensures DB reflects API state on next sync cycle

---

## Accessibility & UX

### Color Coding
- **Gold** (#D4A574): Trial/test items, highlights
- **Green** (#27AE60): Active, healthy
- **Orange** (#E67E22): Warning, expiring soon
- **Red** (#E74C3C): Danger, expired, refund actions

### Responsive Design
- Table headers stack on mobile (<480px)
- Sidebar collapse on small devices
- Modal width: 90% on mobile, max 400px on desktop
- Flexbox layouts adapt to screen size

### Accessibility
- Semantic HTML (forms, tables, sections)
- ARIA-ready button/link structure
- Clear heading hierarchy
- Color + icons (not color alone)
- Focus states for form inputs

---

## Error Handling

### Client Errors
- Required field validation (HTML5)
- Username/package selection enforcement
- Password minimum length hint

### Server Errors
- GOLDEN API failures return 400 with message
- Missing lines return 404 with flash message
- Permission denials caught by `@require_permission`
- Activity logged with full request context

### User Feedback
- Success: Toast alerts + page reload
- Errors: Toast alerts + form remains visible
- Flash messages in page header
- Field-level hints on form inputs

---

## Template Context Variables

All line templates receive:

| Variable | Type | Purpose |
|----------|------|---------|
| `lines` | List[LineCache] | Paginated line objects |
| `total` | int | Total lines in database |
| `pages` | int | Total page count |
| `current_page` | int | Current page number |
| `per_page` | int | Items per page (20) |
| `now` | function | `datetime.utcnow` for expiry calculations |

Detail template additionally receives:
| `line` | LineCache | Single line object |
| `days_left` | int | Result of `days_remaining(line.exp_date)` |

---

## Testing Checklist

- [x] Create route generates line in GOLDEN API
- [x] Extend modal calculates correct expiration
- [x] Refund route marks line as disabled
- [x] Toggle enables/disables without affecting expiry
- [x] Search filters table without page reload
- [x] Pagination shows/hides correctly
- [x] Detail page displays all fields (including masked password)
- [x] Modal forms submit via AJAX with CSRF token
- [x] Permission decorators prevent unauthorized access
- [x] Activity logs record all user actions

---

## Security Notes

1. **CSRF Protection**: All POST requests require meta[name="csrf-token"]
2. **Password Masking**: Detail page shows masked password with toggle
3. **Permission Checking**: Each resource action requires explicit permission
4. **Activity Logging**: All mutations logged with user IP, timestamp, detail JSON
5. **SQL Injection**: SQLAlchemy ORM prevents injection
6. **XSS Prevention**: Jinja2 auto-escapes all user input

---

## Sidebar Navigation

Updated `/templates/app/base.html` with real route links:
- ✅ Testeurs Actifs → `lines.testers_active`
- ❌ Testeurs Expirés → `lines.testers_expired`
- 🎬 Abonnés Actifs → `lines.subs_active`
- ⏰ Abonnés Expirés → `lines.subs_expired`
- ➕ Créer une Ligne → `lines.create_line`

---

## Next Phase (Phase 5)

Statistics and Chart.js integration:
- Dashboard stats cards
- Expiry distribution chart
- Growth trends
- User activity timeline
- Real-time cache status monitoring

See `PHASE_5_STATISTICS.md` for details.
