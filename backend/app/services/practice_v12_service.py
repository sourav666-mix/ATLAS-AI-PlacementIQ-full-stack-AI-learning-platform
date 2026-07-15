# backend/app/services/practice_v12_service.py
"""
ATLAS AI 4.0 - v12 SkillPath Reforged: PRACTICE mode
(spec Section 2, steps 5-7 + Section 6 'next question' logic).

Cost discipline:
  * get_subtopic_tabs / get_next_question / get_subtopic_progress
      -> Type A, ZERO AI calls (pure bank reads + JSON progress state).
  * generate-once-cache
      -> fires ONLY when the student has seen every question in the
         subtopic's bank. Exactly ONE AI call, and the new question is
         saved back to topic_questions with review_status='auto' so the
         next student gets it FREE from the DB. The bank grows free.

Serving order (locked): next UNSEEN question in difficulty order
basic -> medium -> advanced, position-stable within a difficulty.

Per-student-per-domain state lives in user_topic_progress.progress_json
with underscore-prefixed keys (platform convention):
  {"_seen_qids": [...], "_answered": n, "_correct": n, "_score_sum": n}
Content is shared across domains; this state never is.
"""

import json
import logging
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import RoadmapTopic
from app.models.practice import TopicQuestion
from app.models.skill_progress import UserTopicProgress
from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.services.curriculum_registry import (
    QUESTIONS_PER_SUBTOPIC,
    CORRECT_SCORE_THRESHOLD,
    MASTERY_CORRECT_THRESHOLD,
)
from app.services.skillpath_v12_service import parse_progress_json, is_mastered
from app.prompts import GENERATE_QUESTION_SYSTEM, GENERATE_QUESTION_USER

logger = logging.getLogger(__name__)

_DIFFICULTY_RANK = {"basic": 0, "medium": 1, "advanced": 2}


# ----------------------------------------------------------------------
# Shared state helpers
# ----------------------------------------------------------------------

async def get_or_create_utp(
    db: AsyncSession, user_id: str, subtopic_id: str, domain_id: str
) -> UserTopicProgress:
    """get-or-create is NOT a plain SELECT-then-INSERT here: get_next_question
    and get_subtopic_progress fire in parallel on a subtopic's first visit
    (skillPathStore.loadNextQuestion uses Promise.all), so two requests can
    both miss the SELECT and race to INSERT the same (user, topic, domain)
    row. On MySQL/InnoDB that race resolves as either a duplicate-key
    IntegrityError OR an outright deadlock (OperationalError 1213) depending
    on timing - so instead of catching either, use MySQL's atomic upsert:
    the loser's statement just becomes a no-op UPDATE instead of erroring."""
    utp = (
        await db.execute(
            select(UserTopicProgress).where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.topic_id == subtopic_id,
                UserTopicProgress.domain_id == domain_id,
            )
        )
    ).scalars().first()
    if utp is not None:
        return utp

    new_id = str(uuid.uuid4())
    stmt = mysql_insert(UserTopicProgress).values(
        id=new_id, user_id=user_id, topic_id=subtopic_id, domain_id=domain_id,
        status="in_progress", mastery_score=0,
        progress_json=json.dumps(
            {"_seen_qids": [], "_answered": 0, "_correct": 0, "_score_sum": 0}
        ),
    )
    # True no-op on conflict: `id=UserTopicProgress.id` sets the PK to its OWN
    # existing value. Using `stmt.inserted.id` (the losing row's proposed id)
    # instead would overwrite the winner's primary key on every conflict.
    stmt = stmt.on_duplicate_key_update(id=UserTopicProgress.id)
    await db.execute(stmt)
    await db.commit()

    utp = (
        await db.execute(
            select(UserTopicProgress).where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.topic_id == subtopic_id,
                UserTopicProgress.domain_id == domain_id,
            )
        )
    ).scalars().first()
    return utp


async def _bank_for_subtopic(
    db: AsyncSession, subtopic_id: str
) -> List[TopicQuestion]:
    """The published bank, difficulty-ordered, stable within difficulty.

    Shared-library topics can reuse a pre-existing RoadmapTopic row that
    matches by title (see _get_or_create_library_topic) — if that row is an
    old v10 topic, it may already carry a v10-shaped question bank (no
    body_json, Title-case difficulty). Those can't be served through the
    v12 arena, so only genuinely v12-shaped rows (body_json set) qualify.
    """
    rows = (
        await db.execute(
            select(TopicQuestion).where(
                TopicQuestion.topic_id == subtopic_id,
                TopicQuestion.review_status.in_(["published", "auto"]),
                TopicQuestion.body_json.is_not(None),
            )
        )
    ).scalars().all()
    return sorted(
        rows,
        key=lambda q: (_DIFFICULTY_RANK.get(q.difficulty, 1), q.created_order or 0),
    )


