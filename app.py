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

# Load channels data once at startup
channels_data = None

def load_channels_data():
    global channels_data
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            channels_data = json.load(f)
        print("✅ Channels data loaded successfully")
    except Exception as e:
        print(f"❌ Error loading channels data: {e}")
        channels_data = {"total_channels": 0, "countries": {}}

# Load data on startup
with app.app_context():
    load_channels_data()

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

# Routes
@app.route('/')
def index():
    """Serve the main landing page"""
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    """Serve the main landing page"""
    return render_template('index.html')

@app.route('/catalog')
def catalog():
    """Serve the catalog page"""
    return render_template('catalog.html')

@app.route('/api/channels')
def get_channels():
    """API endpoint to get all channels data"""
    if channels_data:
        return jsonify(channels_data)
    return jsonify({"error": "Channels data not available"}), 500

@app.route('/api/channels/<region>')
def get_region_channels(region):
    """API endpoint to get channels for a specific region/category"""
    if not channels_data or 'regions' not in channels_data:
        return jsonify({"error": "Channels data not available"}), 500

    region_upper = region.upper()

    # Find matching region (case insensitive)
    for r in channels_data['regions'].keys():
        if r.upper() == region_upper:
            return jsonify({
                "region": r,
                "count": channels_data['regions'][r]['count'],
                "channels": channels_data['regions'][r]['channels']
            })

    return jsonify({"error": f"Region '{region}' not found"}), 404

@app.route('/api/stats')
def get_stats():
    """API endpoint to get overall statistics"""
    if channels_data:
        return jsonify({
            "total_channels": channels_data.get('total_channels', 0),
            "total_regions": len(channels_data.get('regions', {})),
            "regions": list(channels_data.get('regions', {}).keys())
        })
    return jsonify({"error": "Stats not available"}), 500

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
    print("=" * 60)
    print("🎬 Mon IPTV Africa Backend")
    print("=" * 60)
    print(f"📊 Loaded {channels_data.get('total_channels', 0)} channels")
    print(f"🌍 {len(channels_data.get('countries', {}))} countries")
    print("")
    print("🚀 Starting server...")
    print("📍 http://localhost:5000")
    print("📖 API endpoints:")
    print("   - GET /api/channels          (all channels)")
    print("   - GET /api/channels/<country> (specific country)")
    print("   - GET /api/stats             (statistics)")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
