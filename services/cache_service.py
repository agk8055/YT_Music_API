import time
from threading import Lock
from typing import Dict, Any, Optional

class CacheService:
    def __init__(self, ttl: int = 3600):
        self._cache: Dict[str, Any] = {}
        self._ttl = ttl
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._cache.get(key)
            if item and (time.time() - item['timestamp']) < self._ttl:
                return item['value']
            elif item:
                # Item has expired, remove it
                del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        with self._lock:
            self._cache[key] = {
                'value': value,
                'timestamp': time.time()
            }

    def delete(self, key: str):
        with self._lock:
            if key in self._cache:
                del self._cache[key]

# Create a global instance of the cache service
cache_service = CacheService()
