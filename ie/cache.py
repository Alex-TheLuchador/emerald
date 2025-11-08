"""
Caching system for IE data fetchers.

This module provides a simple time-based cache with TTL (time-to-live) to reduce
redundant API calls and improve performance.

Design:
- In-memory cache (dictionary-based)
- Time-based expiration (TTL)
- Thread-safe operations
- Cache hit/miss tracking for monitoring
"""

import time
from typing import Any, Optional, Dict, Tuple
from datetime import datetime
import threading


class IECache:
    """Time-based cache for institutional engine data.

    Each cache entry has a TTL (time-to-live) in seconds. Once expired,
    the entry is considered stale and will be refetched.

    Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize empty cache with statistics tracking."""
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._sets = 0

    def get(self, key: str, ttl: int) -> Optional[Any]:
        """Retrieve cached data if still valid.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds

        Returns:
            Cached data if valid, None if expired or not found
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            data, timestamp = self._cache[key]
            age = time.time() - timestamp

            if age > ttl:
                # Expired - remove from cache
                del self._cache[key]
                self._misses += 1
                return None

            # Valid cache hit
            self._hits += 1
            return data

    def set(self, key: str, data: Any) -> None:
        """Store data in cache with current timestamp.

        Args:
            key: Cache key
            data: Data to cache
        """
        with self._lock:
            self._cache[key] = (data, time.time())
            self._sets += 1

    def invalidate(self, key: str) -> None:
        """Remove a specific key from cache.

        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache performance metrics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                'hits': self._hits,
                'misses': self._misses,
                'sets': self._sets,
                'total_requests': total_requests,
                'hit_rate_pct': hit_rate,
                'entries': len(self._cache),
            }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._sets = 0

    def cleanup_expired(self, ttl: int) -> int:
        """Remove all expired entries from cache.

        Args:
            ttl: Time-to-live threshold in seconds

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp > ttl
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)


# Global cache instance
_global_cache = IECache()


def get_cache() -> IECache:
    """Get the global IE cache instance.

    Returns:
        Global IECache instance
    """
    return _global_cache
