import time
import hashlib
import json
from typing import Any, Optional, Callable
from functools import wraps

class CacheManager:
    def __init__(self, ttl_seconds: int = 180):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def _generate_key(self, fetcher_name: str, topics: list) -> str:
        """Generate cache key from fetcher + topics"""
        topic_names = sorted([t.name for t in topics])
        key_string = f"{fetcher_name}:{','.join(topic_names)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached data if not expired"""
        if key not in self._cache:
            return None
        
        cached_time, data = self._cache[key]
        age = time.time() - cached_time
        
        if age > self._ttl:
            del self._cache[key]  # Expired
            return None
        
        return data
    
    def set(self, key: str, data: Any):
        """Cache data with timestamp"""
        self._cache[key] = (time.time(), data)
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
# Global cache instance

trend_cache = CacheManager(ttl_seconds=180)  # 3 minutes

def cached_fetch(ttl: int = 180):
    """Decorator for caching fetch results"""
    def decorator(fetch_func: Callable):
        @wraps(fetch_func)
        def wrapper(self, topics, *args, **kwargs):
            # Generate cache key
            fetcher_name = self.__class__.__name__
            cache_key = trend_cache._generate_key(fetcher_name, topics)
            
            # Try cache
            cached = trend_cache.get(cache_key)
            if cached is not None:
                print(f"[Cache HIT] {fetcher_name}")
                return cached
            
            # Cache miss - fetch fresh
            print(f"[Cache MISS] {fetcher_name}")
            result = fetch_func(self, topics, *args, **kwargs)
            
            # Store in cache
            trend_cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator