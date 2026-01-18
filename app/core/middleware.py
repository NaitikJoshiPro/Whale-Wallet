"""
Custom middleware for Whale Wallet.

Provides:
- Request logging with correlation IDs
- Rate limiting per user/IP
- Mobile app attestation verification
"""

import time
import uuid
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests with timing and correlation IDs.
    
    Adds X-Request-ID header to all responses for tracing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Bind request context to logger
        log = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )
        
        # Time the request
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            log.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            log.error(
                "Request failed",
                error=str(e),
                duration_ms=round(duration_ms, 2)
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting.
    
    In production, this should use Redis for distributed rate limiting.
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/ready", "/health/live"]:
            return await call_next(request)
        
        # Get client identifier (prefer user ID if authenticated, else IP)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests and get recent count
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id] 
                if t > window_start
            ]
        else:
            self.requests[client_id] = []
        
        if len(self.requests[client_id]) >= self.max_requests:
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                requests=len(self.requests[client_id])
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after_seconds": self.window_seconds
                },
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Record this request
        self.requests[client_id].append(now)
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from auth header (JWT)
        # For now, fall back to IP
        if request.client:
            return request.client.host
        return "unknown"


class AttestationMiddleware(BaseHTTPMiddleware):
    """
    Verify mobile app attestation before processing requests.
    
    Ensures that requests come from genuine, untampered Whale Wallet
    mobile apps by verifying cryptographic attestation tokens.
    
    Only enabled in production environments.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip attestation for non-sensitive endpoints
        exempt_paths = [
            "/health",
            "/docs",
            "/openapi.json",
            "/api/v1/auth/register",  # Allow registration without attestation
        ]
        
        if any(request.url.path.startswith(p) for p in exempt_paths):
            return await call_next(request)
        
        # Check for attestation header
        attestation_token = request.headers.get("X-Attestation-Token")
        
        if not attestation_token:
            logger.warning(
                "Missing attestation token",
                path=request.url.path
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": "attestation_required",
                    "message": "This endpoint requires mobile app attestation"
                }
            )
        
        # Verify attestation token
        # In production, this would call the TEE attestation service
        # to verify the token cryptographically
        is_valid = await self._verify_attestation(attestation_token)
        
        if not is_valid:
            logger.warning(
                "Invalid attestation token",
                path=request.url.path
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": "attestation_failed",
                    "message": "Mobile app attestation verification failed"
                }
            )
        
        return await call_next(request)
    
    async def _verify_attestation(self, token: str) -> bool:
        """
        Verify attestation token with TEE verification service.
        
        In production, this would:
        1. Decode the attestation token
        2. Verify the signature using the platform's public key
        3. Check that the app hash matches expected values
        4. Verify the token hasn't expired
        """
        # Placeholder - always return True in development
        # In production, implement actual verification
        return True
