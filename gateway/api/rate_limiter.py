"""
NEXUS Ingestion Rate Limiter
Token-bucket rate limiting per device and globally to protect the gateway from denial of service.
"""

import time
import threading
from typing import Dict


class TokenBucketRateLimiter:
    def __init__(self, rate_per_sec: float = 1000.0, burst: float = 2000.0):
        self.rate = rate_per_sec
        self.burst = burst
        self._lock = threading.Lock()
        self._tokens: Dict[str, float] = {}
        self._last_update: Dict[str, float] = {}

    def is_allowed(self, client_id: str, cost: float = 1.0) -> bool:
        now = time.monotonic()
        with self._lock:
            last = self._last_update.get(client_id, now)
            tokens = self._tokens.get(client_id, self.burst)

            # Refill tokens based on elapsed time
            elapsed = now - last
            tokens = min(self.burst, tokens + elapsed * self.rate)
            self._last_update[client_id] = now

            if tokens >= cost:
                self._tokens[client_id] = tokens - cost
                return True
            else:
                self._tokens[client_id] = tokens
                return False


rate_limiter = TokenBucketRateLimiter(rate_per_sec=5000.0, burst=10000.0)
