"""
User API routing module.

This module defines the FastAPI routes for user management, including endpoints to
list users, retrieve a single user, create a new user, update an existing user, and
delete a user. All endpoints use dependency injection for database sessions and
handle API exceptions via a custom decorator.

Routes:
    GET     /           - List all users.
    GET     /{user_id}  - Retrieve a user by ID.
    POST    /           - Create a new user.
    PUT     /{user_id}  - Update an existing user.
    DELETE  /{user_id}  - Delete a user by ID.

Dependencies:
    - FastAPI APIRouter for route definitions.
    - SQLModel Session for database operations.
    - Custom exception handler decorator.
    - User models and schemas for request/response validation.

"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from core.utility.decorators import handle_api_exceptions
from db.session import get_session

from .models import (User, UserCreateSchema, UserListSchema, UserResponse,
                    UserUpdateSchema)

router = APIRouter()


@router.get("/")
@handle_api_exceptions
def read_users(session: Session = Depends(get_session)):
    """List all users in the system."""
    query = select(User)
    result = session.exec(query).all()

    return UserListSchema(
        data=[UserResponse.model_validate(user) for user in result], count=len(result)
    )


@router.get("/{user_id}")
@handle_api_exceptions
def get_user(user_id: int, session: Session = Depends(get_session)):
    """Retrieve a user by their ID."""
    user = session.get(User, user_id)
    if not user:
        return None  # Triggers not found response

    return UserResponse.model_validate(user)


@router.post("/")
@handle_api_exceptions
def create_user(payload: UserCreateSchema, session: Session = Depends(get_session)):
    """Create a new user in the system."""
    data = payload.model_dump(exclude={"password", "confirm_password"})
    user = User(**data)
    user.set_password(payload.password)  # Hash the password
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserResponse.model_validate(user)


@router.put("/{user_id}")
@handle_api_exceptions
def update_user(
    user_id: int, payload: UserUpdateSchema, session: Session = Depends(get_session)
):
    """Update an existing user by their ID."""
    user = session.get(User, user_id)
    if not user:
        return None  # Triggers not found response

    data = payload.model_dump(exclude_unset=True, exclude={"password"})

    # Handle password separately if provided
    if payload.password is not None:
        user.set_password(payload.password)

    # Update other fields
    for key, value in data.items():
        setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
@handle_api_exceptions
def delete_user(user_id: int, session: Session = Depends(get_session)):
    """Delete a user by their ID."""
    user = session.get(User, user_id)
    if not user:
        return None  # Triggers not found response

    session.delete(user)
    session.commit()

    return {"message": "User deleted successfully"}
