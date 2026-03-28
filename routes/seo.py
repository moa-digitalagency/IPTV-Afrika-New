"""
SEO Management Routes
- Meta tag editing per page
- robots.txt generation
- Sitemap generation
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

from config.database import db
from models.settings import SeoSetting
from models.logs import ActivityLog
from security.decorators import require_permission, superadmin_required
from services.seo_service import SeoService
from utils.date_helpers import format_date_fr

seo_bp = Blueprint('seo', __name__, url_prefix='/app/seo')

# ============================================================================
# DECORATORS
# ============================================================================

def log_action(action, target_type=None, target_id=None, detail=None):
    """Log action to activity log"""
    try:
        ip = request.remote_addr or '0.0.0.0'
        log = ActivityLog(
            user_id=current_user.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail or {},
            ip_address=ip
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging action: {e}")

# ============================================================================
# ROUTES
# ============================================================================

@seo_bp.route('/', methods=['GET'])
@login_required
@require_permission('seo', 'read')
def index():
    """SEO management overview"""
    # Get list of pages that have SEO settings
    pages = db.session.query(SeoSetting.page_slug).distinct().all()
    page_list = [p[0] for p in pages]

    # Predefined pages
    predefined_pages = {
        'home': 'Accueil',
        'catalog': 'Catalogue',
        'channels': 'Chaînes',
        'about': 'À Propos',
        'contact': 'Contact',
        'legal': 'Mentions Légales',
        'privacy': 'Politique de Confidentialité',
    }

    # Get SEO data for each page
    seo_pages = {}
    for slug, title in predefined_pages.items():
        seo = SeoSetting.query.filter_by(page_slug=slug).first()
        seo_pages[slug] = {
            'title': title,
            'has_meta': seo is not None,
            'meta_title': seo.meta_title if seo else None,
            'meta_description': seo.meta_description if seo else None,
            'updated_at': format_date_fr(seo.updated_at) if seo and seo.updated_at else 'Jamais'
        }

    return render_template('app/seo/index.html', seo_pages=seo_pages)

@seo_bp.route('/page/<slug>', methods=['GET', 'POST'])
@login_required
@require_permission('seo', 'write')
@superadmin_required
def edit_page(slug):
    """Edit meta tags for a page"""
    predefined_pages = {
        'home': 'Accueil',
        'catalog': 'Catalogue',
        'channels': 'Chaînes',
        'about': 'À Propos',
        'contact': 'Contact',
        'legal': 'Mentions Légales',
        'privacy': 'Politique de Confidentialité',
    }

    if slug not in predefined_pages:
        flash('Page non trouvée', 'danger')
        return redirect(url_for('seo.index'))

    seo = SeoSetting.query.filter_by(page_slug=slug).first()

    if request.method == 'POST':
        # Create or update SEO setting
        if not seo:
            seo = SeoSetting(page_slug=slug)
            db.session.add(seo)

        seo.meta_title = request.form.get('meta_title', '').strip()
        seo.meta_description = request.form.get('meta_description', '').strip()
        seo.og_title = request.form.get('og_title', '').strip()
        seo.og_description = request.form.get('og_description', '').strip()
        seo.og_image_url = request.form.get('og_image_url', '').strip()
        seo.og_type = request.form.get('og_type', 'website').strip()
        seo.canonical_url = request.form.get('canonical_url', '').strip()
        seo.robots_directive = request.form.get('robots_directive', 'index, follow').strip()
        seo.updated_by = current_user.id
        seo.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            log_action('seo_update', 'page', slug, {
                'meta_title': seo.meta_title[:50],
                'meta_description': seo.meta_description[:50]
            })
            flash(f'Meta tags de la page "{predefined_pages[slug]}" mis à jour', 'success')
            return redirect(url_for('seo.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la sauvegarde: {str(e)}', 'danger')

    return render_template('app/seo/page_editor.html',
        page_slug=slug,
        page_title=predefined_pages[slug],
        seo=seo
    )

@seo_bp.route('/robots.txt', methods=['GET'])
def robots_txt():
    """Generate robots.txt dynamically"""
    content = SeoService.generate_robots_txt()
    return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@seo_bp.route('/sitemap.xml', methods=['GET'])
def sitemap_xml():
    """Generate sitemap.xml dynamically"""
    content = SeoService.generate_sitemap()
    return content, 200, {'Content-Type': 'application/xml; charset=utf-8'}

# ============================================================================
# SETTINGS ROUTES
# ============================================================================

settings_bp = Blueprint('settings', __name__, url_prefix='/app/settings')

@settings_bp.route('/', methods=['GET'])
@login_required
@require_permission('settings', 'read')
def index():
    """Settings overview page"""
    # Get current settings
    settings = {}
    app_settings = db.session.query(
        db.func.count(db.literal_column('*')).label('total')
    ).select_entity_from(db.text('app_settings')).scalar()

    return render_template('app/settings/index.html', settings=settings)

@settings_bp.route('/golden-api', methods=['POST'])
@login_required
@require_permission('settings', 'write')
@superadmin_required
def update_golden_api():
    """Update GOLDEN API credentials"""
    from models.settings import AppSetting
    from services.golden_api import GoldenAPIService

    api_key = request.form.get('api_key', '').strip()
    api_url = request.form.get('api_url', '').strip()

    if not api_key or not api_url:
        flash('API key et URL sont obligatoires', 'danger')
        return redirect(url_for('settings.index'))

    try:
        # Update or create settings
        for key, value in [('golden_api_key', api_key), ('golden_api_base_url', api_url)]:
            setting = AppSetting.query.filter_by(key=key).first()
            if not setting:
                setting = AppSetting(key=key, value_type='string')
                db.session.add(setting)
            setting.value = value
            setting.updated_by = current_user.id
            setting.updated_at = datetime.utcnow()

        db.session.commit()
        log_action('settings_update', 'golden_api', None, {'key': api_key[:20] + '...'})
        flash('Paramètres GOLDEN API mis à jour', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la sauvegarde: {str(e)}', 'danger')

    return redirect(url_for('settings.index'))

@settings_bp.route('/branding', methods=['POST'])
@login_required
@require_permission('settings', 'write')
@superadmin_required
def update_branding():
    """Update branding settings"""
    from models.settings import AppSetting

    app_name = request.form.get('app_name', '').strip()
    app_description = request.form.get('app_description', '').strip()

    if not app_name:
        flash('Nom de l\'application obligatoire', 'danger')
        return redirect(url_for('settings.index'))

    try:
        for key, value in [('app_name', app_name), ('app_description', app_description)]:
            if value:
                setting = AppSetting.query.filter_by(key=key).first()
                if not setting:
                    setting = AppSetting(key=key, value_type='string')
                    db.session.add(setting)
                setting.value = value
                setting.updated_by = current_user.id
                setting.updated_at = datetime.utcnow()

        db.session.commit()
        log_action('settings_update', 'branding', None, {'app_name': app_name})
        flash('Paramètres de marque mis à jour', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la sauvegarde: {str(e)}', 'danger')

    return redirect(url_for('settings.index'))

@settings_bp.route('/notifications', methods=['POST'])
@login_required
@require_permission('settings', 'write')
@superadmin_required
def update_notifications():
    """Update notification settings"""
    from models.settings import AppSetting

    notify_expiry = request.form.get('notify_expiry', 'off') == 'on'
    expiry_days = request.form.get('expiry_days', '7', type=int)

    try:
        for key, value in [('notify_expiry', str(notify_expiry)), ('expiry_notify_days', str(expiry_days))]:
            setting = AppSetting.query.filter_by(key=key).first()
            if not setting:
                setting = AppSetting(key=key, value_type='boolean' if key == 'notify_expiry' else 'integer')
                db.session.add(setting)
            setting.value = value
            setting.updated_by = current_user.id
            setting.updated_at = datetime.utcnow()

        db.session.commit()
        log_action('settings_update', 'notifications', None, {'notify_expiry': notify_expiry})
        flash('Paramètres de notification mis à jour', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la sauvegarde: {str(e)}', 'danger')

    return redirect(url_for('settings.index'))

@settings_bp.route('/test-api', methods=['POST'])
@login_required
@require_permission('settings', 'read')
@superadmin_required
def test_api():
    """Test GOLDEN API connection"""
    from services.golden_api import GoldenAPIService, GoldenAPIException

    try:
        # Try to fetch packages as test
        result = GoldenAPIService.get_packages()
        if result:
            return jsonify({
                'success': True,
                'message': f'✅ Connexion réussie — {len(result)} packages trouvés',
                'packages_count': len(result)
            })
        else:
            return jsonify({
                'success': False,
                'message': '❌ Aucun package retourné'
            }), 400
    except GoldenAPIException as e:
        return jsonify({
            'success': False,
            'message': f'❌ Erreur API: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Erreur: {str(e)}'
        }), 500

@settings_bp.route('/cache-ttl', methods=['POST'])
@login_required
@require_permission('settings', 'write')
@superadmin_required
def update_cache_ttl():
    """Update cache TTL settings"""
    from models.settings import AppSetting

    cache_ttl_lines = request.form.get('cache_ttl_lines', '900', type=int)
    cache_ttl_packages = request.form.get('cache_ttl_packages', '3600', type=int)

    if cache_ttl_lines < 60 or cache_ttl_packages < 300:
        flash('TTL minimum: 60s pour lines, 300s pour packages', 'danger')
        return redirect(url_for('settings.index'))

    try:
        for key, value in [('cache_ttl_lines', str(cache_ttl_lines)), ('cache_ttl_packages', str(cache_ttl_packages))]:
            setting = AppSetting.query.filter_by(key=key).first()
            if not setting:
                setting = AppSetting(key=key, value_type='integer')
                db.session.add(setting)
            setting.value = str(value)
            setting.updated_by = current_user.id
            setting.updated_at = datetime.utcnow()

        db.session.commit()
        log_action('settings_update', 'cache_ttl', None, {'lines': cache_ttl_lines, 'packages': cache_ttl_packages})
        flash('TTL du cache mis à jour', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la sauvegarde: {str(e)}', 'danger')

    return redirect(url_for('settings.index'))
