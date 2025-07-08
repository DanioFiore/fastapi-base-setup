"""
Authentication models for the API.

This module defines Pydantic models used for authentication-related API endpoints,
including login, logout, and token refresh operations. These models provide request
and response validation for authentication flows.

The models include:
- LoginRequest: Validates user login credentials
- LoginResponse: Returns authentication tokens and user data after login
- RefreshTokenRequest: Validates refresh token requests
- RefreshTokenResponse: Returns new access tokens
- LogoutResponse: Confirms successful logout operations

All models use Pydantic for automatic validation and serialization, ensuring
type safety and proper data structure for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr

from api.users.models import UserResponse


class LoginRequest(BaseModel):
    """
    Request model for user login authentication.

    This model validates the structure of login requests, ensuring that
    the email field contains a valid email address and the password
    is provided as a string.

    Attributes:
        email (EmailStr): The user's email address, validated for proper format
        password (str): The user's password in plain text (will be hashed during processing)
    """

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """
    Response model for user login authentication.

    This model represents the response data returned after a successful user login,
    containing authentication tokens and user information.

    Attributes:
        access_token (str): JWT access token for authenticating API requests.
        refresh_token (str): JWT refresh token for obtaining new access tokens.
        token_type (str): The type of token (typically 'bearer').
        user (UserResponse): User information and profile data.
    """

    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """
    Request model for refreshing authentication tokens.

    This model represents the payload required to refresh an expired access token
    using a valid refresh token.

    Attributes:
        refresh_token (str): The refresh token used to obtain a new access token.
                            Must be a valid, non-expired refresh token previously
                            issued by the authentication system.
    """

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """
    Response model for refresh token endpoint.

    This model represents the response structure returned when a refresh token
    is successfully used to obtain a new access token.

    Attributes:
        access_token (str): The new JWT access token that can be used for authentication.
        token_type (str): The type of token, typically "bearer" for JWT tokens.
    """

    access_token: str
    token_type: str


class LogoutResponse(BaseModel):
    """
    Response model for user logout endpoint.

    This model represents the response returned when a user successfully logs out
    of the application.

    Attributes:
        message (str): A message indicating the logout status or confirmation.
    """

    message: str
