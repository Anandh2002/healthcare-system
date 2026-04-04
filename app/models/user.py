# app/models/user.py

# This class IS the users table.
# Every class attribute = a column in the table.
# SQLAlchemy reads this class and knows exactly how to create the table.


import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum

# Python enum for user roles
# Using an enum prevents typos — you can't accidentally set role="adminn"
class UserRole(str, enum.Enum):
    patient = "patient"
    doctor  = "doctor"
    staff   = "staff"
    admin   = "admin"


class User(Base):
    # __tablename__ tells SQLAlchemy what to name the table in PostgreSQL

    __tablename__ = "users"

    # Primary key — UUID is better than integer for security
    # (you can't guess other users' IDs by incrementing)
    # server_default uses PostgreSQL's own gen_random_uuid() function

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # Email — unique so no two users share the same email
    # index=True creates a B-tree index for fast lookups
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Phone — optional (nullable=True means it can be empty)
    phone: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # Role — uses our Python enum above
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.patient,
    )

    # Account status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Timestamps — always use timezone-aware datetimes
    # server_default means PostgreSQL sets this automatically
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # Soft delete — instead of actually deleting a user,
    # we set this timestamp. deleted_at = None means active.
    # This preserves appointment history even if a user "deletes" their account.
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

