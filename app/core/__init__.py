"""Core module initialization."""

from app.core.events import create_start_app_handler, create_stop_app_handler
from app.core.middleware import (
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    AttestationMiddleware
)

__all__ = [
    "create_start_app_handler",
    "create_stop_app_handler",
    "RequestLoggingMiddleware",
    "RateLimitMiddleware",
    "AttestationMiddleware"
]
