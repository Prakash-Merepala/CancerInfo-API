"""
Security and Rate Limiting
"""
import time
from typing import Dict, Tuple
from fastapi import Header, HTTPException, Request, status
from app.core.config import settings
from app.core.errors import RateLimitExceededError, UnauthorizedError


class InMemoryRateLimiter:
    """
    Sliding window in-memory rate limiter per IP.
    Returns (allowed: bool, limit: int, remaining: int, reset_time: int)
    """
    def __init__(self, requests_per_minute: int = 120):
        self.requests_per_minute = requests_per_minute
        self.clients: Dict[str, list[float]] = {}

    def check(self, client_ip: str) -> Tuple[bool, int, int, int]:
        now = time.time()
        window_start = now - 60.0

        if client_ip not in self.clients:
            self.clients[client_ip] = []

        # Filter out requests older than 1 minute
        self.clients[client_ip] = [t for t in self.clients[client_ip] if t > window_start]
        current_count = len(self.clients[client_ip])

        reset_time = int(window_start + 60.0 - now)
        if reset_time <= 0:
            reset_time = 60

        if current_count >= self.requests_per_minute:
            return False, self.requests_per_minute, 0, reset_time

        self.clients[client_ip].append(now)
        remaining = max(0, self.requests_per_minute - current_count - 1)
        return True, self.requests_per_minute, remaining, reset_time


rate_limiter = InMemoryRateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)


def verify_admin_key(
    x_admin_key: str = Header(None, alias="X-Admin-Key"),
    authorization: str = Header(None, alias="Authorization"),
) -> bool:
    expected_key = settings.ADMIN_API_KEY
    if not expected_key:
        raise UnauthorizedError("Admin API key is not configured on server.")

    provided = None
    if x_admin_key:
        provided = x_admin_key.strip()
    elif authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            provided = parts[1].strip()

    if not provided or provided != expected_key:
        raise UnauthorizedError("Valid administrator credentials required for this endpoint.")
    return True
