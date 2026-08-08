import threading
import time


class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            timestamps = [t for t in self._hits.get(key, []) if now - t < self._window]
            if len(timestamps) >= self._max:
                self._hits[key] = timestamps
                return False
            timestamps.append(now)
            self._hits[key] = timestamps
            return True


scan_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
