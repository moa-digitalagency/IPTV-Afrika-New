"""
Rate Limiting Configuration
- Login attempt limiting (5 per minute per IP)
- API endpoint rate limiting
- Custom error handling
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import jsonify

def init_limiter(app):
    """Initialize Flask-Limiter with app"""
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
        strategy="fixed-window"
    )

    @limiter.error_handler
    def ratelimit_error_handler(e):
        """Custom error handler for rate limit violations"""
        return jsonify({
            'success': False,
            'message': '⚠️ Trop de tentatives. Veuillez réessayer dans quelques minutes.',
            'error_code': 'RATE_LIMIT_EXCEEDED'
        }), 429

    return limiter

# Rate limit decorators
LOGIN_LIMIT = "5 per minute"           # 5 attempts per minute per IP
API_LIMIT = "30 per minute"             # 30 API calls per minute per IP
SEARCH_LIMIT = "10 per minute"          # 10 searches per minute per IP
EXPORT_LIMIT = "5 per hour"             # 5 exports per hour per IP

"""
Usage in routes:

from security.rate_limiter import LOGIN_LIMIT

@app.route('/login', methods=['POST'])
@limiter.limit(LOGIN_LIMIT)
def login():
    ...

For AJAX endpoints:
@app.route('/api/test', methods=['POST'])
@limiter.limit(API_LIMIT)
def test_api():
    ...
"""
