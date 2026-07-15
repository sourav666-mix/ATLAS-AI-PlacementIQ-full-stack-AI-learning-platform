# backend/app/services/auth_service.py
"""
Auth business logic (DB-aware, no HTTP concerns).

Functions raise plain ValueError for domain problems (e.g. duplicate email);
the router translates those into HTTP responses. This keeps services reusable
outside of FastAPI (scripts, tests, other services).
"""
import secrets
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.jwt_utils import hash_password, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    return await db.get(User, user_id)


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a new student account. Raises ValueError if the email is taken."""
    existing = await get_user_by_email(db, user_in.email)
    if existing is not None:
        raise ValueError("An account with this email already exists.")

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_google_user(
    db: AsyncSession, email: str, full_name: Optional[str] = None
) -> User:
    """Return the user for a verified Google sign-in, creating one on first login.

    Google accounts have no local password, so a random unguessable one is
    stored; the user can still only sign in via Google (or a future reset).
    """
    user = await get_user_by_email(db, email)
    if user is not None:
        if not user.is_verified:
            user.is_verified = True
            await db.commit()
            await db.refresh(user)
        return user

    user = User(
        email=email,
        hashed_password=hash_password(secrets.token_urlsafe(32)),
        full_name=full_name,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Return the user on valid credentials, else None."""
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


__all__ = ["get_user_by_email", "get_user_by_id", "create_user", "authenticate_user", "get_or_create_google_user"]