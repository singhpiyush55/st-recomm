"""
Simple in-memory cache with TTL.
Stores fetcher results to avoid hitting rate limits.
For production, swap this dict for Redis.
"""

from __future__ import annotations

import time
from typing import Any, Optional

DEFAULT_TTL = 60 * 60 * 24  # 24 hours in seconds


class InMemoryCache:
    """Thread-safe-ish in-memory cache with per-key TTL."""

    def __init__(self, default_ttl: int = DEFAULT_TTL) -> None:
        self._store: dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if it exists and hasn't expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value with a TTL (seconds). Defaults to 24 h."""
        ttl = ttl if ttl is not None else self._default_ttl
        self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Drop everything."""
        self._store.clear()

    def size(self) -> int:
        """Number of (possibly expired) entries."""
        return len(self._store)


# Module-level singleton — import this everywhere
cache = InMemoryCache()
