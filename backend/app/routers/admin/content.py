# content.py - CRUD topics/subtopics/questions; draft->publish; AI regenerate
# FILE: app/routers/admin/content.py
# BATCH 16 (new) - Admin content surface.
# Role rules (v10 Project Guide §8):
#   * super_admin  -> full CRUD + QA queue + Regenerate with AI
#   * college_admin -> READ-ONLY view of the curriculum
# Admin JWT (scope=admin) enforced by Batch 15 dependencies; student tokens 403.

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.admin_content import (
    ArenaReviewAction, QuestionStatusAction, RegenerateRequest,
    ReorderRequest, RowPayload,
)
from app.services import content_admin_service as content
from app.services import question_admin_service as questions
from app.services.admin_auth_service import require_admin_role, require_super_admin

router = APIRouter(prefix="/admin/content", tags=["admin-content"])


# ---------------------------------------------------------------------------
# READ (any admin — college_admin gets a read-only curriculum view)
# ---------------------------------------------------------------------------
@router.get("/tree")
async def get_tree(db: AsyncSession = Depends(get_db),
                   admin=Depends(require_admin_role)):
    return await content.content_tree(db)


@router.get("/domains")
async def get_domains(db: AsyncSession = Depends(get_db),
                      admin=Depends(require_admin_role)):
    return await content.list_domains(db)


@router.get("/phases")
async def get_phases(domain_id: Optional[str] = Query(default=None),
                     db: AsyncSession = Depends(get_db),
                     admin=Depends(require_admin_role)):
    return await content.list_phases(db, domain_id=domain_id)


@router.get("/topics")
async def get_topics(domain_id: Optional[str] = Query(default=None),
                     phase_id: Optional[str] = Query(default=None),
                     parent_id: Optional[str] = Query(default=None),
                     top_level_only: bool = Query(default=False),
                     db: AsyncSession = Depends(get_db),
                     admin=Depends(require_admin_role)):
    return await content.list_topics(db, domain_id=domain_id, phase_id=phase_id,
                                     parent_id=parent_id,
                                     top_level_only=top_level_only)


@router.get("/topics/{topic_id}/content")
async def get_topic_content(topic_id: str,
                            db: AsyncSession = Depends(get_db),
                            admin=Depends(require_admin_role)):
    return await content.get_topic_content(db, topic_id)


