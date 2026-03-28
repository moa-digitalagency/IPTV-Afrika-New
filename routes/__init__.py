"""Routes blueprints"""

def register_blueprints(app):
    """Register all blueprints"""
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.api_internal import api_bp
    from routes.lines import lines_bp
    from routes.stats import stats_bp
    from routes.telegram import telegram_bp
    from routes.users import users_bp
    from routes.seo import seo_bp, settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(lines_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(telegram_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(seo_bp)
    app.register_blueprint(settings_bp)
