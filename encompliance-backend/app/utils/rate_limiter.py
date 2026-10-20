"""
Simple sliding-window rate limiter for in-process throttling.
"""

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, DefaultDict


class RateLimitExceeded(Exception):
    """Raised when a caller exceeds the configured request budget."""


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._events: DefaultDict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> None:
        """Record a call for the provided key and enforce the limit."""
        now = time.time()
        with self._lock:
            window = self._events[key]
            cutoff = now - window_seconds
            while window and window[0] < cutoff:
                window.popleft()

            if len(window) >= limit:
                raise RateLimitExceeded(f"Rate limit exceeded for {key}")

            window.append(now)


rate_limiter = SlidingWindowRateLimiter()

