"""
SEO Service
- Generate robots.txt
- Generate sitemap.xml
- Meta tag management
"""

from datetime import datetime
from urllib.parse import urljoin
from flask import current_app
import os

class SeoService:
    """Service for SEO operations"""

    @staticmethod
    def get_base_url():
        """Get application base URL"""
        if current_app:
            return current_app.config.get('SERVER_URL', 'https://iptvafrka.com')
        return 'https://iptvafrika.com'

    @staticmethod
    def generate_robots_txt():
        """
        Generate robots.txt dynamically

        Allows:
        - All paths except /app/* (admin)
        - Sitemap location
        - Crawl delay
        """
        base_url = SeoService.get_base_url()

        robots = """# Robots.txt for Mon IPTV Africa
# Generated dynamically

User-agent: *
Allow: /
Disallow: /app/
Disallow: /admin/
Disallow: /api/internal/
Disallow: /*.json$
Disallow: /login/
Disallow: /logout/

# Crawl delay
Crawl-delay: 2

# Sitemaps
Sitemap: {}/sitemap.xml

# Search engines
User-agent: Googlebot
Allow: /
Disallow: /app/
Crawl-delay: 1

User-agent: Bingbot
Allow: /
Disallow: /app/
Crawl-delay: 1
""".format(base_url)

        return robots

    @staticmethod
    def generate_sitemap():
        """
        Generate sitemap.xml dynamically

        Includes:
        - Static pages (home, catalog, channels, contact, etc.)
        - Public routes only
        """
        base_url = SeoService.get_base_url()

        # Static pages with priority
        pages = [
            {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
            {'loc': '/catalog', 'priority': '0.9', 'changefreq': 'weekly'},
            {'loc': '/channels', 'priority': '0.9', 'changefreq': 'daily'},
            {'loc': '/about', 'priority': '0.7', 'changefreq': 'monthly'},
            {'loc': '/contact', 'priority': '0.7', 'changefreq': 'monthly'},
            {'loc': '/legal', 'priority': '0.5', 'changefreq': 'yearly'},
            {'loc': '/privacy', 'priority': '0.5', 'changefreq': 'yearly'},
        ]

        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        for page in pages:
            url = urljoin(base_url, page['loc'])
            sitemap += '  <url>\n'
            sitemap += f'    <loc>{url}</loc>\n'
            sitemap += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
            sitemap += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
            sitemap += f'    <priority>{page["priority"]}</priority>\n'
            sitemap += '  </url>\n'

        sitemap += '</urlset>'

        return sitemap

    @staticmethod
    def get_meta_tags(page_slug):
        """
        Get meta tags for a page from database

        Args:
            page_slug: Page identifier (e.g., 'home', 'catalog')

        Returns:
            Dict with meta tags or defaults
        """
        from models.settings import SeoSetting

        seo = SeoSetting.query.filter_by(page_slug=page_slug).first()

        if seo:
            return {
                'meta_title': seo.meta_title or f'Mon IPTV Africa — {page_slug}',
                'meta_description': seo.meta_description or 'Service IPTV de qualité en Afrique',
                'og_title': seo.og_title or seo.meta_title or 'Mon IPTV Africa',
                'og_description': seo.og_description or seo.meta_description,
                'og_image': seo.og_image_url,
                'og_type': seo.og_type or 'website',
                'canonical': seo.canonical_url,
                'robots': seo.robots_directive or 'index, follow'
            }

        # Default meta tags
        defaults = {
            'home': {
                'meta_title': 'Mon IPTV Africa — Service IPTV Premium',
                'meta_description': 'Accédez à des centaines de chaînes TV en streaming. Service IPTV fiable et rapide.',
                'og_type': 'website'
            },
            'catalog': {
                'meta_title': 'Catalogue Mon IPTV Africa — Nos Offres',
                'meta_description': 'Découvrez tous nos offres IPTV: testeurs, abonnements, packs spécialisés.',
                'og_type': 'website'
            },
            'channels': {
                'meta_title': 'Chaînes Mon IPTV Africa — Programme Complet',
                'meta_description': 'Liste complète des chaînes TV disponibles sur Mon IPTV Africa.',
                'og_type': 'website'
            }
        }

        default = defaults.get(page_slug, {})

        return {
            'meta_title': default.get('meta_title', 'Mon IPTV Africa'),
            'meta_description': default.get('meta_description', 'Service IPTV Premium en Afrique'),
            'og_title': default.get('meta_title', 'Mon IPTV Africa'),
            'og_description': default.get('meta_description', ''),
            'og_image': None,
            'og_type': default.get('og_type', 'website'),
            'canonical': None,
            'robots': 'index, follow'
        }

    @staticmethod
    def validate_meta_tags(meta_dict):
        """
        Validate meta tag input

        Args:
            meta_dict: Dictionary with meta tag values

        Returns:
            Tuple (is_valid, errors)
        """
        errors = []

        if meta_dict.get('meta_title'):
            if len(meta_dict['meta_title']) > 60:
                errors.append('Meta title max 60 caractères')
            if len(meta_dict['meta_title']) < 10:
                errors.append('Meta title min 10 caractères')

        if meta_dict.get('meta_description'):
            if len(meta_dict['meta_description']) > 160:
                errors.append('Meta description max 160 caractères')
            if len(meta_dict['meta_description']) < 20:
                errors.append('Meta description min 20 caractères')

        if meta_dict.get('og_image_url'):
            if not meta_dict['og_image_url'].startswith(('http://', 'https://')):
                errors.append('URL de l\'image invalide')

        if meta_dict.get('canonical_url'):
            if not meta_dict['canonical_url'].startswith(('http://', 'https://', '/')):
                errors.append('URL canonique invalide')

        return (len(errors) == 0, errors)
