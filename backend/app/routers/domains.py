# backend/app/routers/domains.py
"""
Domain catalogue routes (mounted at /domains).

    GET /domains          -> list active career domains
    GET /domains/{slug}   -> one domain with its phases + topics
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.catalog import DomainDetailOut, DomainOut, PhaseOut, TopicOut
from app.services import catalog_service

router = APIRouter()


@router.get("", response_model=List[DomainOut])
async def list_domains(db: AsyncSession = Depends(get_db)):
    return await catalog_service.list_domains(db)


@router.get("/{slug}", response_model=DomainDetailOut)
async def get_domain(slug: str, db: AsyncSession = Depends(get_db)):
    domain = await catalog_service.get_domain_by_slug(db, slug)
    if domain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    phases = await catalog_service.get_domain_phases(db, domain.id)
    topics = await catalog_service.get_domain_topics(db, domain.id)

    # Validate ONLY the scalar domain fields (DomainOut has no relationships),
    # then attach the separately-queried lists — avoids async lazy-loading
    # domain.phases / domain.topics off the ORM object.
    base = DomainOut.model_validate(domain)
    return DomainDetailOut(
        **base.model_dump(),
        phases=[PhaseOut.model_validate(p) for p in phases],
        topics=[TopicOut.model_validate(t) for t in topics],
    )