# backend/app/routers/arena.py
"""
Code Arena Pro routes (mounted at /arena).

    GET  /arena/problems             -> browse the bank (filter by category/difficulty)
    GET  /arena/next                 -> next unsolved problem in a cell (generates if empty)
    GET  /arena/problems/{id}        -> problem detail (no hidden tests / solution)
    POST /arena/problems/{id}/submit -> run code, AI review, award first-pass points
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.arena import ProblemDetail, ProblemSummary, RunIn, SubmitIn, SubmitResult
from app.services import arena_service

router = APIRouter()


@router.get("/problems", response_model=List[ProblemSummary])
async def list_problems(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await arena_service.list_problems(db, category, difficulty)


@router.get("/next", response_model=ProblemDetail)
async def next_problem(
    category: str = Query(...),
    difficulty: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    prob = await arena_service.next_problem(db, current_user.id, category, difficulty)
    if prob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No problems available for this cell.")
    return arena_service.public_view(prob)


@router.get("/problems/{problem_id}", response_model=ProblemDetail)
async def get_problem(problem_id: str, db: AsyncSession = Depends(get_db)):
    prob = await arena_service.get_problem(db, problem_id)
    if prob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    return arena_service.public_view(prob)


@router.post("/run")
async def run(
    payload: RunIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Run visible tests only — fast feedback, no points, no AI review."""
    try:
        return await arena_service.run_visible(db, payload.problem_id, payload.language, payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/problems/{problem_id}/submit", response_model=SubmitResult)
async def submit(
    problem_id: str,
    payload: SubmitIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await arena_service.submit(db, current_user.id, problem_id, payload.language, payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))