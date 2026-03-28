"""Application and SEO settings models"""
from config.database import db
from datetime import datetime
import json

class AppSetting(db.Model):
    """Application settings key-value store"""
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')  # string, integer, boolean, json
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def get_value(self):
        """Get value with proper type conversion"""
        if self.value_type == 'integer':
            return int(self.value) if self.value else 0
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            return json.loads(self.value) if self.value else {}
        return self.value

    def __repr__(self):
        return f'<AppSetting {self.key}>'


class SeoSetting(db.Model):
    """SEO settings for pages"""
    __tablename__ = 'seo_settings'

    id = db.Column(db.Integer, primary_key=True)
    page_slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.String(500), nullable=True)
    og_title = db.Column(db.String(255), nullable=True)
    og_description = db.Column(db.String(500), nullable=True)
    og_image_url = db.Column(db.String(512), nullable=True)
    og_type = db.Column(db.String(50), default='website')
    canonical_url = db.Column(db.String(512), nullable=True)
    robots_directive = db.Column(db.String(50), default='index, follow')
    schema_markup = db.Column(db.JSON, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f'<SeoSetting {self.page_slug}>'
