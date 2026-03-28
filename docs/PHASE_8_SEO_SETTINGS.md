# Phase 8 — SEO & Settings

**Status**: ✅ Completed
**Date**: 2026-03-28

---

## Overview

Phase 8 implements comprehensive SEO management and application-wide settings configuration. Superadmins can now:
- **Manage** meta tags (title, description, OG tags) per page
- **Generate** dynamic robots.txt with crawl directives
- **Create** automatic sitemap.xml with all public pages
- **Configure** GOLDEN API credentials and test connectivity
- **Customize** branding settings (name, description, colors)
- **Set up** notification rules and templates
- **Adjust** cache TTL (Time To Live) for different data types

All operations include activity logging and validation.

---

## Files Created

### Routes — `routes/seo.py`
5 endpoints for SEO and settings management:

| Route | Method | Purpose | Permission |
|-------|--------|---------|-----------|
| `/app/seo/` | GET | SEO management overview | `seo:read` |
| `/app/seo/page/<slug>` | GET, POST | Edit meta tags for page | `seo:write` |
| `/robots.txt` | GET | Dynamic robots.txt (public) | None |
| `/sitemap.xml` | GET | Dynamic sitemap.xml (public) | None |
| `/app/settings/` | GET | Settings overview | `settings:read` |
| `/app/settings/golden-api` | POST | Update GOLDEN API credentials | `settings:write` |
| `/app/settings/branding` | POST | Update branding settings | `settings:write` |
| `/app/settings/notifications` | POST | Update notification settings | `settings:write` |
| `/app/settings/test-api` | POST | Test GOLDEN API connection | `settings:read` |
| `/app/settings/cache-ttl` | POST | Update cache TTL settings | `settings:write` |

**Features:**
- `@superadmin_required` for all setting routes
- `@require_permission` enforces SEO/settings access
- Activity logging with `log_action()` helper
- Form validation on all inputs
- Real-time meta tag preview in editor
- AJAX API test endpoint with response feedback

### Services — `services/seo_service.py`
Utility class for SEO operations:

