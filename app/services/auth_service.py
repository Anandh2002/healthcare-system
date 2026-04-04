# app/services/auth_service.py

# The service layer contains business logic.
# It answers questions like:
#   "Is this user allowed to do this?"
#   "What should happen when a user registers?"
#   "Is this password correct?"
#
# It uses the repository for DB access and
# security utils for hashing/JWT.


from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.user_repo import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.models.user import User


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db
        # Service creates its own repository instance
        self.user_repo = UserRepository(db)

    
    async def register(self, data: RegisterRequest) -> TokenResponse:
        """
        Register a new patient account.
        
        Steps:
        1. Check email not already taken
        2. Hash the password
        3. Create user in DB
        4. Return JWT tokens (log them in immediately after register)
        """

        # Step 1 — check email uniqueness
        # We check this in the service layer (not just DB constraint)
        # so we can return a friendly error message
        if await self.user_repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        # Step 2 — hash the password
        # NEVER pass the plain password to the repository
        hashed = hash_password(data.password)

        # Step 3 — create user
        user = await self.user_repo.create(
            email=data.email,
            hashed_password=hashed,
            phone=data.phone,
        )

        # Step 4 — generate tokens and return
        # User is registered AND logged in in one step
        return self._generate_tokens(user)

    
    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Login with email and password.
        
        Steps:
        1. Find user by email
        2. Verify password against stored hash
        3. Check account is active
        4. Return JWT tokens
        
        IMPORTANT: Steps 1 and 2 give the SAME error message
        intentionally — never tell attackers whether the email
        exists or the password is wrong. "Invalid credentials" only.
        """

        # Step 1 — find user
        user = await self.user_repo.get_by_email(data.email)

        # Step 2 — verify password
        # We do BOTH checks before returning error
        # This prevents "timing attacks" where attackers can tell
        # if an email exists based on response speed
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",  # always the same message
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Step 3 — check account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Contact support.",
            )

        # Step 4 — generate and return tokens
        return self._generate_tokens(user)

    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Use a valid refresh token to get a new access token.
        
        This is called when the access token expires (after 15 min).
        The client sends the refresh token and gets a fresh pair back.
        """
        # Decode and validate the refresh token
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Make sure it's actually a refresh token, not an access token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Get the user from DB to make sure they still exist and are active
        user = await self.user_repo.get_by_id(payload.get("sub"))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return self._generate_tokens(user)


    def _generate_tokens(self, user: User) -> TokenResponse:
        """
        Private helper — creates both tokens for a user.
        Called after successful register, login, or refresh.
        """
        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )