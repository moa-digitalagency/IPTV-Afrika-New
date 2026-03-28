#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean up old logs from the database
Run monthly via cron: 0 0 1 * * /path/to/cleanup_logs.py
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cleanup_logs():
    """Remove activity logs older than 90 days"""
    from config.development import DevelopmentConfig
    from config.database import db
    from models.logs import ActivityLog
    from flask import Flask

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        from config.production import ProductionConfig as Config
    else:
        Config = DevelopmentConfig

    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        print("=" * 60)
        print("🧹 Cleaning Up Old Logs")
        print("=" * 60)

        # Delete activity logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted_count = ActivityLog.query.filter(
            ActivityLog.created_at < cutoff_date
        ).delete()

        db.session.commit()

        print(f"\n✅ Deleted {deleted_count} activity logs older than 90 days")
        print(f"   Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")

        # Get current log stats
        total_logs = ActivityLog.query.count()
        oldest_log = ActivityLog.query.order_by(ActivityLog.created_at.asc()).first()

        print(f"\n📊 Current log stats:")
        print(f"   • Total logs: {total_logs}")
        if oldest_log:
            print(f"   • Oldest log: {oldest_log.created_at.strftime('%Y-%m-%d')}")

        print("\n" + "=" * 60)
        return True

if __name__ == '__main__':
    try:
        cleanup_logs()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