# ----------------------------------------------------------------------
# Steps 5-6: Practice button -> subtopic tabs (Type A)
# ----------------------------------------------------------------------

async def get_subtopic_tabs(
    db: AsyncSession, user_id: str, topic_id: str, domain_id: str
) -> dict:
    topic = (
        await db.execute(select(RoadmapTopic).where(RoadmapTopic.id == topic_id))
    ).scalars().first()
    if topic is None:
        raise ValueError("Topic not found")

    subtopics = (
        await db.execute(
            select(RoadmapTopic)
            .where(RoadmapTopic.parent_topic_id == topic_id)
            .order_by(RoadmapTopic.item_order)
        )
    ).scalars().all()

    tabs = []
    for order, st in enumerate(subtopics):
        utp = (
            await db.execute(
                select(UserTopicProgress).where(
                    UserTopicProgress.user_id == user_id,
                    UserTopicProgress.topic_id == st.id,
                    UserTopicProgress.domain_id == domain_id,
                )
            )
        ).scalars().first()
        p = parse_progress_json(getattr(utp, "progress_json", None))
        bank = await _bank_for_subtopic(db, st.id)
        correct = int(p["_correct"])
        tabs.append({
            "subtopic_id": st.id,
            "name": st.title,
            "tab_order": order,
            "answered": int(p["_answered"]),
            "correct": correct,
            "bank_size": max(len(bank), QUESTIONS_PER_SUBTOPIC),
            "mastered": is_mastered(correct),
            "mastery_pct": min(
                100, round(correct / MASTERY_CORRECT_THRESHOLD * 100)
            ),
        })

    return {
        "topic_id": topic_id,
        "topic_title": topic.title,
        "tabs": tabs,
        "all_mastered": bool(tabs) and all(t["mastered"] for t in tabs),
    }


# ----------------------------------------------------------------------
# Step 7: serve the next question (Type A; Type B ONLY on exhaustion)
# ----------------------------------------------------------------------

def _question_payload(q: TopicQuestion, position: int, bank_size: int) -> dict:
    """What the student is allowed to see BEFORE answering.
    model_solution / why_how / common_mistakes are withheld until analysis."""
    body = q.body_json if isinstance(q.body_json, dict) else json.loads(q.body_json or "{}")
    examples = (body.get("examples") or [])[:2]
    while len(examples) < 2:                      # locked: exactly two examples
        examples.append({"input": "", "output": "", "why": ""})
    return {
        "question_id": q.id,
        "subtopic_id": q.topic_id,
        "position": position,
        "bank_size": bank_size,
        "difficulty": q.difficulty or "basic",
        "question_kind": q.question_kind or "text",
        "question": body.get("question", ""),
        "examples": examples,
        "starter_code": body.get("starter_code")
        if (q.question_kind or "text") == "code" else None,
        "source": "auto" if q.review_status == "auto" else "seed",
    }


async def get_next_question(
    db: AsyncSession, user_id: str, subtopic_id: str, domain_id: str
) -> dict:
    subtopic = (
        await db.execute(
            select(RoadmapTopic).where(RoadmapTopic.id == subtopic_id)
        )
    ).scalars().first()
    if subtopic is None or subtopic.parent_topic_id is None:
        raise ValueError("Subtopic not found")

    utp = await get_or_create_utp(db, user_id, subtopic_id, domain_id)
    p = parse_progress_json(utp.progress_json)
    seen = set(p["_seen_qids"])

    bank = await _bank_for_subtopic(db, subtopic_id)
    regenerated = False

    unseen = [q for q in bank if q.id not in seen]
    if not unseen:
        # generate-once-cache: exactly ONE AI call, saved back forever
        new_q = await _generate_once_cache(db, subtopic)
        bank.append(new_q)
        unseen = [new_q]
        regenerated = True

    q = unseen[0]
    position = bank.index(q) + 1
    return {
        "exhausted_and_regenerated": regenerated,
        "question": _question_payload(q, position, len(bank)),
    }


