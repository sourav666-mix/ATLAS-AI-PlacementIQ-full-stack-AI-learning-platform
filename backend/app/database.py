# backend/app/database.py
"""
Async SQLAlchemy 2.0 setup for MySQL (asyncmy driver).

Exposes:
    Base                -> declarative base every model inherits from
    engine              -> the async engine
    AsyncSessionLocal   -> async session factory
    get_db()            -> FastAPI dependency yielding a session

Usage in a router:

    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database import get_db

    @router.get("/things")
    async def list_things(db: AsyncSession = Depends(get_db)):
        ...
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Shared declarative base. Every model in app/models inherits this."""
    pass


# echo=DEBUG prints SQL in development; pool_pre_ping avoids stale connections.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,     # keep attributes usable after commit
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, always closed."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()