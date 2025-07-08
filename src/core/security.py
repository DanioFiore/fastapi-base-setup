"""
Security utilities for JWT token creation, verification, 
password hashing, and password strength validation.

This module provides functions to:
- Create and verify JWT access and refresh tokens.
- Hash and verify passwords using bcrypt.
- Validate password strength according to configurable requirements.
- Generate token pairs (access and refresh) for authentication workflows.
- Refresh access tokens using valid refresh tokens.

Dependencies:
    - fastapi
    - jose
    - passlib
    - core.config (for application settings)

Functions:
    - create_access_token: Generate a JWT access token.
    - create_refresh_token: Generate a JWT refresh token.
    - verify_token: Decode and validate a JWT token.
    - get_password_hash: Hash a plain text password.
    - verify_password: Check a plain password against its hash.
    - validate_password_strength: Ensure password meets security requirements.
    - create_token_pair: Generate both access and refresh tokens for a user.
    - refresh_access_token: Issue a new access token from a valid refresh token.

"""
from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify

    Returns:
        The decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password

    Returns:
        The hashed password
    """

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """

    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength based on configured requirements.

    Args:
        password: The password to validate

    Returns:
        True if password meets requirements

    Raises:
        HTTPException: If password doesn't meet requirements
    """

    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long",
        )

    if not any(char.isdigit() for char in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit",
        )

    if not any(char.isupper() for char in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter",
        )

    if not any(char.islower() for char in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter",
        )

    if not any(char in settings.PASSWORD_SPECIAL_CHARS for char in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
            "Password must contain at least one special character: "
            f"{settings.PASSWORD_SPECIAL_CHARS}"
            ),
        )

    return True


def create_token_pair(user_data: dict) -> dict:
    """
    Create both access and refresh tokens for a user.

    Args:
        user_data: User data to encode in tokens

    Returns:
        Dictionary containing access_token, refresh_token, and token_type
    """

    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(data=user_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_access_token(refresh_token: str) -> str:
    """
    Create a new access token from a valid refresh token.

    Args:
        refresh_token: The refresh token

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        # Remove refresh token specific data
        user_data = {k: v for k, v in payload.items() if k not in ["exp", "type"]}

        # Create new access token
        return create_access_token(data=user_data)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc
