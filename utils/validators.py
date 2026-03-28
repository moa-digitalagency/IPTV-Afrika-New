"""Data validation utilities"""
import re

def validate_username(username):
    """Validate M3U username format"""
    if not username or len(username) < 3:
        return False, "Le nom d'utilisateur doit avoir au moins 3 caractères"
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', username):
        return False, "Le nom d'utilisateur contient des caractères invalides"
    return True, None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(pattern, email):
        return False, "Format d'email invalide"
    return True, None

def validate_phone(phone):
    """Validate phone number format"""
    # Remove spaces and common separators
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
    if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
        return False, "Numéro de téléphone invalide"
    return True, None

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        return False, "Le mot de passe doit avoir au moins 8 caractères"
    if not any(c.isupper() for c in password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    if not any(c.isdigit() for c in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    return True, None
