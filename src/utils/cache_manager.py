"""
Cache Manager Implementation

Manages caching for safety layer operations.
"""

import time
from typing import Dict, Any, Optional
from collections import OrderedDict


class CacheManager:
    """Simple cache manager for safety layer operations."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize cache manager."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "total_requests": 0}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        self.stats["total_requests"] += 1

        if key not in self.cache:
            self.stats["misses"] += 1
            return None

        value, timestamp = self.cache[key]

        # Check if entry has expired
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            self.stats["misses"] += 1
            return None

        # Move to end (LRU)
        self.cache.move_to_end(key)
        self.stats["hits"] += 1
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Remove if already exists
        if key in self.cache:
            del self.cache[key]

        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1

        # Add new entry
        self.cache[key] = (value, time.time())

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = self.stats["hits"] / max(1, self.stats["total_requests"])

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "total_requests": self.stats["total_requests"],
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "total_requests": 0}

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        expired_keys = []

        for key, (value, timestamp) in self.cache.items():
            if current_time - timestamp > self.ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)
