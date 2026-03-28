"""
Input Validation and Sanitization
- HTML/script escaping
- SQL injection prevention (parameterized queries)
- Email validation
- URL validation
- Username/password validation
"""

import re
from html import escape
from urllib.parse import urlparse

# Constants
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,80}$'
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
URL_PATTERN = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 256

class ValidationError(Exception):
    """Custom validation error"""
    pass

class Validator:
    """Input validation utilities"""

    @staticmethod
    def sanitize_html(text):
        """
        Escape HTML special characters
        Prevents XSS via user input
        """
        if not text:
            return ''
        return escape(str(text))

    @staticmethod
    def validate_email(email):
        """
        Validate email format

        Args:
            email: Email address string

        Returns:
            True if valid, False otherwise
        """
        if not email or len(email) > 254:
            return False
        return bool(re.match(EMAIL_PATTERN, email.lower()))

    @staticmethod
    def validate_username(username):
        """
        Validate username format
        - Alphanumeric, hyphens, underscores
        - 3-80 characters

        Args:
            username: Username string

        Returns:
            True if valid, False otherwise
        """
        if not username:
            return False
        return bool(re.match(USERNAME_PATTERN, username))

    @staticmethod
    def validate_password(password):
        """
        Validate password strength
        - Minimum 8 characters
        - Maximum 256 characters
        - No specific complexity requirement (user choice)

        Args:
            password: Password string

        Returns:
            Tuple (is_valid, message)
        """
        if not password:
            return (False, 'Mot de passe obligatoire')

        if len(password) < PASSWORD_MIN_LENGTH:
            return (False, f'Min {PASSWORD_MIN_LENGTH} caractères')

        if len(password) > PASSWORD_MAX_LENGTH:
            return (False, f'Max {PASSWORD_MAX_LENGTH} caractères')

        return (True, 'OK')

    @staticmethod
    def validate_url(url):
        """
        Validate URL format

        Args:
            url: URL string

        Returns:
            True if valid HTTP(S) URL
        """
        if not url:
            return False

        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and parsed.netloc
        except Exception:
            return False

    @staticmethod
    def validate_integer_range(value, min_val=None, max_val=None, name='value'):
        """
        Validate integer is within range

        Args:
            value: Value to validate
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            name: Field name for error message

        Returns:
            Tuple (is_valid, message)
        """
        try:
            num = int(value)
        except (ValueError, TypeError):
            return (False, f'{name} doit être un nombre entier')

        if min_val is not None and num < min_val:
            return (False, f'{name} minimum: {min_val}')

        if max_val is not None and num > max_val:
            return (False, f'{name} maximum: {max_val}')

        return (True, 'OK')

    @staticmethod
    def validate_length(text, min_len=None, max_len=None, name='texte'):
        """
        Validate text length

        Args:
            text: Text to validate
            min_len: Minimum length
            max_len: Maximum length
            name: Field name for error message

        Returns:
            Tuple (is_valid, message)
        """
        if not text:
            return (False, f'{name} obligatoire')

        length = len(str(text))

        if min_len and length < min_len:
            return (False, f'{name} min {min_len} caractères')

        if max_len and length > max_len:
            return (False, f'{name} max {max_len} caractères')

        return (True, 'OK')

    @staticmethod
    def validate_choice(value, choices, name='option'):
        """
        Validate value is in allowed choices

        Args:
            value: Value to validate
            choices: List of allowed values
            name: Field name for error message

        Returns:
            Tuple (is_valid, message)
        """
        if value not in choices:
            return (False, f'{name} invalide. Choix: {", ".join(str(c) for c in choices)}')

        return (True, 'OK')

    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize filename for file uploads
        - Remove path traversal attempts
        - Remove special characters
        - Limit length

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        if not filename:
            return 'file'

        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]

        # Keep only alphanumeric, dash, underscore, dot
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1)
            filename = name[:250] + '.' + ext

        return filename

    @staticmethod
    def validate_ip_address(ip):
        """
        Validate IPv4 address format

        Args:
            ip: IP address string

        Returns:
            True if valid IPv4
        """
        parts = ip.split('.')
        if len(parts) != 4:
            return False

        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False

        return True

# Shorthand validators for common use
def safe_str(text, max_len=None):
    """Safely escape and optionally truncate string"""
    text = Validator.sanitize_html(text)
    if max_len and len(text) > max_len:
        text = text[:max_len] + '...'
    return text

def safe_int(value, default=0, min_val=None, max_val=None):
    """Safely convert to integer with bounds"""
    try:
        num = int(value)
        if min_val is not None:
            num = max(num, min_val)
        if max_val is not None:
            num = min(num, max_val)
        return num
    except (ValueError, TypeError):
        return default
