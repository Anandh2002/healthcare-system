# app/schemas/user.py

# These schemas define what data looks like
# when going IN (requests) and OUT (responses)
# for user-related endpoints.

from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserRole
import uuid


class UserResponse(BaseModel):
    """
    Safe user data returned to clients.
    Notice: NO hashed_password field — never expose this.
    """
    id: uuid.UUID
    email: str
    phone: str | None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """
    Paginated list of users — for admin endpoints.
    Always return pagination metadata so the frontend
    knows how many pages exist.
    """
    data: list[UserResponse]
    total: int        # total records matching the filter
    page: int         # current page number
    page_size: int    # records per page
    pages: int        # total number of pages


class UpdateRoleRequest(BaseModel):
    """Admin request to change a user's role."""
    role: UserRole


class UpdateStatusRequest(BaseModel):
    """Admin request to activate/deactivate a user."""
    is_active: bool