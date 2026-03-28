#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mon IPTV Africa Backend - Flask app with landing pages + admin dashboard
"""

from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ENV = os.environ.get('FLASK_ENV', 'development')
if ENV == 'production':
    from config.production import ProductionConfig as Config
else:
    from config.development import DevelopmentConfig as Config

app = Flask(__name__,
    template_folder='templates',
    static_folder='statics',
    static_url_path='/statics'
)

# Load configuration
app.config.from_object(Config)

# Enable CORS
CORS(app)

# Initialize database
from config.database import db
db.init_app(app)

# Initialize Flask-Login
from security.auth import init_login_manager
init_login_manager(app)

# Initialize Security Headers
from security.headers import init_security_headers
init_security_headers(app)

# Initialize Rate Limiter
from security.rate_limiter import init_limiter
limiter = init_limiter(app)

# Register blueprints (admin routes)
from routes import register_blueprints
register_blueprints(app)

# Load data on startup
with app.app_context():
    # Sync packages from GOLDEN API on startup
    try:
        from services.cache_service import CacheService
        CacheService.sync_packages()
    except Exception as e:
        print(f"⚠️  Warning: Could not sync packages on startup: {e}")

    # Migrate missing exp_dates for lines without expiration dates
    try:
        from scripts.migrate_missing_exp_dates import migrate_missing_exp_dates
        migrate_missing_exp_dates()
    except Exception as e:
        print(f"⚠️  Warning: Could not migrate missing exp_dates: {e}")

    # Recalculate incorrect exp_dates (when package durations change)
    try:
        from scripts.recalculate_incorrect_exp_dates import recalculate_incorrect_exp_dates
        recalculate_incorrect_exp_dates()
    except Exception as e:
        print(f"⚠️  Warning: Could not recalculate exp_dates: {e}")

# Routes
@app.route('/')
def index():
    """Serve the main landing page"""
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    """Serve the main landing page"""
    return render_template('index.html')

@app.route('/installation')
def installation():
    """Serve the installation page"""
    return render_template('installation.html')

@app.route('/sports')
def sports():
    """Serve the sports page"""
    return render_template('sports.html')

@app.route('/vod')
def vod():
    """Serve the VOD (Films & Séries) page"""
    return render_template('vod.html')

@app.route('/statics/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('statics', filename)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("🎬 Mon IPTV Africa Backend")
    print("=" * 60)
    print("🚀 Starting server...")
    print(f"📍 http://localhost:{port}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=port)
