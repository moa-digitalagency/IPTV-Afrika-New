#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GOLDEN API connection and credentials
Useful for debugging API issues
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api():
    """Test GOLDEN API connectivity and credentials"""
    from config.development import DevelopmentConfig
    from config.database import db
    from services.golden_api import GoldenAPIService, GoldenAPIException
    from models.settings import AppSetting
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
        print("🧪 GOLDEN API Connection Test")
        print("=" * 60)

        # Check configuration
        print("\n📋 Checking configuration...")
        golden_key = AppSetting.query.filter_by(key='golden_api_key').first()
        golden_url = AppSetting.query.filter_by(key='golden_api_base_url').first()

        if not golden_key or not golden_key.value:
            print("❌ API Key not configured")
            print("   Set it in app settings: golden_api_key")
            return False

        if not golden_url or not golden_url.value:
            print("❌ API URL not configured")
            print("   Set it in app settings: golden_api_base_url")
            return False

        print(f"✅ API Key configured: {golden_key.value[:10]}...")
        print(f"✅ API URL: {golden_url.value}")

        # Test connection
        print("\n🔌 Testing connection...")
        success, message = GoldenAPIService.test_connection()

        if success:
            print(f"✅ {message}")
            print("\n✅ GOLDEN API is accessible!")
            return True
        else:
            print(f"❌ {message}")
            print("\n❌ Failed to connect to GOLDEN API")
            print("\nPossible issues:")
            print("  1. Invalid API key (golden_api_key)")
            print("  2. Wrong API URL (golden_api_base_url)")
            print("  3. Network connectivity issues")
            print("  4. API server is down")
            return False

if __name__ == '__main__':
    try:
        success = test_api()
        print("\n" + "=" * 60)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("=" * 60)
        sys.exit(1)
