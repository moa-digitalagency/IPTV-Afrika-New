"""
Security Headers Configuration
- Content Security Policy (CSP)
- X-Frame-Options (clickjacking protection)
- X-Content-Type-Options (MIME sniffing)
- Strict-Transport-Security (HSTS)
- Referrer-Policy
"""

from flask import request

def init_security_headers(app):
    """Register security header middleware"""

    @app.after_request
    def set_security_headers(response):
        """Apply security headers to all responses"""

        # Content Security Policy
        # - Prevents inline scripts (XSS)
        # - Allows scripts only from self
        # - Allows Chart.js, Font Awesome and other CDNs
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com unpkg.com cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.tailwindcss.com fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: cdnjs.cloudflare.com fonts.gstatic.com; "
            "connect-src 'self' api.telegram.org fonts.googleapis.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prevent clickjacking attacks
        # - DENY: page cannot be embedded anywhere
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        # - Force browser to respect Content-Type
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable HTTPS enforcement (30 days, includeSubDomains)
        response.headers['Strict-Transport-Security'] = 'max-age=2592000; includeSubDomains'

        # Prevent browser XSS filter bypass (IE only, but harmless)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer Policy - don't send full referrer to external sites
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Feature-Policy / Permissions-Policy
        # - Disable camera, microphone, geolocation, etc.
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )

        return response

    # Optional: Redirect HTTP to HTTPS in production
    @app.before_request
    def enforce_https():
        """Enforce HTTPS in production"""
        if app.config.get('ENV') == 'production':
            if request.endpoint and 'static' not in request.endpoint:
                if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
                    url = request.url.replace('http://', 'https://', 1)
                    return redirect(url, code=301)

def get_csp_nonce(app):
    """Generate CSP nonce for inline scripts (if needed)"""
    import secrets
    return secrets.token_urlsafe(16)
