# app/schemas/auth.py

# Pydantic schemas are like "contracts" for your API.
# They define exactly what shape the data must be in.
# FastAPI uses these to:
#   1. Validate incoming request data automatically
#   2. Serialize outgoing response data
#   3. Generate the API docs at /docs

from pydantic import BaseModel, EmailStr, field_validator
import re
from uuid import UUID


class RegisterRequest(BaseModel):
    """What the client sends when registering."""
    email: EmailStr              # Pydantic validates email format automatically
    password: str
    phone: str | None = None    # optional field

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        """
        Validate password strength before it even reaches our endpoint.
        Pydantic calls this automatically when the request comes in.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Remove spaces and dashes for storage
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not cleaned.isdigit():
            raise ValueError("Phone must contain only digits")
        return cleaned


class LoginRequest(BaseModel):
    """What the client sends when logging in."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """What we send back after successful login/register."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    """What the client sends to get a new access token."""
    refresh_token: str


class UserResponse(BaseModel):
    """Safe user data we return — notice NO hashed_password field!"""
    id: UUID   
    email: str
    phone: str | None
    role: str
    is_active: bool
    is_verified: bool

    # This tells Pydantic to read data from SQLAlchemy model attributes
    # Without this, Pydantic only reads from plain dicts
    model_config = {"from_attributes": True}