# app/repositories/user_repo.py
# Full updated file

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.user import User, UserRole


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.patient,
        phone: str | None = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
            phone=phone,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        role: UserRole | None = None,
    ) -> tuple[list[User], int]:
        """
        Get paginated list of users with optional role filter.
        Returns (list_of_users, total_count).

        skip  = how many records to skip (for pagination)
        limit = how many records to return per page

        Page 1: skip=0,  limit=20 → records 1-20
        Page 2: skip=20, limit=20 → records 21-40
        Page 3: skip=40, limit=20 → records 41-60
        """
        # Base query — filter out soft-deleted users
        query = select(User).where(User.deleted_at.is_(None))

        # Optionally filter by role
        if role:
            query = query.where(User.role == role)

        # Count query — same filters but just counts
        # We need total for pagination metadata
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginated data query
        result = await self.db.execute(
            query.order_by(User.created_at.desc())
                 .offset(skip)
                 .limit(limit)
        )
        users = result.scalars().all()

        return list(users), total

    async def update_role(self, user_id: str, new_role: UserRole) -> User | None:
        """
        Change a user's role.
        Only admins should call this (enforced at the router level).
        """
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(role=new_role)
        )
        # Fetch and return the updated user
        return await self.get_by_id(user_id)

    async def set_active(self, user_id: str, is_active: bool) -> User | None:
        """
        Activate or deactivate a user account.
        Deactivated users can't login — their token gets rejected in get_current_user.
        """
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=is_active)
        )
        return await self.get_by_id(user_id)