"""
Whale Wallet - Sovereign Wealth Preservation System

A non-custodial MPC wallet designed for high-net-worth individuals,
combining institutional-grade security with personal sovereignty.

Core Features:
- 2-of-3 MPC threshold signing (Mobile + Server + Recovery)
- Programmable policy engine with velocity limits, whitelists, time locks
- Deep Duress Mode for physical security
- Sovereign Inheritance with Dead Man's Switch
- AI-powered concierge for white-glove support
"""

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.api.v1.router import api_router
from app.api.health import health_router
from app.core.events import create_start_app_handler, create_stop_app_handler
from app.core.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    AttestationMiddleware
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup (database connections, cache warming) and
    shutdown (graceful connection closing) operations.
    """
    settings = get_settings()
    
    # Startup
    logger.info(
        "Starting Whale Wallet API",
        environment=settings.env,
        mpc_node_id=settings.mpc_node_id
    )
    
    startup_handler = create_start_app_handler(app)
    await startup_handler()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Whale Wallet API")
    shutdown_handler = create_stop_app_handler(app)
    await shutdown_handler()


def create_application() -> FastAPI:
    """
    Factory function to create the FastAPI application.
    
    This pattern allows for easy testing by creating fresh
    application instances with different configurations.
    """
    import os
    from fastapi.staticfiles import StaticFiles
    from app.api.views import view_router
    
    settings = get_settings()
    
    app = FastAPI(
        title="Whale Wallet",
        description="Sovereign Wealth Preservation System for Digital Assets",
        version="1.0.0",
        docs_url="/docs",  # Always enable docs for now
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json",  # Always enable OpenAPI
        lifespan=lifespan
    )
    
    # === Middleware Stack ===
    # Order matters: first added = last executed (outer layer)
    
    # CORS - allow specified origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Development
            "http://localhost:8080",  # Local development
            "https://app.whalewallet.io",  # Production
            "https://whale-api-191939075930.us-central1.run.app",  # Cloud Run
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    
    # Compression for responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds
    )
    
    # Mobile app attestation (only in production)
    if settings.attestation_enabled:
        app.add_middleware(AttestationMiddleware)
    
    # === Static Files ===
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # === Routers ===
    app.include_router(health_router, tags=["Health"])
    app.include_router(api_router, prefix="/api/v1")
    
    # === Frontend View Routes ===
    app.include_router(view_router)
    
    return app



# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
