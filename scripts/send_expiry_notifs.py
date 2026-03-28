#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send expiry notifications to users
Run daily via cron: 0 9 * * * /path/to/send_expiry_notifs.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def send_notifications():
    """Send expiry notifications for lines expiring soon"""
    from config.development import DevelopmentConfig
    from config.database import db
    from services.notification_service import NotificationService
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
        print("📬 Sending Expiry Notifications")
        print("=" * 60)

        stats = NotificationService.get_expiry_stats()
        print(f"\n📊 Current status:")
        print(f"   • Total active lines: {stats['total_active']}")
        print(f"   • Expired: {stats['expired']}")
        print(f"   • Expiring soon (7 days): {stats['expiring_soon']}")
        print(f"   • Healthy: {stats['healthy']}")

        expiring_lines = NotificationService.get_expiring_lines()
        print(f"\n📋 Found {len(expiring_lines)} lines expiring soon")

        # TODO: Implement Telegram notification sending
        # This will be implemented in Phase 6
        print("\n⚠️  Telegram notifications not yet implemented")
        print("This will be implemented in Phase 6 (Telegram Bot)")

        print("\n" + "=" * 60)
        return True

if __name__ == '__main__':
    try:
        send_notifications()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
