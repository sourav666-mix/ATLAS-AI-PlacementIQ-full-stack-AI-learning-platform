# FILE: app/services/question_admin_service.py
# BATCH 16 (new) - Question bank admin:
#   * CRUD on topic_questions (25-question sets)
#   * draft -> publish -> flag workflow (review_status column, v10 ALTER)
#   * "Regenerate with AI" — the DELIBERATE Type-B exception (admin-only,
#     one gateway call, result saved back as a DRAFT for human review)
#   * Arena QA queue — review 'auto' generated arena_problems before students
#     keep seeing them (approve / flag / edit)
#
# AI gateway convention (non-negotiable):
#   from app.services.ai_provider_router import complete as ask_ai, parse_json
# (admin_common.call_ai wraps `complete`; parse_json is used directly here.)

from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin_common import (
    apply_fields, audit, call_ai, col, column_names, parse_json,
    require_model, row_get, to_dict,
)

T_QUESTIONS = "topic_questions"
T_ARENA = "arena_problems"

VALID_STATUSES = {"draft", "published", "auto", "flagged"}
_ACTION_TO_STATUS = {"publish": "published", "draft": "draft", "flag": "flagged"}

# Candidate column names per logical field (defensive mapping)
_FIELD_COLS = {
    "question": ("question", "question_text", "prompt", "statement", "text"),
    "model_answer": ("model_answer", "answer", "solution", "correct_answer"),
    "why": ("why", "why_text", "reveal_why"),
    "how": ("how", "how_text", "reveal_how", "derivation"),
    "example": ("example", "example_text", "reveal_example"),
    "common_mistakes": ("common_mistakes", "mistakes", "reveal_common_mistakes"),
}

REGEN_SYSTEM = (
    "You are a senior curriculum author for ATLAS AI, a placement-prep platform "
    "for Indian B.Tech students. You rewrite a single practice question and its "
    "full reveal content. Return STRICT JSON only — no markdown, no preamble."
)

REGEN_TEMPLATE = """Rewrite/improve this practice question. Keep the same topic, \
difficulty and question_kind unless the admin instructions say otherwise.

CURRENT QUESTION (JSON):
{current}

ADMIN INSTRUCTIONS: {instructions}

Return STRICT JSON with exactly these keys:
{{"question": "...", "model_answer": "...", "why": "...", "how": "...", \
"example": "...", "common_mistakes": "..."}}"""


def _status_col(model):
    return col(model, "review_status", "status")


# ---------------------------------------------------------------------------
# topic_questions CRUD
# ---------------------------------------------------------------------------
async def list_questions(db: AsyncSession, topic_id: Optional[str] = None,
                         status: Optional[str] = None,
                         limit: int = 50, offset: int = 0) -> dict:
    Question = require_model(T_QUESTIONS)
    stmt = select(Question)
    count_stmt = select(func.count()).select_from(Question)
    fk = col(Question, "topic_id", "subtopic_id")
    if topic_id and fk is not None:
        stmt = stmt.where(fk == topic_id)
        count_stmt = count_stmt.where(fk == topic_id)
    scol = _status_col(Question)
    if status and scol is not None:
        stmt = stmt.where(scol == status)
        count_stmt = count_stmt.where(scol == status)
    order = col(Question, "sort_order", "order_index", "position", "created_at", "id")
    if order is not None:
        stmt = stmt.order_by(order)
    total = int((await db.execute(count_stmt)).scalar() or 0)
    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    return {"total": total, "limit": limit, "offset": offset,
            "items": [to_dict(r) for r in rows]}


async def create_question(db: AsyncSession, admin, payload: dict) -> dict:
    Question = require_model(T_QUESTIONS)
    cols = column_names(Question)
    data = dict(payload or {})
    if "id" in cols and not data.get("id"):
        data["id"] = str(uuid.uuid4())
    # New admin-authored questions start as drafts unless explicitly published
    if "review_status" in cols and not data.get("review_status"):
        data["review_status"] = "draft"
    row = Question()
    apply_fields(row, data)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.create_question", T_QUESTIONS,
                row_get(row, "id"), {"topic_id": data.get("topic_id")})
    return to_dict(row)


async def update_question(db: AsyncSession, admin, question_id: str,
                          payload: dict) -> dict:
    Question = require_model(T_QUESTIONS)
    row = await db.get(Question, question_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Question not found")
    applied = apply_fields(row, payload)
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.update_question", T_QUESTIONS,
                question_id, {"fields": sorted(applied.keys())})
    return to_dict(row)


