# Phase 5 — Statistiques + Chart.js

**Status**: ✅ Completed
**Date**: 2026-03-28

---

## Overview

Phase 5 implements a comprehensive statistics dashboard with real-time data visualization using Chart.js. Admins can now:
- View 6 key metrics (total, active, expiring soon, expired, testers, paid)
- See expiry distribution across subscription lifecycle
- Compare trial vs paid subscription breakdown
- Track 30-day activity timeline
- Analyze package distribution by popularity
- Monitor cache synchronization status
- Export reports (Phase 5.2)

All charts auto-refresh every 5 minutes with AJAX endpoints.

---

## Files Created

### Routes — `routes/stats.py`
5 endpoints providing statistics and chart data:

| Route | Method | Purpose |
|-------|--------|---------|
| `/app/stats/` | GET | Statistics dashboard page |
| `/app/stats/api/summary` | GET | Summary stats JSON |
| `/app/stats/api/charts/expiry` | GET | Expiry distribution |
| `/app/stats/api/charts/trial-vs-paid` | GET | Trial/paid breakdown |
| `/app/stats/api/charts/activity` | GET | 30-day activity timeline |
| `/app/stats/api/charts/packages` | GET | Package popularity |

#### Key Features
- `@login_required` protects all routes
- `@require_permission('stats', 'read')` enforces access control
- Proper database aggregation using SQLAlchemy
- JSON responses for AJAX consumption
- Error handling with 500 status on exceptions
- Lightweight queries with `.scalar()` and `func.count()`

### Template — `templates/app/stats/index.html`
Comprehensive statistics dashboard:

**Sections:**

1. **Key Metrics Grid** (6 cards)
   - 📺 Total Lines (all, enabled/disabled)
   - 🟢 Active Lines (not expired)
   - ⚠️ Expiration Close (< 7 days)
   - ❌ Expired Lines (overdue)
   - 🧪 Testers (is_trial = True)
   - 💳 Paid (is_trial = False)

2. **Expiry Distribution Chart** (Doughnut)
   - Color zones: Expired (red), <7d (orange), 7-30d (gold), >30d (green)
   - Shows lifecycle distribution at a glance

3. **Trial vs Paid Chart** (Horizontal Bar)
   - 4 bars: Active testers, Expired testers, Active paid, Expired paid
   - Quick comparison of subscription types

4. **Activity Timeline** (Line Chart)
   - 30-day activity history
   - X-axis: Dates (DD/MM format)
   - Y-axis: Number of daily actions
   - Filled area under curve

5. **Package Distribution** (Bar Chart)
   - Top 10 packages by line count
   - Color-coded bars
   - Horizontal layout for readability

6. **Cache Status** (Table)
   - Last sync timestamp
   - Lines in cache count
   - Packages in cache count
   - Cache age indicator

7. **Export Data** (Button)
   - Placeholder for CSV export (Phase 5.2)
   - Downloads complete report

**Styling:**
- Dark luxury theme (matches admin design)
- Responsive grid (auto-fit, minmax 500px)
- Smooth Chart.js animations
- Color-coded by severity/type
- Mobile-responsive layout

### Updated Files

**`routes/__init__.py`**
- Registered `stats_bp` blueprint
- Stats accessible via `/app/stats/`

**`templates/app/base.html`**
- Updated sidebar "Statistiques" link
- Points to `url_for('stats.index')`

---

## Chart.js Implementation

### Chart Types Used

| Chart | Type | Interaction |
|-------|------|------------|
| Expiry Distribution | Doughnut | Click legend to toggle segments |
| Trial vs Paid | Bar (horizontal) | Hover shows values |
| Activity | Line | Point hover, crosshair |
| Packages | Bar (vertical) | Hover shows exact counts |

### Chart Configuration
All charts share common settings:
```javascript
{
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: {
            labels: {
                color: 'var(--text-primary)',
                font: { family: "'Montserrat', sans-serif" }
            }
        }
    },
    scales: {
        x/y: {
            ticks: { color: 'var(--text-muted)' },
            grid: { color: 'var(--bg-elevated)' }
        }
    }
}
```

### Auto-Refresh Behavior
- Initial load: `DOMContentLoaded` event
- Refresh interval: 5 minutes (300,000 ms)
- Parallel loading: `Promise.all()` for 4 chart endpoints
- Non-blocking: Promises resolve independently
- Chart destruction before redraw to prevent memory leaks

