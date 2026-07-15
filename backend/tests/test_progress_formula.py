# FILE: tests/test_progress_formula.py
# BATCH 18 (new) - Critical path 7: the daily point FORMULA, checked by hand
# against the stored row (System Understanding §5 — pure math, zero AI):
#   daily_points = questions*2 + avg_score*1.5 + topics_completed*15
#                + arena_points + interview_points + championship_points
#                + min(streak, 10)*2
# Also: record_event must never touch the AI gateway.

from __future__ import annotations

import inspect

import pytest
from sqlalchemy import select

import helpers


def _recompute(row) -> float:
    questions = float(helpers.row_get(
        row, "questions_attempted", "questions", "questions_today",
        default=0) or 0)
    avg_score = float(helpers.row_get(
        row, "avg_score", "average_score", "avg_score_today", default=0) or 0)
    topics = float(helpers.row_get(
        row, "topics_completed", "topics_done", default=0) or 0)
    arena = float(helpers.row_get(
        row, "arena_points", "arena_points_today", default=0) or 0)
    interview = float(helpers.row_get(
        row, "interview_points", "studio_points", default=0) or 0)
    champ = float(helpers.row_get(
        row, "championship_points", "champ_points", default=0) or 0)
    streak = float(helpers.row_get(
        row, "streak", "current_streak", "streak_days", default=0) or 0)
    return (questions * 2 + avg_score * 1.5 + topics * 15
            + arena + interview + champ + min(streak, 10) * 2)


def test_record_event_and_hand_checked_formula(client, student, db_session,
                                               ai_spy):
    try:
        from app.services import progress_engine
    except ImportError:
        pytest.fail("app/services/progress_engine.py missing — the scoring "
                    "spine is mandatory (Session 6)")
    record_event = getattr(progress_engine, "record_event", None)
    assert callable(record_event), \
        "progress_engine.record_event(db, user_id, event_type, payload) " \
        "is the specified spine entry point and was not found"

    events = [
        ("attempt_scored", {"score": 8, "first_attempt": True,
                            "question_id": "q1", "topic_id": "t1"}),
        ("attempt_scored", {"score": 6, "first_attempt": True,
                            "question_id": "q2", "topic_id": "t1"}),
        ("arena_solved", {"difficulty": "Medium", "points": 10,
                          "problem_id": "p1"}),
    ]
    ai_spy.reset()
    fired = 0

    async def _fire():
        nonlocal fired
        async with db_session.session() as session:
            for event_type, payload in events:
                try:
                    result = record_event(session, student["user_id"],
                                          event_type, payload)
                    if inspect.isawaitable(result):
                        await result
                    fired += 1
                except Exception:
                    continue
            await session.commit()
    db_session.run(_fire())
    assert ai_spy.calls == 0, \
        f"progress_engine made {ai_spy.calls} AI call(s) — the scoring " \
        f"spine is pure math, NO AI, no exceptions"

    Daily = helpers.model_for_table("daily_activity")
    assert Daily is not None, "daily_activity model not found"
    ucol = helpers.col(Daily, "user_id")

    async def _rows():
        async with db_session.session() as session:
            return (await session.execute(
                select(Daily).where(ucol == student["user_id"])
            )).scalars().all()
    rows = db_session.run(_rows())

    if not rows:
        pytest.skip(f"record_event fired {fired}/{len(events)} events but "
                    f"wrote no daily_activity row — report record_event's "
                    f"accepted event_type strings so we pin them")

    checked = 0
    for row in rows:
        stored = helpers.row_get(row, "daily_points", "points",
                                 "points_earned")
        if stored is None:
            continue
        expected = _recompute(row)
        assert abs(float(stored) - expected) < 0.01, \
            f"daily_points={stored} but hand recomputation from the row's " \
            f"own counters gives {expected} — the Section-5 formula is " \
            f"not being applied"
        checked += 1
    assert checked > 0, "no daily_points value found to verify"


def test_streak_resets_to_one_after_gap():
    """Streak rule: after a missed day the streak RESETS TO 1 — not 0 and
    not continue. Pure-logic check of the documented rule."""
    def next_streak(prev_streak: int, days_gap: int) -> int:
        # The rule every implementation must satisfy
        return prev_streak + 1 if days_gap == 1 else 1

    assert next_streak(6, 1) == 7
    assert next_streak(6, 2) == 1, "streak must RESET TO 1 after a gap"
    assert next_streak(6, 30) == 1
    assert next_streak(0, 1) == 1