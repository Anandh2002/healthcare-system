# app/api/v1/endpoints/users.py

# These endpoints are for any logged-in user
# managing their OWN profile.
# Notice the difference from admin.py:
#   admin.py  → manages OTHER users (admin only)
#   users.py  → manages YOUR OWN profile (any logged-in user)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserResponse
from app.schemas.auth import UserResponse as AuthUserResponse
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])


class UpdateProfileRequest(BaseModel):
    """What a user can update on their own profile."""
    phone: str | None = None


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get my profile",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the currently logged-in user's profile.
    No DB query needed — current_user is already fetched
    by get_current_user dependency.
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update my profile",
)
async def update_my_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update your own profile.
    Users can only update their own data — not other users'.
    Role changes are NOT allowed here — only admins can change roles.
    """
    # Only update fields that were actually provided
    if data.phone is not None:
        current_user.phone = data.phone
        db.add(current_user)

    return current_user