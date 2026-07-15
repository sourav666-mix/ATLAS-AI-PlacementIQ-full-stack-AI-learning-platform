# studio_service.py - [NEW] interviewer loop + report builder
# backend/app/services/studio_service.py
"""AI Interview Studio — the interviewer session loop.

AI budget (spec, Phase 10):
  start()  → ONE call  (generates the whole question set)
  turn()   → ONE call  (evaluate transcript + follow-up decision + next Q)
  finish() → ONE call  (strengths/weaknesses/summary narrative)

Storage (interview_studio_sessions): transcript text + numbers ONLY. Audio and
video never reach this service — the schemas physically cannot carry them.

Session state lives in transcript_json:
  {"_questions": [...], "_follow_up_used": {...}, "turns": [ {...}, ... ]}
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.studio import (
    FinalReport,
    SessionListItem,
    StartResponse,
    StudioSetup,
    TurnRequest,
    TurnResponse,
)
from app.services import studio_catalog, studio_prompts, studio_report_links
from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.services.voice_service import text_to_speech

# --- INTEGRATION POINT -------------------------------------------------------
from app.models.interview_studio import InterviewStudioSession  # Batch 3
# -----------------------------------------------------------------------------


# ── start ────────────────────────────────────────────────────────────────────
async def start(db: AsyncSession, user, setup: StudioSetup) -> StartResponse:
    domain = studio_catalog.resolve_domain(setup.domain)
    if not domain:
        raise HTTPException(404, f"Unknown interview domain '{setup.domain}'")

    # ONE AI call: the entire question set
    system, message = studio_prompts.question_set(
        domain["name"], domain["focus"], setup.level, setup.question_count)
    try:
        raw = await ask_ai(system, message)
        data = parse_json(raw) if isinstance(raw, str) else raw
        questions = [str(q) for q in (data.get("questions") or []) if str(q).strip()]
    except Exception:
        questions = []
    if len(questions) < setup.question_count:
        # deterministic fallback so the session never fails to start
        pads = [f"Tell me about a {domain['name']} concept you find most "
                f"interesting and explain it as if to a junior. (Q{i+1})"
                for i in range(len(questions), setup.question_count)]
        questions += pads
    questions = questions[: setup.question_count]

    session = InterviewStudioSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        domain=domain["name"],
        level=setup.level,
        question_count=setup.question_count,
        transcript_json={"_questions": questions, "_follow_up_used": {},
                          "turns": []},
        per_question_scores_json=[],
        overall_score=None,
        presence_pct=None,
        report_json=None,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    audio_b64 = provider = None
    if setup.voice_mode:
        audio_b64, provider = await text_to_speech(questions[0])

    return StartResponse(
        session_id=session.id,
        domain=domain["name"],
        level=setup.level,
        question_count=setup.question_count,
        first_question=questions[0],
        question_index=0,
        audio_b64=audio_b64,
        tts_provider=provider,
    )


# ── one turn ─────────────────────────────────────────────────────────────────
async def turn(db: AsyncSession, user, session_id: str,
               payload: TurnRequest, voice_mode: bool = True) -> TurnResponse:
    session = await _get_open_session(db, user.id, session_id)
    state: dict = dict(session.transcript_json or {})
    questions: list = state.get("_questions", [])
    follow_used: dict = dict(state.get("_follow_up_used", {}))
    turns: list = list(state.get("turns", []))

    idx = payload.question_index
    # the question being answered: a follow-up (stored on the previous turn) or the set question
    pending_follow = state.get("_pending_follow_up")
    if pending_follow and pending_follow.get("index") == idx:
        question_text = pending_follow["question"]
        answering_follow_up = True
    else:
        if idx < 0 or idx >= len(questions):
            raise HTTPException(400, "question_index out of range")
        question_text = questions[idx]
        answering_follow_up = False

    remaining = max(0, len(questions) - 1 - idx)

    # ONE AI call: evaluation + follow-up decision
    system, message = studio_prompts.turn_eval(
        session.domain, session.level, question_text,
        payload.transcript_text, remaining)
    try:
        raw = await ask_ai(system, message)
        data = parse_json(raw) if isinstance(raw, str) else raw
    except Exception:
        data = {}
    score = max(0, min(10, int(data.get("score", 5) or 5)))
    feedback = str(data.get("feedback") or "Noted — let's keep going.").strip()
    hint = str(data.get("model_answer_hint") or "").strip()
    weakness_tag = str(data.get("weakness_tag") or "").strip()
    wants_follow = bool(data.get("ask_follow_up")) and remaining > 0
    follow_q = str(data.get("follow_up_question") or "").strip()

    # record this turn (transcript text + numbers only)
    turns.append({
        "index": idx,
        "question": question_text,
        "is_follow_up": answering_follow_up,
        "transcript": payload.transcript_text,
        "score": score,
        "feedback": feedback,
        "weakness_tag": weakness_tag,
        "answer_secs": payload.answer_secs,
        "presence_pct": payload.presence_pct,
    })

    # decide the next question
    is_follow_up_next = False
    next_q: str | None = None
    next_idx: int | None = None
    state.pop("_pending_follow_up", None)

    if (wants_follow and follow_q and not answering_follow_up
            and str(idx) not in follow_used):
        # ask the probe; the student answers it against the SAME index
        follow_used[str(idx)] = True
        state["_pending_follow_up"] = {"index": idx, "question": follow_q}
        next_q, next_idx, is_follow_up_next = follow_q, idx, True
    elif idx + 1 < len(questions):
        next_q, next_idx = questions[idx + 1], idx + 1

    complete = next_q is None

    # persist state
    state["_follow_up_used"] = follow_used
    state["turns"] = turns
    session.transcript_json = state
    session.per_question_scores_json = [
        {"index": t["index"], "score": t["score"]} for t in turns]
    await db.commit()

    audio_b64 = provider = None
    if voice_mode:
        spoken = feedback if complete else f"{feedback} ... Next question: {next_q}"
        audio_b64, provider = await text_to_speech(spoken)

    return TurnResponse(
        question_index=idx,
        score=score,
        feedback=feedback,
        model_answer_hint=hint,
        is_follow_up=is_follow_up_next,
        next_question=next_q,
        next_index=next_idx,
        audio_b64=audio_b64,
        tts_provider=provider,
        session_complete=complete,
    )


# ── finish ───────────────────────────────────────────────────────────────────
async def finish(db: AsyncSession, user, session_id: str,
                 presence_pct: int | None) -> FinalReport:
    session = await _get_open_session(db, user.id, session_id)
    state: dict = dict(session.transcript_json or {})
    turns: list = state.get("turns", [])
    if not turns:
        raise HTTPException(400, "No answered questions — nothing to report")

    scores = [int(t.get("score", 0)) for t in turns]
    overall = round(sum(scores) / (10 * len(scores)) * 100)

    # ONE AI call: narrative report
    system, message = studio_prompts.final_report(session.domain, session.level, turns)
    try:
        raw = await ask_ai(system, message)
        data = parse_json(raw) if isinstance(raw, str) else raw
    except Exception:
        data = {}
    strengths = [str(s) for s in (data.get("strengths") or [])][:4]
    weaknesses = [str(w) for w in (data.get("weaknesses") or [])][:4]
    summary = str(data.get("summary") or "").strip()

    # merge per-turn weakness tags into the weakness list
    for t in turns:
        tag = t.get("weakness_tag")
        if tag and tag not in weaknesses:
            weaknesses.append(tag)

    plan = studio_report_links.build_plan(weaknesses)

    # presence: request value, else average of per-turn numbers
    if presence_pct is None:
        turn_p = [t["presence_pct"] for t in turns if t.get("presence_pct") is not None]
        presence_pct = round(sum(turn_p) / len(turn_p)) if turn_p else None

    report = {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "summary": summary,
        "improvement_plan": [p.model_dump() for p in plan],
    }
    session.overall_score = overall
    session.presence_pct = presence_pct
    session.report_json = report
    await db.commit()

    # award points via the scoring spine (graceful if event type is unhandled)
    points = 0
    try:
        from app.services.progress_engine import record_event
        score_weight = overall / 100
        points = round(15 * score_weight)
        await record_event(db, user.id, "interview", {
            "interview_sessions": 1,
            "score_weight": score_weight,
            "overall_score": overall,
        })
    except Exception:
        points = 0

    return FinalReport(
        session_id=session.id,
        domain=session.domain,
        level=session.level,
        questions_answered=len(turns),
        overall_score=overall,
        presence_pct=presence_pct,
        strengths=strengths,
        weaknesses=weaknesses,
        per_question=[{"index": t["index"], "question": t["question"][:120],
                        "score": t["score"]} for t in turns],
        improvement_plan=plan,
        summary=summary,
        points_awarded=points,
    )


# ── history ──────────────────────────────────────────────────────────────────
async def list_sessions(db: AsyncSession, user) -> list[SessionListItem]:
    rows = (await db.execute(
        select(InterviewStudioSession)
        .where(InterviewStudioSession.user_id == user.id)
        .order_by(InterviewStudioSession.created_at.desc())
    )).scalars().all()
    return [SessionListItem(
        id=r.id, domain=r.domain or "", level=r.level or "",
        question_count=r.question_count or 0,
        overall_score=r.overall_score, presence_pct=r.presence_pct,
        created_at=getattr(r, "created_at", None),
        finished=r.report_json is not None,
    ) for r in rows]


async def get_report(db: AsyncSession, user, session_id: str) -> FinalReport:
    session = (await db.execute(select(InterviewStudioSession).where(
        InterviewStudioSession.id == session_id,
        InterviewStudioSession.user_id == user.id,
    ))).scalar_one_or_none()
    if not session or not session.report_json:
        raise HTTPException(404, "Report not found — finish the session first")
    rep = session.report_json or {}
    turns = (session.transcript_json or {}).get("turns", [])
    return FinalReport(
        session_id=session.id, domain=session.domain or "",
        level=session.level or "", questions_answered=len(turns),
        overall_score=session.overall_score or 0,
        presence_pct=session.presence_pct,
        strengths=rep.get("strengths", []),
        weaknesses=rep.get("weaknesses", []),
        per_question=[{"index": t["index"], "question": t["question"][:120],
                        "score": t["score"]} for t in turns],
        improvement_plan=[
            studio_report_links.PlatformPlanItem(**p)
            for p in rep.get("improvement_plan", [])],
        summary=rep.get("summary", ""),
    )


async def _get_open_session(db, user_id, session_id) -> InterviewStudioSession:
    session = (await db.execute(select(InterviewStudioSession).where(
        InterviewStudioSession.id == session_id,
        InterviewStudioSession.user_id == user_id,
    ))).scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    if session.report_json is not None:
        raise HTTPException(403, "Session already finished")
    return session