# app/core/security.py

# This file has 4 jobs:
# 1. Hash a plain password into bcrypt
# 2. Verify a plain password against a stored hash
# 3. Create a JWT access token
# 4. Create a JWT refresh token

from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

# CryptContext tells passlib WHICH algorithm to use.
# bcrypt is the industry standard for password hashing.
# "deprecated=auto" means old hashes get auto-upgraded to newer bcrypt versions.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The algorithm used to sign JWTs.
# HS256 = HMAC with SHA-256 — fast and secure for our use case.
ALGORITHM = "HS256"

def hash_password(plain_password: str) -> str:
    """
    Convert a plain text password into a bcrypt hash.
    
    Example:
        hash_password("john1234")
        → "$2b$12$Kf8sJ9xQ2mNpL..."  (always different even for same input!)
    
    The hash is different every time because bcrypt adds a random "salt".
    This means two users with the same password have different hashes.
    """
    return pwd_context.hash(plain_password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches a stored hash.
    
    Example:
        verify_password("john1234", "$2b$12$Kf8sJ9xQ2mNpL...")
        → True
        
        verify_password("wrongpass", "$2b$12$Kf8sJ9xQ2mNpL...")
        → False
    
    We NEVER decrypt the hash — bcrypt re-hashes the input and
    compares the result. This is what makes it secure.
    """
    return pwd_context.verify(plain_password, hashed_password)



def create_access_token(subject: str | Any) -> str:
    """
    Create a short-lived JWT access token.
    
    subject = the user's ID (stored inside the token)
    expire  = when this token stops working (15 minutes from now)
    
    The token looks like: "eyJhbGci...eyJzdWI...signature"
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # "payload" is the data stored inside the token
    # "sub" = subject (standard JWT claim for the user identifier)
    # "exp" = expiry (standard JWT claim — jose validates this automatically)
    # "type" = our custom claim to distinguish access from refresh tokens
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    
    # jwt.encode() signs the payload with our SECRET_KEY
    # Anyone can READ a JWT (it's just base64) but can't FAKE one
    # without knowing the SECRET_KEY
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str | Any) -> str:
    """
    Create a long-lived JWT refresh token.
    Same as access token but lives for 7 days and type="refresh".
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Raises JWTError if:
    - Token signature is invalid (tampered)
    - Token has expired
    - Token is malformed
    
    Returns the payload dict if valid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise # let the caller handle the error