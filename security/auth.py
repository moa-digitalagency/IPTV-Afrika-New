"""Flask-Login configuration"""
from flask_login import LoginManager
from models.user import User

login_manager = LoginManager()

def init_login_manager(app):
    """Initialize Flask-Login"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
