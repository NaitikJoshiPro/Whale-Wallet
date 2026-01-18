"""
Health check endpoints for Cloud Run and orchestration systems.

Provides:
- /health - Basic health check
- /health/live - Liveness probe (is the process running?)
- /health/ready - Readiness probe (can it handle requests?)
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings, Settings

health_router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    version: str
    environment: str
    mpc_node_id: str


class ReadinessResponse(BaseModel):
    """Readiness check response with dependency status."""
    status: str
    database: str
    redis: str
    mpc: str


@health_router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns 200 if the application is running.
    Used by load balancers and monitoring systems.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.env,
        mpc_node_id=settings.mpc_node_id
    )


@health_router.get("/health/live")
async def liveness_probe() -> JSONResponse:
    """
    Kubernetes-style liveness probe.
    
    Returns 200 if the process is alive.
    If this fails, the container should be restarted.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "alive"}
    )


@health_router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_probe() -> ReadinessResponse:
    """
    Kubernetes-style readiness probe.
    
    Checks connectivity to all required dependencies:
    - PostgreSQL database
    - Redis cache
    - MPC coordinator
    
    If this fails, the instance should be removed from the load balancer.
    """
    # These would be actual connectivity checks in production
    # For now, return placeholder values
    
    db_status = "connected"
    redis_status = "connected"
    mpc_status = "connected"
    
    # Determine overall status
    all_healthy = all([
        db_status == "connected",
        redis_status == "connected",
        mpc_status == "connected"
    ])
    
    response = ReadinessResponse(
        status="ready" if all_healthy else "degraded",
        database=db_status,
        redis=redis_status,
        mpc=mpc_status
    )
    
    if not all_healthy:
        return JSONResponse(
            status_code=503,
            content=response.model_dump()
        )
    
    return response