async def _generate_once_cache(
    db: AsyncSession, subtopic: RoadmapTopic
) -> TopicQuestion:
    """Bank exhausted -> ONE live generation, persisted with
    review_status='auto' for admin QA. Next student gets it free."""
    parent = (
        await db.execute(
            select(RoadmapTopic).where(RoadmapTopic.id == subtopic.parent_topic_id)
        )
    ).scalars().first()
    topic_title = parent.title if parent else "General"

    raw = await ask_ai(
        GENERATE_QUESTION_SYSTEM,
        GENERATE_QUESTION_USER.format(
            topic=topic_title, subtopic=subtopic.title, difficulty="advanced"
        ),
    )
    body = parse_json(raw)

    # deterministic shape guard - never trust LLM output blindly
    examples = (body.get("examples") or [])[:2]
    while len(examples) < 2:
        examples.append({"input": "", "output": "", "why": ""})
    clean = {
        "question": str(body.get("question", ""))[:4000],
        "examples": examples,
        "model_solution": str(body.get("model_solution", ""))[:6000],
        "why_how": str(body.get("why_how", ""))[:3000],
        "common_mistakes": [str(m)[:300] for m in
                            (body.get("common_mistakes") or [])[:5]],
        "starter_code": str(body.get("starter_code", ""))[:2000] or None,
    }
    kind = body.get("question_kind")
    if kind not in ("code", "text", "sql", "math"):
        kind = "text"

    existing_count = len(await _bank_for_subtopic(db, subtopic.id))
    q = TopicQuestion(
        topic_id=subtopic.id,
        difficulty="advanced",
        question_kind=kind,
        review_status="auto",
        created_order=existing_count,
        question_text=clean["question"],
        body_json=json.dumps(clean),
    )
    db.add(q)
    await db.commit()
    logger.info("generate-once-cache: appended auto question to subtopic %s",
                subtopic.id)
    return q


# ----------------------------------------------------------------------
# Progress strip (Type A)
# ----------------------------------------------------------------------

async def get_subtopic_progress(
    db: AsyncSession, user_id: str, subtopic_id: str, domain_id: str
) -> dict:
    utp = await get_or_create_utp(db, user_id, subtopic_id, domain_id)
    p = parse_progress_json(utp.progress_json)
    bank = await _bank_for_subtopic(db, subtopic_id)
    seen = set(p["_seen_qids"])
    next_q = next((q for q in bank if q.id not in seen), None)
    correct = int(p["_correct"])
    return {
        "subtopic_id": subtopic_id,
        "answered": int(p["_answered"]),
        "correct": correct,
        "bank_size": max(len(bank), QUESTIONS_PER_SUBTOPIC),
        "mastery_pct": min(100, round(correct / MASTERY_CORRECT_THRESHOLD * 100)),
        "mastered": is_mastered(correct),
        "next_difficulty": next_q.difficulty if next_q else None,
    }


# ----------------------------------------------------------------------
# Attempt recording (called by analysis_v12_service - pure math)
# ----------------------------------------------------------------------

async def record_attempt_progress(
    db: AsyncSession,
    user_id: str,
    subtopic_id: str,
    domain_id: str,
    question_id: str,
    score: int,
) -> dict:
    """Deterministic state transition. Returns mastery flags for the UI."""
    utp = await get_or_create_utp(db, user_id, subtopic_id, domain_id)
    p = parse_progress_json(utp.progress_json)

    first_time = question_id not in p["_seen_qids"]
    if first_time:
        p["_seen_qids"].append(question_id)
        p["_answered"] = int(p["_answered"]) + 1
        if score >= CORRECT_SCORE_THRESHOLD:
            p["_correct"] = int(p["_correct"]) + 1
        p["_score_sum"] = int(p["_score_sum"]) + int(score)

    correct = int(p["_correct"])
    mastered = is_mastered(correct)
    utp.progress_json = json.dumps(p)
    utp.mastery_score = min(100, round(correct / QUESTIONS_PER_SUBTOPIC * 100))
    utp.status = "mastered" if mastered else "in_progress"
    await db.flush()

    # did the whole TOPIC just complete? (all sibling subtopics mastered)
    subtopic = (
        await db.execute(
            select(RoadmapTopic).where(RoadmapTopic.id == subtopic_id)
        )
    ).scalars().first()
    siblings = (
        await db.execute(
            select(RoadmapTopic).where(
                RoadmapTopic.parent_topic_id == subtopic.parent_topic_id
            )
        )
    ).scalars().all()
    topic_complete = True
    for sib in siblings:
        sib_utp = (
            await db.execute(
                select(UserTopicProgress).where(
                    UserTopicProgress.user_id == user_id,
                    UserTopicProgress.topic_id == sib.id,
                    UserTopicProgress.domain_id == domain_id,
                )
            )
        ).scalars().first()
        sp = parse_progress_json(getattr(sib_utp, "progress_json", None))
        if not is_mastered(int(sp["_correct"])):
            topic_complete = False
            break

    return {
        "counted": first_time,
        "subtopic_mastered": mastered,
        "topic_complete": topic_complete,
        "answered": int(p["_answered"]),
        "correct": correct,
    }
