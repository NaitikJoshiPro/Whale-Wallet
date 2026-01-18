"""
API v1 Router Aggregation

Combines all v1 API routes into a single router
for clean mounting in the main application.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.wallet import router as wallet_router
from app.api.v1.policy import router as policy_router
from app.api.v1.transaction import router as transaction_router
from app.api.v1.concierge import router as concierge_router

api_router = APIRouter()

# Mount all v1 routers with their prefixes
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    wallet_router,
    prefix="/wallet",
    tags=["Wallet"]
)

api_router.include_router(
    policy_router,
    prefix="/policies",
    tags=["Policy Engine"]
)

api_router.include_router(
    transaction_router,
    prefix="/transactions",
    tags=["Transactions"]
)

api_router.include_router(
    concierge_router,
    prefix="/concierge",
    tags=["AI Concierge"]
)