### Color Scheme
- Expiry: Red (#E74C3C), Orange (#F39C12), Gold (#D4A574), Green (#27AE60)
- Activity: Gold (#D4A574) line with 10% fill opacity
- Packages: 10-color palette for variety
- Axes: Muted text on elevated background

---

## Data Aggregation Queries

### Summary Stats (get_dashboard_stats)
From `StatsService`:
```python
{
    'total_lines': count all enabled lines,
    'active_lines': where exp_date > now,
    'expired_lines': where exp_date <= now,
    'trial_lines': where is_trial = True,
    'paid_lines': where is_trial = False,
    'expiring_soon': where exp_date 0-7 days,
    'last_sync': max(cached_at),
    'cached_lines': count all in cache,
    'cached_packages': count all packages,
    'cache_age': minutes since last update
}
```

### Expiry Distribution
Four ranges:
- **Expired**: `exp_date < now` (enabled)
- **<7 days**: `now <= exp_date < now + 7d` (enabled)
- **7-30 days**: `now + 7d <= exp_date < now + 30d` (enabled)
- **>30 days**: `exp_date >= now + 30d` (enabled)

### Trial vs Paid
2x2 matrix:
- Testers active/expired
- Paid active/expired
- Counts from `is_trial` + `exp_date` filters

### Activity Timeline
Last 30 days with daily granularity:
```sql
SELECT DATE(created_at), COUNT(*)
FROM activity_log
WHERE created_at >= NOW() - 30 days
GROUP BY DATE(created_at)
ORDER BY date
```

### Package Distribution
Top 10 packages by line count:
```sql
SELECT package_name, COUNT(*)
FROM line_cache
WHERE enabled = True
GROUP BY package_name
ORDER BY COUNT(*) DESC
LIMIT 10
```

---

## API Endpoints (AJAX)

### `/app/stats/api/summary`
Returns dashboard metrics:
```json
{
    "total_lines": 245,
    "active_lines": 198,
    "expired_lines": 47,
    "trial_lines": 80,
    "paid_lines": 165,
    "expiring_soon": 12,
    "last_sync": "2026-03-28T15:30:00",
    "cached_lines": 245,
    "cached_packages": 15,
    "cache_age": "2 minutes"
}
```

### `/app/stats/api/charts/expiry`
```json
{
    "labels": ["Expiré", "Expiration < 7j", "Expiration 7-30j", "Actif > 30j"],
    "data": [47, 12, 25, 161],
    "colors": ["#E74C3C", "#F39C12", "#D4A574", "#27AE60"]
}
```

### `/app/stats/api/charts/trial-vs-paid`
```json
{
    "labels": ["Testeurs Actifs", "Testeurs Expirés", "Abonnés Actifs", "Abonnés Expirés"],
    "data": [65, 15, 133, 32],
    "colors": ["#D4A574", "#E74C3C", "#27AE60", "#95A5A6"]
}
```

### `/app/stats/api/charts/activity`
```json
{
    "labels": ["28/02", "01/03", "02/03", ...],
    "data": [5, 12, 8, 15, ...],
    "color": "#D4A574"
}
```

### `/app/stats/api/charts/packages`
```json
{
    "labels": ["Premium 4K", "Standard HD", "Basic SD", ...],
    "data": [85, 72, 45, ...],
    "colors": ["#D4A574", "#E67E22", "#C1440E", ...]
}
```

---

## Performance Considerations

### Database Optimization
- Use `.scalar()` for single aggregates (faster than `.all()`)
- Use `func.count()` for counting (avoids loading data)
- Filter early with `.filter()` before aggregation
- Group by on indexed columns (`is_trial`, `exp_date`, `package_name`)

### Chart.js Optimization
- Destroy old chart instances before redraw
- Use `maintainAspectRatio: true` to avoid layout shift
- Lazy-load Chart.js from CDN
- Parallel load all 4 chart data with `Promise.all()`

### Caching Strategy
- Client-side: 5-minute refresh interval
- Server-side: line_cache synced every 15 minutes
- Cache miss = slow query, but acceptable for dashboards

---

## Error Handling

### Server Errors
- Try-except wraps all aggregation queries
- Returns `{'error': str(e)}` with 500 status
- Template shows error alert if data load fails

### Missing Data
- Default values: 0 for counts, "-" for strings
- Safe JSON fallbacks: `data.labels || []`
- Empty charts gracefully show "No data"

### Browser Compatibility
- Chart.js 3.9.1 from CDN (covers 98%+ browsers)
- Promise.all() supported in all modern browsers
- Fallback: static text if Chart.js fails to load

---

## Mobile Responsiveness

### Breakpoints
- Desktop: `grid-template-columns: repeat(auto-fit, minmax(500px, 1fr))`
- Tablet: 2 columns on 1024px+, 1 column below
- Mobile: Charts stack vertically, full width

### Stat Cards
- 6 cards in auto-fit grid
- Min-width: 200px (adapts to small screens)
- Touch-friendly: Large tap targets

### Charts
- Canvas elements responsive via Chart.js
- Labels rotate/hide on small screens
- Legend moves bottom on mobile

---

## Security Notes

1. **Permission Control**: `@require_permission('stats', 'read')`
2. **Data Privacy**: Aggregates only, no user PII exposed
3. **SQL Injection**: SQLAlchemy ORM prevents injection
4. **XSS Prevention**: Chart.js sanitizes data, Jinja2 auto-escapes labels

---

## Future Enhancements (Phase 5.2+)

- **CSV Export**: `/app/stats/api/export` endpoint with file download
- **Date Range Filter**: Statistics for custom periods
- **Comparative Analysis**: Month-over-month, year-over-year
- **Forecasting**: Predicted expiries in next 30/60/90 days
- **Custom Dashboards**: User-configurable metric cards
- **Real-time WebSocket**: Live metric updates without polling
- **PDF Reports**: Generate branded reports with embedded charts
- **User Activity Details**: Drill-down into who did what when

---

## Testing Checklist

- [x] Stats dashboard loads without errors
- [x] Summary stats display correct counts
- [x] All 4 charts render with data
- [x] Charts auto-refresh every 5 minutes
- [x] Permission check blocks unauthorized users
- [x] Error alerts show if API fails
- [x] Mobile layout stacks vertically
- [x] Chart legend toggles work
- [x] Activity timeline shows last 30 days
- [x] Package chart shows top 10 packages

---

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `routes/stats.py` | 180 | 5 endpoints for stats/charts |
| `templates/app/stats/index.html` | 350 | Dashboard with 4 charts |
| `routes/__init__.py` | 14 | Register stats blueprint |
| `templates/app/base.html` | 187 | Updated sidebar link |

**Total New Code**: ~530 lines
**External Dependency**: Chart.js 3.9.1 (CDN)

---

## Next Phase (Phase 6)

Telegram Bot Integration:
- Bot token configuration
- Message template management
- Conversation tracking
- Expiry notifications
- User verification workflow

See `PHASE_6_TELEGRAM_BOT.md` for details.
