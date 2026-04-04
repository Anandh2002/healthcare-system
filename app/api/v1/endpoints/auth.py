# app/api/v1/endpoints/auth.py

# The router is the final layer — it receives HTTP requests
# and hands them to the service layer.
# It should be thin — no business logic here.
# Just: receive → validate → call service → return response

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)
from app.models.user import User

# All routes in this router will be prefixed with /auth
# and grouped under "auth" in the docs
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,  # 201 = Created (more accurate than 200 for new resources)
    summary="Register a new patient account",
)
async def register(
    data: RegisterRequest,           # FastAPI reads + validates the request body
    db: AsyncSession = Depends(get_db),  # DB session injected automatically
):
    """
    Register a new patient.
    Returns access and refresh tokens on success.
    """
    service = AuthService(db)
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    service = AuthService(db)
    return await service.login(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Get new tokens using refresh token",
)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a refresh token for a new token pair."""
    service = AuthService(db)
    return await service.refresh_token(data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged-in user info",
)
async def get_me(
    # get_current_user runs first — validates token, fetches user from DB
    # if token is invalid it returns 401 before this code runs
    current_user: User = Depends(get_current_user),
):
    """
    Returns the profile of the currently authenticated user.
    This is a protected route — requires a valid access token.
    """
    return current_user