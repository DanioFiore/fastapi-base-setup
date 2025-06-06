from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from db.config import Base
from typing import List
from sqlmodel import SQLModel
from datetime import datetime
from pydantic import EmailStr, Field, model_validator, field_validator
from core.security import get_password_hash, verify_password


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=1) 
    is_superuser = Column(Boolean, default=0) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def set_password(self, password: str):
        """Hash and set the user's password"""
        self.password_hash = get_password_hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        return verify_password(password, str(self.password_hash))


class UserResponse(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListSchema(SQLModel):
    data: List[UserResponse]
    count: int


# Base schema with shared validators
class UserValidation(SQLModel):
    """Base schema with shared validation logic"""
    
    @field_validator('username', check_fields=False)
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Additional username validation - alphanumeric and underscore only"""
        if v and not v.replace('_', '').isalnum():
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v

    @field_validator('password', check_fields=False)
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Add password strength validation"""
        if v:  # Only validate if password is provided
            if not any(char.isdigit() for char in v):
                raise ValueError("Password must contain at least one digit")
            if not any(char.isupper() for char in v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(char.islower() for char in v):
                raise ValueError("Password must contain at least one lowercase letter")
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Validate that password and confirm_password fields match"""
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match")
        return self


class UserCreateSchema(UserValidation):
    username: str = Field(..., min_length=3, max_length=50, description="Username must be 3-50 characters")
    email: EmailStr = Field(..., description="Valid email address required")
    password: str = Field(..., min_length=8, max_length=100, description="Password must be at least 8 characters")
    confirm_password: str = Field(..., description="Confirm password must match password field")
    is_active: bool = True
    is_superuser: bool = False


class UserUpdateSchema(UserValidation):
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8, max_length=100, description="New password (optional)")
    confirm_password: str = Field(..., description="Confirm password must match password field")
    is_active: bool | None = None
    is_superuser: bool | None = None
