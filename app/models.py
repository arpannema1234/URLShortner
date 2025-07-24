from datetime import datetime
from threading import Lock
from typing import Dict, Optional


class URLMapping:
    """Represents a URL mapping with metadata."""
    
    def __init__(self, short_code: str, original_url: str):
        self.short_code = short_code
        self.original_url = original_url
        self.clicks = 0
        self.created_at = datetime.utcnow()
    
    def increment_clicks(self):
        """Increment the click count for this URL mapping."""
        self.clicks += 1
    
    def to_dict(self):
        """Convert the URL mapping to a dictionary."""
        return {
            'short_code': self.short_code,
            'url': self.original_url,
            'clicks': self.clicks,
            'created_at': self.created_at.isoformat()
        }


class URLStore:
    """Thread-safe in-memory store for URL mappings."""
    
    def __init__(self):
        self._mappings: Dict[str, URLMapping] = {}
        self._lock = Lock()
    
    def add_mapping(self, short_code: str, original_url: str) -> URLMapping:
        """Add a new URL mapping."""
        with self._lock:
            if short_code in self._mappings:
                raise ValueError(f"Short code '{short_code}' already exists")
            
            mapping = URLMapping(short_code, original_url)
            self._mappings[short_code] = mapping
            return mapping
    
    def get_mapping(self, short_code: str) -> Optional[URLMapping]:
        """Get a URL mapping by short code."""
        with self._lock:
            return self._mappings.get(short_code)
    
    def increment_clicks(self, short_code: str) -> bool:
        """Increment clicks for a short code. Returns True if successful, False if not found."""
        with self._lock:
            mapping = self._mappings.get(short_code)
            if mapping:
                mapping.increment_clicks()
                return True
            return False
    
    def code_exists(self, short_code: str) -> bool:
        """Check if a short code already exists."""
        with self._lock:
            return short_code in self._mappings


# Global URL store instance
url_store = URLStore()