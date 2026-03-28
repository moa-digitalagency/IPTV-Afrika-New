# GOLDEN API Analysis & Integration

## API Endpoints Used

### 1. GET /v1/packages
**Purpose**: Fetch available packages with durations and trial status

**Response Structure**:
```json
{
  "packages": [
    {
      "id": 12345,
      "package_name": "24 Hours",
      "official_duration": 24,
      "official_duration_in": "hours",  // Can be: days, hours, months, years
      "is_trial": 1,
      "max_connections": 1,
      "credits_cost": 0
    }
  ]
}
```

**Key Points**:
- Must convert duration to days (24 hours = 1 day)
- `is_trial` flag determines line type
- Cached in `PackageCache` table

---

## 2. POST /v1/lines
**Purpose**: Create a new M3U line

**Request Payload**:
```json
{
  "username": "USER1234",
  "password": "ABCD123",
  "package_id": 12345
}
```

⚠️ **CRITICAL**: Only send `username`, `password`, `package_id`. The API does NOT accept:
- `full_name`
- `email`
- `note`

Sending unsupported fields may cause 422 validation errors.

**Response Structure**:
```json
{
  "id": 6857750,
  "username": "USER1234",
  "password": "ABCD123",
  "package_id": 12345,
  "package_name": "24 Hours",
  "enabled": true,
  "max_connections": 1,
  "created_at": "2026-03-28 15:30:00"
  // NOTE: Missing fields:
  // - exp_date (must calculate from package duration)
  // - dns_link (must fetch via GET /v1/lines/{id})
  // - full_name, email, note (not returned by API - save locally only)
}
```

**Missing Fields Handling**:
1. `exp_date`: Calculate as `now() + PackageCache.duration_days`
2. `dns_link`: Fetch via GET endpoint below
3. `full_name`, `email`, `note`: Save directly from form input to database

---

## 3. GET /v1/lines/{id}
**Purpose**: Fetch complete line details

**Response Structure**:
```json
{
  "id": 6857750,
  "username": "USER1234",
  "password": "ABCD123",
  "package_id": 12345,
  "package_name": "24 Hours",
  "dns_link": "http://kdifzszc.sidiman.com/get.php",
  "exp_date": "2026-03-29",
  "enabled": true,
  "max_connections": 1,
  "created_at": "2026-03-28T15:30:00Z"
}
```

**Key Points**:
- Always returns `dns_link` (required for M3U playlist URL)
- `exp_date` format varies: ISO8601 with T or simple YYYY-MM-DD
- Must parse both formats

---

## 4. POST /v1/lines/{id}/extend
**Purpose**: Extend line expiration

**Request**:
```json
{
  "days": 30
}
```

**Response**: Same as GET /v1/lines/{id}

---

## 5. POST /v1/lines/{id}/refund
**Purpose**: Refund and disable line

**Response**: Same as GET /v1/lines/{id}

---

## Current Integration Issues & Fixes

### Issue 1: exp_date = NULL → Testers Don't Appear
**Problem**:
- Create response doesn't include `exp_date`
- Filter `LineCache.exp_date > now()` fails when exp_date is NULL
- Testers show as 0 in active list

**Solution**:
- Fallback 1: Fetch full details via GET /v1/lines/{id}
- Fallback 2: Calculate from `PackageCache.duration_days`
  ```python
  if not cache_line.exp_date and package:
      duration_days = package.duration_days or 0
      if duration_days > 0:
          cache_line.exp_date = datetime.utcnow() + timedelta(days=duration_days)
  ```

**Code Location**: `routes/lines.py:305-310`

---

### Issue 2: dns_link = NULL → M3U Link Shows "Chargement..."
**Problem**:
- Create response doesn't include `dns_link`
- GET /v1/lines/{id} call may fail silently
- Template shows "Lien M3U non disponible" fallback message

**Solution**:
1. Always call GET /v1/lines/{id} after create if `dns_link` missing
2. Parse ISO8601 dates correctly (handle both T and plain formats)
3. Template handles None gracefully with error message

