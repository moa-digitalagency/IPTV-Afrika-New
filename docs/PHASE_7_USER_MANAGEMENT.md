# Phase 7 — User Management

**Status**: ✅ Completed
**Date**: 2026-03-28

---

## Overview

Phase 7 implements complete user account management with role-based access control and granular permissions. Admins can now:
- **Create** new user accounts with email and password
- **Edit** user details (email, role, active status)
- **Change** passwords for users
- **Delete** user accounts (soft delete - deactivate)
- **Manage** granular permissions per resource
- **View** user activity logs with full audit trail
- **Filter** users by search and pagination
- **Assign** roles: superadmin, admin, operator

All operations include permission checks, activity logging, and password security.

---

## Files Created

### Routes — `routes/users.py`
6 endpoints for user management:

| Route | Method | Purpose | Permission |
|-------|--------|---------|-----------|
| `/app/users/` | GET | List all users with pagination | `users:read` |
| `/app/users/create` | GET, POST | Create new user account | `users.create:write` |
| `/app/users/<id>/edit` | GET, POST | Edit user details | `users.edit:write` |
| `/app/users/<id>/password` | POST | Change user password | `users.edit:write` |
| `/app/users/<id>/delete` | POST | Deactivate user account | `users.delete:write` |
| `/app/users/<id>/permissions` | GET, POST | Manage user permissions | `users.permissions:write` |
| `/app/users/<id>/activity` | GET | View user activity log | `users:read` |

**Features:**
- `@superadmin_required` for all user management routes
- `@require_permission` enforces resource-based access
- Activity logging with `log_action()` helper
- Password hashing using `werkzeug.security`
- Form validation (email uniqueness, password length ≥8)
- Soft delete (deactivate instead of removing)
- AJAX operations for password/delete with confirmation

### Templates

#### `templates/app/users/index.html`
User list with search and pagination:

**Sections:**
1. **Search & Actions**
   - Text input for username filtering (client-side)
   - "New User" button

2. **Stats Cards**
   - Total users
   - Active users count
   - Superadmin count

3. **Users Table**
   - Columns: Username | Email | Role | Status | Created | Last Login | Actions
   - Role badge (red/orange/green for superadmin/admin/operator)
   - Status indicator (green/gray for active/inactive)
   - Action buttons: Edit (✏️), Permissions (🔐), Activity (📊)

4. **Pagination**
   - 20 users per page
   - Standard pagination controls
   - Empty state when no users

#### `templates/app/users/create.html`
Create new user form:

**Form Fields:**
- Username input (alphanumeric + hyphens)
- Email input (validated format)
- Password input (≥8 chars)
- Role select: Operator (🟢) | Admin (🟠) | Superadmin (🔴)

**Info Panel:**
- Role descriptions with permission explanations

#### `templates/app/users/edit.html`
Edit user details with sidebar actions:

**Left Column:**
- Email input
- Role selector
- Active checkbox
- Save button

**Right Column:**
1. **Account Info**
   - Username (readonly)
   - Created date
   - Last login timestamp

2. **Password Change**
   - New password input (≥8 chars)
   - Change button (AJAX)

3. **Actions**
   - Manage Permissions button
   - View Activity button
   - Delete button (with confirmation)

#### `templates/app/users/permissions.html`
Granular permission management:

**Info Panel:**
- Explanation of Read vs Write permissions
- Visual indicators for each action type

**Permission Cards:**
- Grouped by resource (lines, stats, telegram, etc.)
- Checkboxes for read/write permissions
- Color-coded by resource type
- Save button to commit changes

**Quick Presets:**
- Operator preset button
- Admin preset button
- Superadmin preset button
- Clear all button

#### `templates/app/users/activity.html`
User activity audit trail:

**Stats:**
- Total activity count
- Last action timestamp

**Activity Table:**
- Columns: Action | Target | Details | IP | Date/Time
- Sortable by timestamp (desc)
- Paginated (50 per page)
- Action types: user_*, line_*, telegram_*
- Details shown as key-value pairs

---

## Database Models (Already Defined)

### `User`
| Field | Type | Constraint |
|-------|------|-----------|
| id | SERIAL | PK |
| username | VARCHAR(80) | UNIQUE NOT NULL |
| email | VARCHAR(120) | UNIQUE NOT NULL |
| password_hash | VARCHAR(256) | NOT NULL |
| role | VARCHAR(20) | DEFAULT 'operator' |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | DEFAULT NOW() |
| last_login | TIMESTAMP | nullable |
| created_by | INTEGER | FK users.id |

**Roles:**
- `superadmin` - Full system access + configuration
- `admin` - Most features, no user management
- `operator` - Basic line management only

### `Permission`
| Field | Type | Constraint |
|-------|------|-----------|
| id | SERIAL | PK |
| user_id | INTEGER | FK users.id CASCADE |
| resource | VARCHAR(50) | e.g., 'lines.create', 'telegram.config' |
| can_read | BOOLEAN | DEFAULT TRUE |
| can_write | BOOLEAN | DEFAULT FALSE |
| UNIQUE(user_id, resource) | | |

**Resources:**
- `lines`, `lines.testers`, `lines.subscribers`, `lines.create`, `lines.extend`, `lines.refund`
- `stats`
- `telegram.config`, `telegram.templates`, `telegram.conversations`
- `users`, `users.create`, `users.edit`, `users.delete`, `users.permissions`
- `seo`, `settings`

---

## Security Features

### Password Security
- Hashed with `werkzeug.security.generate_password_hash()`
- Verified with `check_password_hash()`
- Minimum 8 characters enforced
- Salt generated per password
- Never stored in plaintext