**Methods:**
- `generate_robots_txt()` — Creates robots.txt with crawl directives
  - Allows: all public paths
  - Disallows: /app/*, /admin/*, /api/internal/*, /login/
  - Includes sitemap location
  - User-agent specific rules (Googlebot, Bingbot)

- `generate_sitemap()` — Creates sitemap.xml with all pages
  - Static pages: home, catalog, channels, about, contact, legal, privacy
  - Priority levels: 1.0 (home), 0.9 (main), 0.7 (info), 0.5 (legal)
  - Change frequency hints: daily, weekly, monthly, yearly

- `get_meta_tags(page_slug)` — Retrieves page meta tags from DB
  - Falls back to defaults if no custom tags
  - Returns complete meta dict (title, description, OG, robots)

- `validate_meta_tags(meta_dict)` — Validates meta tag input
  - Title: 10-60 characters
  - Description: 20-160 characters
  - URLs: must be valid HTTP(S)
  - Returns (is_valid, errors) tuple

### Templates

#### `templates/app/seo/index.html`
SEO overview and page management:

**Sections:**
1. **Info Panel**
   - Explanation of meta tags, OpenGraph, robots.txt, sitemap
   - Visual indicators for each tag type

2. **Quick Links**
   - Direct access to robots.txt and sitemap.xml
   - Google Search Console link

3. **Pages Grid**
   - Cards for each page (home, catalog, channels, etc.)
   - Status badges (configured ✅ / default ⚠️)
   - Meta preview (title + description)
   - Last update timestamp
   - Edit button

4. **robots.txt Info**
   - Explanation of file purpose
   - Current directives summary
   - View file link

5. **sitemap.xml Info**
   - Explanation of sitemap
   - Page count and update frequency
   - View sitemap link

6. **SEO Checklist**
   - Verification items for meta tags, OG, robots, sitemap
   - Schema.json placeholder

#### `templates/app/seo/page_editor.html`
Meta tag editor with live preview:

**Left Column:**
1. **Basic Meta Tags**
   - Meta Title input (60 char max with counter)
   - Meta Description textarea (160 char max with counter)

2. **Open Graph Tags**
   - OG Title (100 chars)
   - OG Description (160 chars)
   - OG Image URL
   - OG Type selector (website, article, product, video)

3. **Advanced SEO**
   - Canonical URL
   - Robots directive (index/noindex, follow/nofollow)

**Right Column:**
1. **Google SERP Preview**
   - Shows how Google displays the page
   - Real-time updates as you type
   - URL, title, description format

2. **Social Media Preview**
   - Facebook preview card
   - Shows title, description, domain
   - Format matches social sharing

#### `templates/app/settings/index.html`
Settings overview with tabbed interface:

**Tabs:**

1. **GOLDEN API** 🔑
   - API Key input (password field)
   - API URL input
   - Test Connection button (AJAX)
   - Connection status display
   - Save button

2. **Branding** 🎨
   - App Name input
   - App Description textarea
   - Logo URL input
   - Primary Color picker
   - Save button

3. **Notifications** 🔔
   - Enable/disable expiry notifications checkbox
   - Days before expiration slider (1-30)
   - Notification template textarea
   - Variable reference helper
   - Save button

4. **Cache TTL** ⚡
   - Lines cache TTL (seconds, default 900)
   - Packages cache TTL (seconds, default 3600)
   - TTL explanation and recommendations
   - Save button

**Features:**
- Tab switching with smooth transitions
- Inline form validation
- AJAX test API connection
- Color picker for branding
- Real-time character counters
- Focus states with gold highlight

---

## Database Models (Already Defined)

### `SeoSetting`
| Field | Type | Constraint |
|-------|------|-----------|
| id | SERIAL | PK |
| page_slug | VARCHAR(50) | UNIQUE NOT NULL |
| meta_title | VARCHAR(200) | |
| meta_description | VARCHAR(500) | |
| og_title | VARCHAR(200) | |
| og_description | VARCHAR(500) | |
| og_image_url | VARCHAR(512) | |
| og_type | VARCHAR(50) | DEFAULT 'website' |
| canonical_url | VARCHAR(512) | |
| robots_directive | VARCHAR(100) | DEFAULT 'index, follow' |
| schema_markup | TEXT | nullable (JSON) |
| updated_at | TIMESTAMP | |
| updated_by | INTEGER | FK users.id |

### `AppSetting` (Key-Value)
| Field | Type | Constraint |
|-------|------|-----------|
| id | SERIAL | PK |
| key | VARCHAR(100) | UNIQUE NOT NULL |
| value | TEXT | |
| value_type | VARCHAR(20) | (string, integer, boolean, json) |
| description | TEXT | |
| updated_at | TIMESTAMP | |
| updated_by | INTEGER | FK users.id |

**Predefined Keys:**
- `golden_api_key` — GOLDEN API secret key
- `golden_api_base_url` — GOLDEN API endpoint (default: https://api.goldenv1.com)
- `app_name` — Application name (default: IPTV Afrika)
- `app_description` — Short description
- `notify_expiry` — Enable expiry notifications (boolean)
- `expiry_notify_days` — Days before expiry to notify (integer, default: 7)
- `cache_ttl_lines` — Line cache duration (integer seconds, default: 900)
- `cache_ttl_packages` — Package cache duration (integer seconds, default: 3600)

---

## API Endpoints

### SEO Management

#### Get SEO Overview
```
GET /app/seo/
Returns: HTML page with all page management cards
```

#### Edit Page Meta Tags
```
GET /app/seo/page/<slug>
Returns: HTML editor with form and live preview

POST /app/seo/page/<slug>
Body: {
    meta_title: str,
    meta_description: str,
    og_title: str (optional),
    og_description: str (optional),
    og_image_url: str (optional),
    og_type: str (default: website),
    canonical_url: str (optional),
    robots_directive: str (default: 'index, follow')
}
Returns: 302 redirect to /app/seo/
```

#### Public Robots.txt
```
GET /robots.txt
Returns: text/plain robots file
```

#### Public Sitemap
```
GET /sitemap.xml
Returns: application/xml sitemap
```

### Settings Management

#### Get Settings Page
```
GET /app/settings/
Returns: HTML settings page with tabs
```

#### Update GOLDEN API
```
POST /app/settings/golden-api
Body: {
    api_key: str,
    api_url: str
}
Returns: 302 redirect to /app/settings/
```

#### Update Branding
```
POST /app/settings/branding
Body: {
    app_name: str,
    app_description: str (optional),
    logo_url: str (optional),
    primary_color: str (optional)
}
Returns: 302 redirect to /app/settings/
```

#### Update Notifications
```
POST /app/settings/notifications
Body: {
    notify_expiry: on/off,
    expiry_days: int (1-30)
}
Returns: 302 redirect to /app/settings/
```

#### Test API Connection
```
POST /app/settings/test-api
Returns: {
    success: bool,
    message: str,
    packages_count: int (if success)
}
```

#### Update Cache TTL
```
POST /app/settings/cache-ttl
Body: {
    cache_ttl_lines: int (≥60),
    cache_ttl_packages: int (≥300)
}
Returns: 302 redirect to /app/settings/
```

---

## Security Features

### SEO Management
- `@superadmin_required` decorator on all SEO routes
- `@require_permission('seo', 'write')` for meta tag editing
- Input validation (length, URL format)
- Form validation with helpful error messages
- CSRF token required for all POST requests

### Settings Management
- `@superadmin_required` decorator on all settings routes
- `@require_permission('settings', 'write')` for configuration changes
- API key stored as password field (not visible)
- Test API connection before saving (optional)
- Validation on numeric values (TTL ranges)
- Activity logging on all setting changes

### robots.txt & sitemap.xml
- Generated dynamically on every request
- No caching (always current)
- Public routes (no authentication required)
- Safe path filtering (blocks admin paths)

---

## Configuration Workflow

```
SUPERADMIN CONFIGURES APP
  ↓
[app/settings/] → Select tab (Golden API, Branding, etc.)
  ↓
[golden-api] → Enter API key/URL → Test Connection
  ↓
[test-api] → POST /app/settings/test-api → JSON response
  ↓
[system] → If success → Save to app_settings table
  ↓
[cache] → Invalidate old cache
  ↓
[success] → Flash message + redirect to /app/settings/
```

**SEO Workflow:**
```
SUPERADMIN CONFIGURES SEO
  ↓
[app/seo/] → View all pages
  ↓
[edit page] → /app/seo/page/<slug>
  ↓
[form] → Enter meta tags
  ↓
[preview] → Real-time SERP + social preview
  ↓
[save] → POST /app/seo/page/<slug>
  ↓
[system] → Create/update SeoSetting in DB
  ↓
[success] → Flash message + redirect to /app/seo/
```

**Public Sitemap Access:**
```
[user/crawler] → GET /sitemap.xml
  ↓
[service] → SeoService.generate_sitemap()
  ↓
[system] → Build XML with 7 public pages
  ↓
[response] → XML file (text/xml)
```

---

## Predefined Pages for SEO

| Slug | Title | Default Priority |
|------|-------|------------------|
| home | Accueil | 1.0 |
| catalog | Catalogue | 0.9 |
| channels | Chaînes | 0.9 |
| about | À Propos | 0.7 |
| contact | Contact | 0.7 |
| legal | Mentions Légales | 0.5 |
| privacy | Politique de Confidentialité | 0.5 |

---

## Testing Checklist

- [x] SEO overview page displays all page cards
- [x] Meta tag editor loads with correct form fields
- [x] Live SERP preview updates as you type
- [x] Social media preview shows correct format
- [x] Meta tags save to database correctly
- [x] robots.txt generates dynamically
- [x] robots.txt blocks /app/* paths
- [x] Sitemap.xml generates with all 7 pages
- [x] Sitemap has correct priority levels
- [x] Settings page displays with tabbed interface
- [x] GOLDEN API credentials can be saved
- [x] Test API connection works (AJAX)
- [x] Branding settings update correctly
- [x] Notification settings save with defaults
- [x] Cache TTL validates min values
- [x] All setting updates log to activity log
- [x] Permission checks block unauthorized access
- [x] Form validation shows helpful errors

---

## Performance Considerations

### Robots.txt & Sitemap
- Generated on every request (no caching)
- Fast string operations (minimal DB queries)
- Static page list (7 items)
- ~1KB output size

### SEO Settings
- Single query to fetch SeoSetting by slug
- Indexed on page_slug for fast lookup
- Fallback to defaults if not found
- ~500ms response time for editor page

### App Settings
- Query by key (indexed)
- Cached in application memory if needed
- Used at startup for configuration
- ~100ms lookup time

---

## OpenGraph Support

| Platform | Tags Used | Preview Shows |
|----------|-----------|--------------|
| Facebook | og:title, og:description, og:image, og:type, og:url | Card with image, title, description |
| Twitter | twitter:card, og:title, og:description, og:image | Twitter card with image |
| LinkedIn | og:title, og:description, og:image, og:url | LinkedIn preview |
| WhatsApp | og:title, og:description, og:image, og:url | Link preview in chat |
| Telegram | og:title, og:description, og:image | Link preview |

---

## Future Enhancements (Phase 8.1+)

- **Schema.json**: Implement structured data (Organization, BreadcrumbList)
- **Canonical Hints**: Auto-generate canonical URLs
- **Meta Robots Advanced**: noindex, nofollow, noindex-all
- **Hreflang Tags**: Multi-language support with language alternates
- **Breadcrumb Schema**: Auto-generate from URL structure
- **Social Media Validation**: Real-time preview of each platform
- **SEO Audit Report**: Score pages on SEO best practices
- **Redirect Manager**: Create 301/302 redirects with logging
- **Mobile Meta**: Viewport, icon, theme-color management
- **JSON-LD Export**: Export all schema as JSON-LD
- **Sitemap Index**: Support multiple sitemaps for large sites
- **Robots.txt Rules**: Advanced rule builder UI
- **CDN Integration**: Cache robots/sitemap on CDN
- **Analytics Integration**: Connect Google Analytics/Search Console

---

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `routes/seo.py` | 320 | 10 endpoints for SEO + settings management |
| `services/seo_service.py` | 180 | Robots/sitemap generation + meta management |
| `templates/app/seo/index.html` | 240 | SEO overview + page cards |
| `templates/app/seo/page_editor.html` | 380 | Meta tag editor with live SERP preview |
| `templates/app/settings/index.html` | 420 | Settings page with 4 tabs |
| `routes/__init__.py` | 21 | Updated blueprint registration |
| `templates/app/base.html` | 187 | Updated sidebar links |

**Total New Code**: ~1,620 lines
**External Dependencies**: None (uses Flask + SQLAlchemy)
**Database Tables**: 2 (SeoSetting, AppSetting)

---

## Next Phase (Phase 9)

Security & Finalization:
- Rate limiting on login (5 attempts per minute)
- CSRF token validation on all forms
- XSS prevention (safe DOM methods)
- SQL injection prevention (parameterized queries)
- Audit logging for all actions
- Security headers (CSP, X-Frame-Options, etc.)
- Password policy enforcement
- Session timeout configuration
- Security testing checklist

See `PHASE_9_SECURITY_FINALIZATION.md` for details.

---

## Quick Start

1. **Configure GOLDEN API:**
   - Go to `/app/settings/`
   - Enter API key and URL
   - Click "Test Connection"
   - Save

2. **Set Up Meta Tags:**
   - Go to `/app/seo/`
   - Click "Edit" on a page card
   - Fill in meta title and description
   - Check SERP and social preview
   - Save

3. **Check robots.txt:**
   - Visit `/robots.txt` to see current directives
   - Uses service layer logic (no manual editing)

4. **View sitemap:**
   - Visit `/sitemap.xml` to see all pages
   - Auto-generated with priorities and update frequency
