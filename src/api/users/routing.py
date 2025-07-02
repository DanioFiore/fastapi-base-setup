from fastapi import APIRouter, Depends
from db.session import get_session
from sqlmodel import Session, select
from .models import (
    User,
    UserResponse,
    UserListSchema,
    UserCreateSchema,
    UserUpdateSchema
)
from core.utility.decorators import handle_api_exceptions

router = APIRouter()


@router.get("/")
@handle_api_exceptions
def read_users(session: Session = Depends(get_session)):
    query = select(User)
    result = session.exec(query).all()
    
    return UserListSchema(
        data=[UserResponse.model_validate(user) for user in result],
        count=len(result)
    )



@router.get("/{user_id}")
@handle_api_exceptions
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        return None  # Triggers not found response
    
    return UserResponse.model_validate(user)
    
@router.post("/")
@handle_api_exceptions
def create_user(
    payload: UserCreateSchema,
    session: Session = Depends(get_session)
):
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
    user_id: int,
    payload: UserUpdateSchema,
    session: Session = Depends(get_session)
):
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
    user = session.get(User, user_id)
    if not user:
        return None  # Triggers not found response

    session.delete(user)
    session.commit()
    
    return {"message": "User deleted successfully"}