### Permission Checks
- `@superadmin_required` decorator on all routes
- `@require_permission` validates resource access
- Granular permissions override role defaults
- All mutations require `write` permission
- All reads require `read` permission

### Account Management
- Email uniqueness enforced
- Soft delete (deactivate instead of remove)
- Cannot delete own account
- Cannot delete superadmin from UI (Phase 7.1)
- Password changes logged with admin flag

### Audit Logging
- All operations logged to `ActivityLog`
- Includes: user, action, target, detail, IP, timestamp
- Activity visible in user profile
- Sorted chronologically (newest first)
- 50-item pagination for large histories

---

## API Endpoints

### List Users
```
GET /app/users/?page=1
Returns: User list with pagination
```

### Create User
```
POST /app/users/create
Body: {
    username: str,
    email: str,
    password: str (≥8 chars),
    role: str (superadmin|admin|operator)
}
Returns: 302 redirect to edit page
```

### Edit User
```
POST /app/users/<id>/edit
Body: {
    email: str,
    role: str,
    is_active: bool
}
Returns: 302 redirect to edit page
```

### Change Password (AJAX)
```
POST /app/users/<id>/password
Body: password=str
Returns: {"success": bool, "message": str}
```

### Delete User (AJAX)
```
POST /app/users/<id>/delete
Returns: {"success": bool, "message": str}
```

### Manage Permissions
```
POST /app/users/<id>/permissions
Body: perm_<resource>_<action>=on
Returns: 302 redirect to permissions page
```

### View Activity
```
GET /app/users/<id>/activity?page=1
Returns: Activity log with pagination
```

---

## User Workflow

```
CREATE USER
  ↓
[superadmin] → fill form → POST /create
  ↓
[system] → hash password → create user
  ↓
[superadmin] → assign role + email
  ↓
[superadmin] → optionally customize permissions
  ↓
[superadmin] → user can login
```

**Login Flow:**
```
USER LOGIN
  ↓
[user] → /login → enter username/password
  ↓
[system] → verify password hash
  ↓
[system] → load permissions for user
  ↓
[system] → create Flask-Login session
  ↓
[user] → access /app/* routes
```

**Permission Check:**
```
USER ACCESSES RESOURCE
  ↓
@login_required → verify session
  ↓
@require_permission → check user permissions
  ↓
[system] → query Permission table for resource
  ↓
[system] → verify can_read/can_write
  ↓
[allowed] → proceed | [denied] → 403 Forbidden
```

---

## Role Defaults (Phase 7.1)

**Operator (🟢)**
- lines.testers: read
- lines.subscribers: read
- lines.create: write
- lines.extend: write
- stats: read

**Admin (🟠)**
- [Operator permissions]
- lines.refund: write
- telegram.config: read
- telegram.templates: read
- telegram.conversations: read + write

**Superadmin (🔴)**
- All permissions: read + write
- Can manage users
- Can configure system settings

---

## Testing Checklist

- [x] User list displays with pagination
- [x] Create user form validates password length
- [x] Email uniqueness enforced
- [x] Edit user updates all fields
- [x] Password change works via AJAX
- [x] Delete user deactivates account
- [x] Deleted users cannot login
- [x] Permission checkboxes save correctly
- [x] Activity log shows all actions
- [x] Search filters username (client-side)
- [x] Permission decorators block unauthorized access
- [x] All actions logged with user + IP
- [x] Role badges display correctly

---

## Performance Considerations

### Database
- User queries indexed on username/email
- Pagination at 20 users per list, 50 per activity log
- Permission checks use single FK query
- Activity logs paginated to avoid large loads

### Frontend
- Client-side search (JavaScript filter, no server query)
- AJAX for password/delete to avoid full page reload
- No heavy computations in templates

### Security
- Password hashing (bcrypt-style, computationally expensive by design)
- All form inputs validated on server
- CSRF token required for all POST requests

---

## Future Enhancements (Phase 7.1+)

- **Permission Presets**: Apply operator/admin/superadmin templates with one click
- **Bulk User Import**: CSV upload for creating multiple users
- **Session Management**: View/revoke active user sessions
- **Two-Factor Authentication**: TOTP or email OTP
- **API Keys**: Generate tokens for automated access
- **Audit Report**: Download activity logs as CSV/PDF
- **User Restrictions**: Limit by company, region, or feature set
- **IP Whitelisting**: Restrict login to specific IP ranges
- **Password Policy**: Enforce complexity, expiration, history
- **Single Sign-On**: OAuth2/OIDC integration

---

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `routes/users.py` | 280 | 6 endpoints for user CRUD + permissions |
| `templates/app/users/index.html` | 150 | User list with search + pagination |
| `templates/app/users/create.html` | 140 | User creation form |
| `templates/app/users/edit.html` | 220 | User edit + password change + delete |
| `templates/app/users/permissions.html` | 150 | Granular permission management |
| `templates/app/users/activity.html` | 130 | Activity audit log |
| `routes/__init__.py` | 14 | Register users blueprint |
| `templates/app/base.html` | 187 | Updated sidebar link |

**Total New Code**: ~1,200 lines
**External Dependencies**: None (uses werkzeug from Flask)
**Database Tables**: 2 (User, Permission)

---

## Next Phase (Phase 8)

SEO & Settings:
- Meta tag management per page
- Dynamic robots.txt generation
- Sitemap generation (static + dynamic)
- App-wide settings (golden API key, cache TTL, branding)
- Test API connectivity
- Export/import configuration

See `PHASE_8_SEO_SETTINGS.md` for details.
