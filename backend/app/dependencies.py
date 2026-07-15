# backend/app/dependencies.py
"""
Shared FastAPI dependencies.

get_current_user  -> decodes the Bearer JWT and loads the User (401 on failure).
get_current_active_user -> above + rejects deactivated accounts (400).

Every protected router imports these:
    from app.dependencies import get_current_active_user
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services import auth_service
from app.utils.jwt_utils import JWTError, decode_access_token

# Sends the standard "Authorization: Bearer <token>" header; also powers the
# "Authorize" button in /docs.
_bearer = HTTPBearer(auto_error=True)

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _credentials_exc

    user_id = payload.get("sub")
    if not user_id:
        raise _credentials_exc

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise _credentials_exc
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive account")
    return current_user


__all__ = ["get_current_user", "get_current_active_user"]