async def delete_question(db: AsyncSession, admin, question_id: str) -> dict:
    Question = require_model(T_QUESTIONS)
    row = await db.get(Question, question_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Question not found")
    await db.delete(row)
    await db.commit()
    await audit(db, admin, "content.delete_question", T_QUESTIONS, question_id)
    return {"deleted": question_id}


async def set_question_status(db: AsyncSession, admin,
                              ids: list, action: str) -> dict:
    """Bulk draft -> publish -> flag transitions."""
    new_status = _ACTION_TO_STATUS.get(action)
    if new_status is None:
        raise HTTPException(status_code=422,
                            detail=f"action must be one of {sorted(_ACTION_TO_STATUS)}")
    Question = require_model(T_QUESTIONS)
    scol = _status_col(Question)
    if scol is None:
        raise HTTPException(status_code=500,
                            detail="topic_questions has no review_status column")
    status_name = scol.key if hasattr(scol, "key") else "review_status"
    changed = []
    for qid in ids:
        row = await db.get(Question, qid)
        if row is not None:
            setattr(row, status_name, new_status)
            changed.append(qid)
    await db.commit()
    await audit(db, admin, f"content.question_{action}", T_QUESTIONS, None,
                {"ids": changed, "status": new_status})
    return {"action": action, "status": new_status, "updated": changed}


# ---------------------------------------------------------------------------
# "Regenerate with AI" — deliberate Type-B exception (ONE call, saved as draft)
# ---------------------------------------------------------------------------
async def regenerate_question(db: AsyncSession, admin, question_id: str,
                              instructions: Optional[str] = None) -> dict:
    Question = require_model(T_QUESTIONS)
    row = await db.get(Question, question_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Question not found")

    current = {logical: row_get(row, *cands)
               for logical, cands in _FIELD_COLS.items()}
    current["difficulty"] = row_get(row, "difficulty", "level")
    current["question_kind"] = row_get(row, "question_kind", "kind", "type")

    prompt = REGEN_TEMPLATE.format(
        current=json.dumps(current, ensure_ascii=False, default=str),
        instructions=(instructions or "General quality improvement."),
    )
    raw = await call_ai(prompt, system=REGEN_SYSTEM)
    try:
        data = parse_json(raw)
    except Exception:
        raise HTTPException(status_code=502,
                            detail="AI returned unparseable JSON; try again")
    if not isinstance(data, dict) or not data.get("question"):
        raise HTTPException(status_code=502,
                            detail="AI response missing 'question'; not saved")

    cols = column_names(Question)
    applied = {}
    for logical, candidates in _FIELD_COLS.items():
        value = data.get(logical)
        if value is None:
            continue
        for cand in candidates:
            if cand in cols:
                setattr(row, cand, value)
                applied[cand] = True
                break
    # Regenerated content ALWAYS lands as a draft for human review
    if "review_status" in cols:
        row.review_status = "draft"
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.regenerate_question_ai", T_QUESTIONS,
                question_id, {"fields": sorted(applied.keys()),
                              "instructions": instructions})
    return to_dict(row)


# ---------------------------------------------------------------------------
# Arena QA queue — review 'auto' generated arena problems
# ---------------------------------------------------------------------------
async def arena_queue(db: AsyncSession, status: Optional[str] = None,
                      limit: int = 50, offset: int = 0) -> dict:
    Arena = require_model(T_ARENA)
    scol = _status_col(Arena)
    source = col(Arena, "source")
    stmt = select(Arena)
    count_stmt = select(func.count()).select_from(Arena)
    if status and scol is not None:
        cond = scol == status
    elif scol is not None:
        # Default queue = everything not yet published. Approved items leave.
        cond = scol.in_(["auto", "draft", "flagged"])
    elif source is not None:
        cond = source == "auto"
    else:
        cond = None
    if cond is not None:
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    order = col(Arena, "created_at", "id")
    if order is not None:
        stmt = stmt.order_by(order.desc() if hasattr(order, "desc") else order)
    total = int((await db.execute(count_stmt)).scalar() or 0)
    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    return {"total": total, "limit": limit, "offset": offset,
            "items": [to_dict(r) for r in rows]}


async def arena_review(db: AsyncSession, admin, problem_id: str,
                       action: str) -> dict:
    new_status = _ACTION_TO_STATUS.get(action)
    if new_status is None:
        raise HTTPException(status_code=422,
                            detail=f"action must be one of {sorted(_ACTION_TO_STATUS)}")
    Arena = require_model(T_ARENA)
    row = await db.get(Arena, problem_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Arena problem not found")
    scol = _status_col(Arena)
    if scol is None:
        raise HTTPException(status_code=500,
                            detail="arena_problems has no review_status column")
    setattr(row, scol.key if hasattr(scol, "key") else "review_status", new_status)
    await db.commit()
    await audit(db, admin, f"content.arena_{action}", T_ARENA, problem_id,
                {"status": new_status})
    return to_dict(row)


async def arena_update(db: AsyncSession, admin, problem_id: str,
                       payload: dict) -> dict:
    Arena = require_model(T_ARENA)
    row = await db.get(Arena, problem_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Arena problem not found")
    applied = apply_fields(row, payload)
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.arena_update", T_ARENA, problem_id,
                {"fields": sorted(applied.keys())})
    return to_dict(row)


async def arena_delete(db: AsyncSession, admin, problem_id: str) -> dict:
    Arena = require_model(T_ARENA)
    row = await db.get(Arena, problem_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Arena problem not found")
    await db.delete(row)
    await db.commit()
    await audit(db, admin, "content.arena_delete", T_ARENA, problem_id)
    return {"deleted": problem_id}