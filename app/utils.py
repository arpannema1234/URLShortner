import string
import random
import re
from urllib.parse import urlparse


def generate_short_code(length=6):
    """Generate a random short code of specified length using alphanumeric characters."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def is_valid_url(url):
    """Validate if the provided URL is properly formatted."""
    try:
        result = urlparse(url)
        # Check if it has scheme and netloc, and the netloc contains at least a dot
        if not all([result.scheme, result.netloc]):
            return False
        if result.scheme not in ['http', 'https']:
            return False
        # Basic check for domain format (must contain at least one dot)
        if '.' not in result.netloc:
            return False
        return True
    except Exception:
        return False


def normalize_url(url):
    """Normalize URL by ensuring it has a proper scheme."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url