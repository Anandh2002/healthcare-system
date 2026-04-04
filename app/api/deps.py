# app/api/deps.py
# Full updated file — replace everything

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.session import AsyncSessionLocal
from app.core.security import decode_token
from app.repositories.user_repo import UserRepository
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provides a DB session to each request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates the JWT token and returns the current user.
    Used by all protected endpoints.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please login first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use access token.",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload.get("sub"))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact support.",
        )

    return user


async def get_current_active_patient(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Shortcut dependency — only allows patients.
    Use this instead of require_role(UserRole.patient) for cleaner code.
    """
    if current_user.role != UserRole.patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access this resource.",
        )
    return current_user


async def get_current_active_doctor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Shortcut dependency — only allows doctors."""
    if current_user.role != UserRole.doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access this resource.",
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Shortcut dependency — only allows admins."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


def require_role(*roles: UserRole):
    """
    Flexible dependency factory for multiple roles.

    Examples:
        Depends(require_role(UserRole.admin))
        Depends(require_role(UserRole.doctor, UserRole.admin))
        Depends(require_role(UserRole.patient, UserRole.staff, UserRole.admin))
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. "
                    f"Your role '{current_user.role.value}' is not allowed here. "
                    f"Required: {[r.value for r in roles]}"
                ),
            )
        return current_user
    return role_checker