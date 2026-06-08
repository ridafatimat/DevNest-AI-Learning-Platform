# app/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from collections import defaultdict
import time
from app.config import RATE_LIMIT_PER_MIN

# Very simple in-memory rate limiter per IP (demo purpose only)
class SimpleRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, calls_per_min=RATE_LIMIT_PER_MIN):
        super().__init__(app)
        self.calls_per_min = calls_per_min
        self.store = defaultdict(list)  # ip -> list[timestamps]

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60
        timestamps = self.store[ip]
        # purge old
        while timestamps and timestamps[0] < window_start:
            timestamps.pop(0)
        if len(timestamps) >= self.calls_per_min:
            return JSONResponse({"detail": "Too many requests"}, status_code=429)
        timestamps.append(now)
        self.store[ip] = timestamps
        return await call_next(request)
