# auth.py - POST /auth/register /login ; GET /auth/me
# backend/app/routers/auth.py
"""
Auth routes (mounted at /auth in main.py).

    POST /auth/signup  -> create account, returns a JWT (auto-login)
    POST /auth/login   -> returns a JWT
    POST /auth/google  -> verify a Google ID token, create-or-login, returns a JWT
    GET  /auth/me      -> current user (requires Bearer token)
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import GoogleLogin, Token, UserCreate, UserLogin, UserOut
from app.services import auth_service
from app.utils.jwt_utils import create_access_token
from app.utils.validators import normalize_email

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

router = APIRouter()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.create_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return Token(access_token=create_access_token(user.id))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.post("/google", response_model=Token)
async def google_login(payload: GoogleLogin, db: AsyncSession = Depends(get_db)):
    """Exchange a Google Identity Services ID token for an ATLAS JWT.

    First-time Google users get an account created automatically (no
    password step), so this covers both "easy login" and "easy signup".
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured on the server.",
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                GOOGLE_TOKENINFO_URL, params={"id_token": payload.credential}
            )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Google to verify the sign-in. Try again.",
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential.",
        )

    claims = resp.json()
    if claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google credential was issued for a different app.",
        )
    if claims.get("email_verified") not in (True, "true"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified.",
        )

    email = normalize_email(claims["email"])
    user = await auth_service.get_or_create_google_user(
        db, email, full_name=claims.get("name")
    )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated."
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
async def read_me(current_user: User = Depends(get_current_active_user)):
    return current_user