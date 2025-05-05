import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

class APIService:
    """Service for handling API requests with caching and error handling."""

    CACHE_DIR = Path("data/cache")
    CACHE_EXPIRY = 300  # 5 minutes in seconds

    def __init__(self):
        self.session = requests.Session()
        self.base_url = os.getenv("COIN_GECKO_API_URL", "https://api.binance.com/api/v3")
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, endpoint: str) -> Path:
        """Generate cache file path based on endpoint."""
        return self.CACHE_DIR / f"{endpoint.replace('/', '_')}.json"

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache is still valid."""
        if not cache_file.exists():
            return False
        return (time.time() - cache_file.stat().st_mtime) < self.CACHE_EXPIRY

    def _save_to_cache(self, cache_file: Path, data: Dict):
        """Save data to cache file."""
        with open(cache_file, 'w') as f:
            json.dump(data, f)

    def _load_from_cache(self, cache_file: Path) -> Optional[Dict]:
        """Load data from cache file."""
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make GET request to API with caching and error handling.
        
        Args:
            endpoint: API endpoint (e.g., 'coins/markets')
            params: Query parameters
            
        Returns:
            Dictionary with API response data
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        key = endpoint + json.dumps(params or {}, sort_keys=True)
        hashed = hashlib.md5(key.encode()).hexdigest()
        cache_file = self._get_cache_path(hashed)
        
        # Try to load from cache first
        if self._is_cache_valid(cache_file):
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        # Make API request if cache is invalid
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            self._save_to_cache(cache_file, data)
            return data
            
        except requests.exceptions.RequestException as e:
            # Fallback to cache if available
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                print(f"API request failed, using cached data. Error: {str(e)}")
                return cached_data
            raise   