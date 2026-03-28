#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database initialization script - creates all tables and superadmin user"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Ensure proper import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialize database and create superadmin"""
    from config.development import DevelopmentConfig
    from config.database import db
    from models.user import User
    from models.line import LineCache, PackageCache
    from models.telegram import TelegramConfig, TelegramMessageTemplate, TelegramConversation
    from models.settings import AppSetting, SeoSetting
    from models.logs import ActivityLog, CacheSyncLog
    from flask import Flask

    # Create Flask app with config
    app = Flask(__name__,
        template_folder='templates',
        static_folder='statics',
        static_url_path='/statics'
    )
    app.config.from_object(DevelopmentConfig)

    # Initialize database
    db.init_app(app)

    with app.app_context():
        print("=" * 60)
        print("🗄️  Mon IPTV Africa Database Initialization")
        print("=" * 60)

        # Create all tables
        print("\n📊 Creating database tables...")
        try:
            db.create_all()
            print("✅ All tables created successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            sys.exit(1)

        # Create superadmin if not exists
        print("\n👤 Setting up superadmin user...")

        # Get superadmin credentials from environment
        superadmin_username = os.getenv('SUPERADMIN_USERNAME', 'admin')
        superadmin_email = os.getenv('SUPERADMIN_EMAIL', 'admin@moniptvafrica.com')
        superadmin_password = os.getenv('SUPERADMIN_PASSWORD', 'changeme123456')

        superadmin = User.query.filter_by(username=superadmin_username).first()

        if superadmin:
            print(f"⚠️  Superadmin already exists (username: {superadmin_username})")
        else:
            superadmin = User(
                username=superadmin_username,
                email=superadmin_email,
                role='superadmin',
                is_active=True,
                created_at=datetime.utcnow()
            )
            superadmin.set_password(superadmin_password)
            db.session.add(superadmin)
            db.session.commit()
            print(f"✅ Superadmin created (username: {superadmin_username}, email: {superadmin_email})")
            print("⚠️  PLEASE CHANGE THE DEFAULT PASSWORD!")

        # Create default app settings
        print("\n⚙️  Setting up default application settings...")
        default_settings = [
            AppSetting(
                key='app_name',
                value='Mon IPTV Africa',
                value_type='string',
                description='Application name'
            ),
            AppSetting(
                key='golden_api_key',
                value='m8hSy8wU38iUzbs3a7V3fjrCjGUwJSq9YtVrYVsjGfX2GfY3lx7cLsSVscwDgkjX',
                value_type='string',
                description='GOLDEN API Key'
            ),
            AppSetting(
                key='golden_api_base_url',
                value='https://goldenott.net/api',
                value_type='string',
                description='GOLDEN API Base URL'
            ),
            AppSetting(
                key='cache_ttl_lines',
                value='900',
                value_type='integer',
                description='Cache TTL for lines in seconds (default: 900 = 15 min)'
            ),
            AppSetting(
                key='cache_ttl_packages',
                value='3600',
                value_type='integer',
                description='Cache TTL for packages in seconds (default: 3600 = 1 hour)'
            ),
        ]

        for setting in default_settings:
            existing = AppSetting.query.filter_by(key=setting.key).first()
            if not existing:
                db.session.add(setting)

        db.session.commit()
        print("✅ Default settings created")

        # Create default Telegram message templates
        print("\n💬 Setting up default Telegram templates...")
        default_templates = [
            TelegramMessageTemplate(
                slug='welcome',
                title='Welcome',
                body='Bienvenue! 👋\n\nVous avez accès à une ligne M3U IPTV.\n\nDétails:\n• Username: {username}\n• Expire le: {exp_date}\n• Package: {package}\n• Lien DNS: {dns_link}',
                is_active=True,
                lang='fr'
            ),
            TelegramMessageTemplate(
                slug='expiry_warning',
                title='Expiry Warning',
                body='⚠️ Votre abonnement expire bientôt!\n\nVotre ligne M3U {username} expire le {exp_date}.\n\nContactez-nous pour renouveler.',
                is_active=True,
                lang='fr'
            ),
        ]

        for template in default_templates:
            existing = TelegramMessageTemplate.query.filter_by(slug=template.slug).first()
            if not existing:
                db.session.add(template)

        db.session.commit()
        print("✅ Default templates created")

        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("1. Update .env with GOLDEN API credentials")
        print("2. Run: python app.py")
        print("3. Visit: http://localhost:5000/auth/login")
        print("4. Login with admin/change_me_in_production")
        print("=" * 60)

if __name__ == '__main__':
    init_database()
