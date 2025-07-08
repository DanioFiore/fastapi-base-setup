"""
Authentication routing module for FastAPI application.
This module provides authentication endpoints and dependencies for user authentication,
including login, logout, token refresh, and user profile management. It implements
JWT-based authentication with access and refresh tokens.
The module includes:
- JWT token-based authentication dependencies
- Login endpoint with email/password authentication
- Token refresh endpoint for access token renewal
- Logout endpoint (client-side token invalidation)
- User profile endpoints for retrieving and updating current user information
Dependencies:
- get_current_user: Extracts and validates authenticated user from JWT token
- get_current_user_optional: Optional authentication dependency that returns None if no token
Endpoints:
- POST /login: Authenticate user and return JWT tokens
- POST /refresh: Refresh access token using refresh token
- POST /logout: Logout user (client-side token removal)
- GET /me: Get current authenticated user information
- PUT /me: Update current authenticated user information
All endpoints use the @handle_api_exceptions decorator for consistent error handling.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from api.auth.models import (LoginRequest, LoginResponse, LogoutResponse,
                                 RefreshTokenRequest, RefreshTokenResponse)
from api.users.models import User, UserResponse, UserUpdateSchema
from core.security import (create_token_pair, refresh_access_token,
                               verify_token)
from core.utility.decorators import handle_api_exceptions
from db.session import get_session

router = APIRouter()
security = HTTPBearer()


# Dependency to get current user from JWT token
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        session: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.get(User, int(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Optional dependency for endpoints that may or may not require authentication
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session),
) -> Optional[User]:
    """
    Get the current user if token is provided, otherwise return None.

    Args:
        credentials: Optional HTTP Bearer token credentials
        session: Database session

    Returns:
        User object if authenticated, None otherwise
    """

    if credentials is None:
        return None

    try:
        return get_current_user(credentials, session)
    except HTTPException:
        return None


@router.post("/login")
@handle_api_exceptions
def login(login_data: LoginRequest, session: Session = Depends(get_session)):
    """
    Authenticate user and return JWT tokens.

    Args:
        login_data: Login credentials (email and password)
        session: Database session

    Returns:
        Access token, refresh token, and user information

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    query = select(User).where(User.email == login_data.email)
    user = session.exec(query).first()

    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT tokens
    user_data = {"sub": str(user.id), "username": user.username, "email": user.email}
    tokens = create_token_pair(user_data)

    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh")
@handle_api_exceptions
def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    new_access_token = refresh_access_token(refresh_data.refresh_token)
    return RefreshTokenResponse(access_token=new_access_token, token_type="bearer")


@router.post("/logout")
@handle_api_exceptions
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (client-side token invalidation).

    Note: In a stateless JWT implementation, logout is typically handled
    client-side by removing the tokens. For server-side token invalidation,
    you would need to implement a token blacklist.

    Args:
        current_user: Current authenticated user

    Returns:
        Logout confirmation message
    """
    # Here we would typically handle token invalidation on the client side
    return LogoutResponse(message="Successfully logged out")


@router.get("/me")
@handle_api_exceptions
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user information
    """
    return UserResponse.model_validate(current_user)


@router.put("/me")
@handle_api_exceptions
def update_current_user(
    user_data: UserUpdateSchema,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Update current user information.

    Args:
        user_data: Updated user data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated user information
    """
    # Update allowed fields only
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(current_user, field, value)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return UserResponse.model_validate(current_user)
