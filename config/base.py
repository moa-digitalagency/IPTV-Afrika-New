"""Base configuration class"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://iptv_user:iptv_password@localhost:5432/iptv_afrika'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cache
    CACHE_TTL_LINES = int(os.environ.get('CACHE_TTL_LINES', 900))  # 15 minutes
    CACHE_TTL_PACKAGES = int(os.environ.get('CACHE_TTL_PACKAGES', 3600))  # 1 hour

    # API
    GOLDEN_API_BASE_URL = os.environ.get('GOLDEN_API_BASE_URL', 'https://api.goldentv.com')
    GOLDEN_API_KEY = os.environ.get('GOLDEN_API_KEY', '')

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')

    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_SECRET_TOKEN = os.environ.get('TELEGRAM_SECRET_TOKEN', '')

    # Pagination
    ITEMS_PER_PAGE = 20
