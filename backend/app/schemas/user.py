# user.py - UserCreate, UserResponse, Token
# backend/app/schemas/user.py
"""
Pydantic request/response models for auth + user identity.

Request models validate input; response models (from_attributes=True) serialize
ORM objects. Passwords never appear in any response model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.utils.validators import normalize_email, validate_password_strength


# --- requests ---------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def _norm_email(cls, v: str) -> str:
        return normalize_email(v)

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class GoogleLogin(BaseModel):
    """Google Identity Services ID token (the `credential` from the GIS button)."""
    credential: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _norm_email(cls, v: str) -> str:
        return normalize_email(v)


# --- responses --------------------------------------------------------------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: Optional[str] = None
    profile_bar_score: int
    is_active: bool
    is_verified: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT contents we care about."""
    sub: Optional[str] = None


__all__ = ["UserCreate", "UserLogin", "GoogleLogin", "UserOut", "Token", "TokenPayload"]