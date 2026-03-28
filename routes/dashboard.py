"""Dashboard routes"""
from flask import Blueprint, render_template
from flask_login import login_required
from security.decorators import require_permission

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/app')

@dashboard_bp.route('/', methods=['GET'])
@login_required
@require_permission('dashboard', 'read')
def index():
    """Dashboard index page"""
    return render_template('app/dashboard.html')