**Code Locations**:
- `routes/lines.py:277-303` (fetch full details)
- `templates/app/lines/detail.html:477-485` (handle missing dns_link)

---

### Issue 3: full_name, email, note = NULL
**Problem**:
- API doesn't accept these fields (422 validation error)
- API doesn't return these fields in response
- Must be stored locally in database only

**Solution**:
1. Don't send to API: `GoldenAPIService.create_line(username, password, package_id)`
2. Save directly from form: `full_name = request.form.get('full_name')`
3. Store in LineCache with explicit None handling:
   ```python
   cache_line = LineCache(
       full_name=full_name if full_name else None,
       email=email if email else None,
       note=note if note else None,
       ...
   )
   ```

**Code Location**: `routes/lines.py:195-275` (POST create_line)

---

## Complete Line Creation Flow

```
1. User submits form with:
   - username (or auto-generate)
   - password (or auto-generate)
   - package_id (required)
   - full_name (optional, local only)
   - email (optional, local only)
   - note (optional, local only)

2. Server validates package_id exists
   → Lookup PackageCache.is_trial and duration_days

3. Call GoldenAPI.create_line(username, password, package_id)
   → Returns: id, username, password, package_id, package_name, enabled, etc.
   → Missing: exp_date, dns_link, full_name, email, note

4. Save to LineCache:
   - API response fields (username, password, etc.)
   - Form input fields (full_name, email, note)
   - Empty/calculated fields (exp_date, dns_link)

5. Fetch full details: GoldenAPI.get_line(line_id)
   → Returns: dns_link, exp_date (if API provides it)
   → Update missing LineCache fields

6. Fallback exp_date calculation:
   - If still NULL, calculate: now() + package.duration_days
   → exp_date = datetime.utcnow() + timedelta(days=duration_days)

7. Redirect to detail page
   → Line now visible in lists (has exp_date)
   → M3U link available (has dns_link)
   → Full name/email/note displayed (from form input)
```

---

## Package Duration Conversion

Packages use variable duration units. Must convert to days:

```python
def convert_duration_to_days(duration: int, unit: str) -> int:
    if unit == 'years':
        return duration * 365
    elif unit == 'months':
        return duration * 30
    elif unit == 'hours':
        return max(1, duration // 24)  # Min 1 day
    else:  # days
        return duration
```

**Code Location**: `services/cache_service.py:sync_packages()`

---

## M3U URL Format

Complete M3U link with username, password, and parameters:

```
http://kdifzszc.sidiman.com/get.php?username=USER1234&password=ABCD123&type=m3u_plus&output=mpegts
```

**Parameters**:
- `username`: Credentials username
- `password`: Credentials password
- `type`: `m3u_plus` (or m3u, depending on API support)
- `output`: `mpegts` (transport stream format)

**Code Location**: `templates/app/lines/detail.html:481-507`

---

## Debugging Tips

1. **Check dns_link in database**:
   ```sql
   SELECT golden_id, username, dns_link, exp_date FROM line_cache WHERE golden_id = 6857750;
   ```

2. **Check package duration**:
   ```sql
   SELECT golden_id, package_name, duration_days FROM packages_cache;
   ```

3. **Verify API response** (enable debug logging):
   - Check `services/golden_api.py:172-178` (get_line debug logs)
   - Look for "Raw response" in console output

4. **Test API directly**:
   ```bash
   curl -H "X-API-Key: YOUR_KEY" https://api.goldentv.com/v1/packages
   curl -H "X-API-Key: YOUR_KEY" https://api.goldentv.com/v1/lines/6857750
   ```

---

## Key Takeaways

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Testers show 0 | exp_date = NULL | Calculate from package.duration_days |
| M3U link missing | dns_link = NULL | Fetch via GET endpoint |
| Validation errors | Sending unsupported fields | Only send username, password, package_id |
| Info not displaying | Storing API response instead of form input | Save full_name/email/note from form |

