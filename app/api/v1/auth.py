"""
Authentication API Endpoints

Handles user registration, login, and session management.
Uses JWT tokens for stateless authentication.
"""

from datetime import datetime, timedelta
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt

from app.config import get_settings, Settings

logger = structlog.get_logger(__name__)
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# === Request/Response Schemas ===

class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    device_id: str = Field(..., min_length=32, max_length=64)
    attestation_token: str | None = None


class UserRegisterResponse(BaseModel):
    """User registration response."""
    user_id: str
    tier: str
    mpc_setup_required: bool
    message: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    """User profile response."""
    user_id: str
    email: str
    tier: str
    created_at: datetime
    policies_count: int
    duress_mode_enabled: bool
    inheritance_configured: bool


# === Helper Functions ===

def create_access_token(
    data: dict,
    settings: Settings,
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiry_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    settings: Settings = Depends(get_settings)
) -> dict:
    """
    Decode JWT token and return current user.
    
    This is a dependency that can be injected into any route
    that requires authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.warning("JWT validation failed", error=str(e))
        raise credentials_exception
    
    # In production, fetch user from database here
    # For now, return a mock user
    return {
        "user_id": user_id,
        "tier": payload.get("tier", "orca"),
        "email": payload.get("email")
    }


# === API Endpoints ===

@router.post("/register", response_model=UserRegisterResponse)
async def register_user(
    request: UserRegisterRequest,
    settings: Settings = Depends(get_settings)
) -> UserRegisterResponse:
    """
    Register a new user.
    
    This initiates the MPC key generation process:
    1. Create user record
    2. Generate server-side key shard (Shard B)
    3. Return setup instructions for mobile device
    
    The mobile app will then generate Shard A in the Secure Enclave.
    """
    logger.info("User registration initiated", email=request.email)
    
    # In production:
    # 1. Verify attestation token if provided
    # 2. Check if email already exists
    # 3. Create user in database
    # 4. Initiate DKG (Distributed Key Generation) with MPC coordinator
    
    # Mock response
    return UserRegisterResponse(
        user_id="usr_" + request.device_id[:16],
        tier="orca",
        mpc_setup_required=True,
        message="Registration successful. Please complete MPC key setup in the app."
    )


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Settings = Depends(get_settings)
) -> TokenResponse:
    """
    Authenticate user and return JWT token.
    
    In production, this would:
    1. Verify biometric/PIN from mobile app
    2. Check MPC shard availability
    3. Issue short-lived access token
    """
    logger.info("Login attempt", username=form_data.username)
    
    # In production, verify credentials against database
    # For now, accept any credentials for demonstration
    
    access_token = create_access_token(
        data={
            "sub": "usr_demo123456789",
            "email": form_data.username,
            "tier": "humpback"
        },
        settings=settings
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiry_minutes * 60
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user)
) -> UserProfile:
    """
    Get the current authenticated user's profile.
    
    Returns user details, tier information, and feature status.
    """
    # In production, fetch full profile from database
    
    return UserProfile(
        user_id=current_user["user_id"],
        email=current_user.get("email", "user@example.com"),
        tier=current_user["tier"],
        created_at=datetime.utcnow(),
        policies_count=4,
        duress_mode_enabled=True,
        inheritance_configured=False
    )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Logout current user.
    
    In production, this would:
    1. Invalidate the current JWT (add to blocklist)
    2. Clear server-side session data
    3. Optional: Require re-authentication for MPC
    """
    logger.info("User logout", user_id=current_user["user_id"])
    
    return {"message": "Successfully logged out"}


@router.post("/duress-ping")
async def duress_ping(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> dict:
    """
    Silent endpoint to check if user is in duress.
    
    The mobile app can call this with a special flag to indicate
    the user is under duress. The server will then:
    1. Switch to decoy wallet mode
    2. Alert security contacts
    3. Continue responding normally to avoid detection
    
    This endpoint looks identical to a normal health check
    to prevent attackers from detecting its purpose.
    """
    if not settings.enable_duress_mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    # In production, check for duress flag in request headers
    # and trigger appropriate response
    
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
