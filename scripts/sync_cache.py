#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache synchronization script - syncs GOLDEN API data to local database
Run this every 15 minutes via cron: */15 * * * * /path/to/sync_cache.py
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def sync_cache():
    """Synchronize GOLDEN API data to local database"""
    from config.development import DevelopmentConfig
    from config.database import db
    from services.cache_service import CacheService
    from services.golden_api import GoldenAPIException
    from flask import Flask

    # Load environment if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Determine environment
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        from config.production import ProductionConfig as Config
    else:
        Config = DevelopmentConfig

    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        success, message = CacheService.sync_all()

        # Log result
        if success:
            print(f"\n✅ {message}")
            sys.exit(0)
        else:
            print(f"\n❌ {message}")
            sys.exit(1)

if __name__ == '__main__':
    sync_cache()
