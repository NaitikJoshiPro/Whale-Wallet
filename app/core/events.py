"""
Application lifecycle event handlers.

Manages database connections, cache clients, and other
resources that need to be initialized at startup and
cleaned up at shutdown.
"""

from typing import Callable

import structlog
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import redis.asyncio as redis

from app.config import get_settings

logger = structlog.get_logger(__name__)


def create_start_app_handler(app: FastAPI) -> Callable:
    """
    Create the startup event handler.
    
    Initializes:
    - Database connection pool
    - Redis connection pool
    - Vector database client (if enabled)
    - MPC coordinator connection
    """
    
    async def start_app() -> None:
        settings = get_settings()
        
        # === Database Engine (graceful - don't fail if unavailable) ===
        try:
            logger.info("Connecting to PostgreSQL", host=settings.db_host)
            
            engine = create_async_engine(
                settings.database_url,
                echo=settings.debug,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Store engine in app state for dependency injection
            app.state.db_engine = engine
            app.state.db_session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Verify connection
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            logger.info("PostgreSQL connection established")
            app.state.db_connected = True
        except Exception as e:
            logger.warning("PostgreSQL connection failed - running without database", error=str(e))
            app.state.db_connected = False
        
        # === Redis Connection (graceful) ===
        try:
            logger.info("Connecting to Redis", host=settings.redis_host)
            
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            app.state.redis = redis_client
            
            # Verify connection
            await redis_client.ping()
            logger.info("Redis connection established")
            app.state.redis_connected = True
        except Exception as e:
            logger.warning("Redis connection failed - running without cache", error=str(e))
            app.state.redis_connected = False
        
        # === Vector Database (if enabled) ===
        if settings.enable_ai_concierge and settings.vector_db_provider == "pinecone":
            logger.info("Initializing Pinecone vector database")
            # Pinecone initialization would go here
            pass
        
        # === MPC Coordinator ===
        logger.info("Initializing MPC coordinator", node_id=settings.mpc_node_id)
        # MPC coordinator initialization would go here
        
        logger.info(
            "Application startup complete",
            environment=settings.env,
            features={
                "duress_mode": settings.enable_duress_mode,
                "inheritance": settings.enable_inheritance,
                "ai_concierge": settings.enable_ai_concierge
            }
        )
    
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """
    Create the shutdown event handler.
    
    Gracefully closes:
    - Database connection pool
    - Redis connection pool
    - Any open MPC sessions
    """
    
    async def stop_app() -> None:
        logger.info("Beginning graceful shutdown")
        
        # Close Redis connection
        if hasattr(app.state, "redis"):
            await app.state.redis.close()
            logger.info("Redis connection closed")
        
        # Close database engine
        if hasattr(app.state, "db_engine"):
            await app.state.db_engine.dispose()
            logger.info("PostgreSQL connection pool closed")
        
        logger.info("Application shutdown complete")
    
    return stop_app
