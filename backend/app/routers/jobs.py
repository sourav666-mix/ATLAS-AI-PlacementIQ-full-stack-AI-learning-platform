# jobs.py - [NEW] GET /jobs (match scores) ; save/status tracking
# backend/app/routers/jobs.py
"""Jobs & Internships Board — student endpoints.

  GET  /jobs?type=&q=&min_match=   -> board with personal match scores
  GET  /jobs/tracker               -> application pipeline (kanban)
  GET  /jobs/{id}                  -> full detail (+ 'close the gap' when < 60%)
  POST /jobs/{id}/save             -> add to tracker (stage=saved)
  POST /jobs/{id}/status           -> advance the pipeline

There is intentionally NO posting endpoint here — students can never create a
job (zero-spam-by-design). Posting lives in the role-gated admin router.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.jobs import (
    JobDetail,
    JobListResponse,
    TrackerBoard,
    TrackerItem,
    TrackingUpdate,
)
from app.services import jobs_service

router = APIRouter(prefix="/jobs", tags=["Jobs Board"])


@router.get("", response_model=JobListResponse)
@router.get("/", response_model=JobListResponse, include_in_schema=False)
async def list_jobs(
    type: Optional[str] = Query(None, description="job | internship"),
    q: Optional[str] = Query(None, description="search title/company"),
    min_match: int = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cards = await jobs_service.list_jobs(db, user, kind=type, q=q, min_match=min_match)
    return JobListResponse(count=len(cards), jobs=cards)


# declared before "/{job_id}" so "tracker" isn't captured as an id
@router.get("/tracker", response_model=TrackerBoard)
async def my_tracker(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await jobs_service.get_tracker(db, user)


@router.get("/{job_id}", response_model=JobDetail)
async def job_detail(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await jobs_service.get_detail(db, user, job_id)


@router.post("/{job_id}/save", response_model=JobDetail)
async def save_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await jobs_service.save_job(db, user, job_id)


@router.post("/{job_id}/status", response_model=TrackerItem)
async def update_status(
    job_id: str,
    payload: TrackingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await jobs_service.update_stage(db, user, job_id, payload.stage)