# jwt_utils.py - create_token / verify_token / get_current_user (+ admin claims)
# backend/app/utils/jwt_utils.py
"""
Auth primitives: password hashing (bcrypt) + JWT encode/decode.

Pure functions with no DB access — safe to import anywhere. The DB-aware
`get_current_user` dependency lives in app/dependencies.py.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# bcrypt is pinned to 4.0.1 in requirements.txt so passlib 1.7.4 works cleanly.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- passwords --------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    # bcrypt only uses the first 72 bytes; truncate defensively to avoid errors.
    return _pwd_context.hash(plain_password[:72])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password[:72], hashed_password)


# --- JSON Web Tokens --------------------------------------------------------
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """`subject` is the user id; it becomes the token's `sub` claim."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": str(subject), "iat": now, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Return the token payload, or raise jose.JWTError if invalid/expired."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "JWTError",
]