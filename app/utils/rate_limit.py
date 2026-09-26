"""
A minimal, dependency-free rate limiter suitable for a single-process dev/
demo deployment. It keeps a rolling request-timestamp window per client IP
in memory. For a multi-process production deployment, swap this for a
Redis-backed limiter (e.g. `slowapi` + Redis) — see README bonus-features
section.
"""
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = self._hits[client_ip]

        while window and now - window[0] > self.window_seconds:
            window.popleft()

        if len(window) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again shortly."},
            )

        window.append(now)
        return await call_next(request)