@router.get("/questions")
async def get_questions(topic_id: Optional[str] = Query(default=None),
                        status: Optional[str] = Query(default=None),
                        limit: int = Query(default=50, ge=1, le=200),
                        offset: int = Query(default=0, ge=0),
                        db: AsyncSession = Depends(get_db),
                        admin=Depends(require_admin_role)):
    return await questions.list_questions(db, topic_id=topic_id, status=status,
                                          limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# WRITE — DOMAINS / PHASES / TOPICS / SUBTOPICS (super_admin only)
# ---------------------------------------------------------------------------
@router.post("/domains", status_code=201)
async def post_domain(payload: RowPayload,
                      db: AsyncSession = Depends(get_db),
                      admin=Depends(require_super_admin)):
    return await content.create_domain(db, admin,
                                       payload.model_dump(exclude_unset=True))


@router.put("/domains/{domain_id}")
async def put_domain(domain_id: str, payload: RowPayload,
                     db: AsyncSession = Depends(get_db),
                     admin=Depends(require_super_admin)):
    return await content.update_domain(db, admin, domain_id,
                                       payload.model_dump(exclude_unset=True))


@router.delete("/domains/{domain_id}")
async def remove_domain(domain_id: str,
                        db: AsyncSession = Depends(get_db),
                        admin=Depends(require_super_admin)):
    return await content.delete_domain(db, admin, domain_id)


@router.post("/phases", status_code=201)
async def post_phase(payload: RowPayload,
                     db: AsyncSession = Depends(get_db),
                     admin=Depends(require_super_admin)):
    return await content.create_phase(db, admin,
                                      payload.model_dump(exclude_unset=True))


@router.put("/phases/{phase_id}")
async def put_phase(phase_id: str, payload: RowPayload,
                    db: AsyncSession = Depends(get_db),
                    admin=Depends(require_super_admin)):
    return await content.update_phase(db, admin, phase_id,
                                      payload.model_dump(exclude_unset=True))


@router.delete("/phases/{phase_id}")
async def remove_phase(phase_id: str,
                       db: AsyncSession = Depends(get_db),
                       admin=Depends(require_super_admin)):
    return await content.delete_phase(db, admin, phase_id)


@router.post("/topics", status_code=201)
async def post_topic(payload: RowPayload,
                     db: AsyncSession = Depends(get_db),
                     admin=Depends(require_super_admin)):
    return await content.create_topic(db, admin,
                                      payload.model_dump(exclude_unset=True))


@router.put("/topics/{topic_id}")
async def put_topic(topic_id: str, payload: RowPayload,
                    db: AsyncSession = Depends(get_db),
                    admin=Depends(require_super_admin)):
    return await content.update_topic(db, admin, topic_id,
                                      payload.model_dump(exclude_unset=True))


@router.delete("/topics/{topic_id}")
async def remove_topic(topic_id: str,
                       db: AsyncSession = Depends(get_db),
                       admin=Depends(require_super_admin)):
    return await content.delete_topic(db, admin, topic_id)


@router.post("/topics/reorder")
async def post_reorder(payload: ReorderRequest,
                       db: AsyncSession = Depends(get_db),
                       admin=Depends(require_super_admin)):
    return await content.reorder_topics(
        db, admin, [item.model_dump() for item in payload.items])


@router.put("/topics/{topic_id}/content")
async def put_topic_content(topic_id: str, payload: RowPayload,
                            db: AsyncSession = Depends(get_db),
                            admin=Depends(require_super_admin)):
    return await content.upsert_topic_content(
        db, admin, topic_id, payload.model_dump(exclude_unset=True))


# ---------------------------------------------------------------------------
# WRITE — QUESTIONS + draft->publish + Regenerate with AI (super_admin only)
# ---------------------------------------------------------------------------
@router.post("/questions", status_code=201)
async def post_question(payload: RowPayload,
                        db: AsyncSession = Depends(get_db),
                        admin=Depends(require_super_admin)):
    return await questions.create_question(
        db, admin, payload.model_dump(exclude_unset=True))


@router.put("/questions/{question_id}")
async def put_question(question_id: str, payload: RowPayload,
                       db: AsyncSession = Depends(get_db),
                       admin=Depends(require_super_admin)):
    return await questions.update_question(
        db, admin, question_id, payload.model_dump(exclude_unset=True))


@router.delete("/questions/{question_id}")
async def remove_question(question_id: str,
                          db: AsyncSession = Depends(get_db),
                          admin=Depends(require_super_admin)):
    return await questions.delete_question(db, admin, question_id)


@router.post("/questions/status")
async def post_question_status(payload: QuestionStatusAction,
                               db: AsyncSession = Depends(get_db),
                               admin=Depends(require_super_admin)):
    return await questions.set_question_status(db, admin,
                                               payload.ids, payload.action)


@router.post("/questions/{question_id}/regenerate")
async def post_regenerate(question_id: str, payload: RegenerateRequest,
                          db: AsyncSession = Depends(get_db),
                          admin=Depends(require_super_admin)):
    """Deliberate Type-B exception: ONE gateway call, saved back as a DRAFT."""
    return await questions.regenerate_question(
        db, admin, question_id, instructions=payload.instructions)


# ---------------------------------------------------------------------------
# ARENA QA QUEUE (super_admin only)
# ---------------------------------------------------------------------------
@router.get("/arena/queue")
async def get_arena_queue(status: Optional[str] = Query(default=None),
                          limit: int = Query(default=50, ge=1, le=200),
                          offset: int = Query(default=0, ge=0),
                          db: AsyncSession = Depends(get_db),
                          admin=Depends(require_super_admin)):
    return await questions.arena_queue(db, status=status,
                                       limit=limit, offset=offset)


@router.post("/arena/{problem_id}/review")
async def post_arena_review(problem_id: str, payload: ArenaReviewAction,
                            db: AsyncSession = Depends(get_db),
                            admin=Depends(require_super_admin)):
    return await questions.arena_review(db, admin, problem_id, payload.action)


@router.put("/arena/{problem_id}")
async def put_arena_problem(problem_id: str, payload: RowPayload,
                            db: AsyncSession = Depends(get_db),
                            admin=Depends(require_super_admin)):
    return await questions.arena_update(
        db, admin, problem_id, payload.model_dump(exclude_unset=True))


@router.delete("/arena/{problem_id}")
async def remove_arena_problem(problem_id: str,
                               db: AsyncSession = Depends(get_db),
                               admin=Depends(require_super_admin)):
    return await questions.arena_delete(db, admin, problem_id)