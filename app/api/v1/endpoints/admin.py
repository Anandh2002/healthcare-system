# app/api/v1/endpoints/admin.py

# These are admin-only endpoints.
# Every single route here uses Depends(get_current_admin)
# which means:
#   1. Token must be valid
#   2. User must have role = "admin"
# If either fails → request is rejected before your code runs.

import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_admin
from app.repositories.user_repo import UserRepository
from app.schemas.user import (
    UserResponse,
    UserListResponse,
    UpdateRoleRequest,
    UpdateStatusRequest,
)
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users (admin only)",
)
async def list_users(
    # Query parameters for pagination and filtering
    # These come from the URL: /admin/users?page=1&page_size=20&role=patient
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    role: str | None = Query(default=None, description="Filter by role"),

    # These two lines protect the endpoint:
    # 1. get_current_admin validates token AND checks role=admin
    # 2. get_db provides the database session
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated list of all users.
    Only accessible by admins.
    """
    from app.models.user import UserRole

    # Convert role string to enum if provided
    role_filter = None
    if role:
        try:
            role_filter = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Choose from: {[r.value for r in UserRole]}"
            )

    # Calculate skip (offset) from page number
    # Page 1 → skip 0, Page 2 → skip 20, Page 3 → skip 40
    skip = (page - 1) * page_size

    user_repo = UserRepository(db)
    users, total = await user_repo.get_all(
        skip=skip,
        limit=page_size,
        role=role_filter,
    )

    return UserListResponse(
        data=users,
        total=total,
        page=page,
        page_size=page_size,
        # math.ceil(23/20) = 2 pages for 23 records
        pages=math.ceil(total / page_size) if total > 0 else 1,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get a specific user (admin only)",
)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get any user's details by ID."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Change a user's role (admin only)",
)
async def update_user_role(
    user_id: str,
    data: UpdateRoleRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Promote or demote a user's role.

    Example uses:
    - Promote a patient to staff
    - Promote a staff to admin
    - Demote a doctor to patient
    """
    user_repo = UserRepository(db)

    # Prevent admin from changing their own role
    # (could accidentally lock themselves out)
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updated_user = await user_repo.update_role(user_id, data.role)
    return updated_user


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="Activate or deactivate a user (admin only)",
)
async def update_user_status(
    user_id: str,
    data: UpdateStatusRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate or deactivate a user account.

    Deactivated users:
    - Cannot login (login returns 403)
    - Cannot use their existing tokens (get_current_user rejects them)
    - Their data is preserved (soft disable, not delete)
    """
    user_repo = UserRepository(db)

    # Prevent admin from deactivating themselves
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updated_user = await user_repo.set_active(user_id, data.is_active)
    return updated_user