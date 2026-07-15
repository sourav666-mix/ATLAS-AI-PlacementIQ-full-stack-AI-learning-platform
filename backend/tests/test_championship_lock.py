# test_championship.py - [NEW] timer, lock-on-exit, unique attempt, batch analysis
# FILE: tests/test_championship_lock.py
# BATCH 18 (new) - Critical path 5: proctoring lock rules (Guide §4.5).
# Fullscreen-exit violations increment the counter and lock the attempt;
# a locked attempt cannot submit further answers. Server-side rules, not UI.

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

import helpers
from conftest import app


def _seed_live_championship(db):
    Champ = helpers.model_for_table("championships")
    Question = helpers.model_for_table("championship_questions")
    assert Champ is not None, "championships model not found"

    async def _run():
        async with db.session() as session:
            champ_id = str(uuid.uuid4())
            c = Champ()
            helpers.set_first(c, champ_id, "id")
            helpers.set_first(c, "Test Live Championship", "title", "name")
            helpers.set_first(c, "live", "status")
            helpers.set_first(c, datetime.utcnow(), "starts_at")
            helpers.set_first(c, 900, "duration_seconds", "duration")
            session.add(c)
            if Question is not None:
                q = Question()
                helpers.set_first(q, str(uuid.uuid4()), "id")
                helpers.set_first(q, champ_id, "championship_id")
                helpers.set_first(q, "2 + 2 = ?", "question_text", "question")
                helpers.set_first(q, 1, "sort_order", "order_index", "qno")
                session.add(q)
            await session.commit()
            return champ_id
    return db.run(_run())


def _attempt_row(db, champ_id, user_id):
    Attempt = helpers.model_for_table("championship_attempts")
    assert Attempt is not None, "championship_attempts model not found"
    ccol = helpers.col(Attempt, "championship_id")
    ucol = helpers.col(Attempt, "user_id")

    async def _run():
        async with db.session() as session:
            return (await session.execute(
                select(Attempt).where(ccol == champ_id, ucol == user_id)
            )).scalars().first()
    return db.run(_run())


def test_violations_lock_the_attempt(client, student, db_session):
    champ_id = _seed_live_championship(db_session)

    enter = helpers.find_route(app, "POST", "champion", "enter")
    violate = (helpers.find_route(app, "POST", "violation")
               or helpers.find_route(app, "POST", "proctor"))
    if not enter or not violate:
        pytest.skip(f"enter={enter} violation={violate} — report actual paths")

    response = helpers.request_with_variants(
        client, "POST", helpers.fill_path(enter, championship_id=champ_id,
                                          id=champ_id),
        [{"championship_id": champ_id}, {}],
        headers=student["headers"])
    assert response is not None and response.status_code < 400, \
        f"enter failed: {response.status_code} {response.text[:300]}"

    # Two fullscreen exits: one grace, then LOCK (Section 4.5)
    for _ in range(2):
        response = helpers.request_with_variants(
            client, "POST", helpers.fill_path(violate,
                                              championship_id=champ_id,
                                              id=champ_id),
            [{"championship_id": champ_id, "kind": "fullscreen_exit"},
             {"championship_id": champ_id, "event": "fullscreen_exit"},
             {"championship_id": champ_id}],
            headers=student["headers"])
        assert response is not None and response.status_code < 500

    attempt = _attempt_row(db_session, champ_id, student["user_id"])
    assert attempt is not None, "no attempt row after entering"
    exits = helpers.row_get(attempt, "fullscreen_exits", "violations",
                            default=0)
    locked = helpers.row_get(attempt, "locked", "is_locked", default=0)
    assert int(exits) >= 2, f"violations not counted (exits={exits})"
    assert locked in (1, True), \
        f"attempt must be LOCKED after repeated violations (locked={locked})"

    # A locked attempt must reject further answers
    answer = helpers.find_route(app, "POST", "champion", "answer")
    if answer:
        response = helpers.request_with_variants(
            client, "POST", helpers.fill_path(answer,
                                              championship_id=champ_id,
                                              id=champ_id),
            [{"championship_id": champ_id, "question_id": "x",
              "answer": "4"},
             {"championship_id": champ_id, "answers": {"1": "4"}}],
            headers=student["headers"])
        assert response is not None and response.status_code >= 400, \
            f"LOCKED attempt accepted an answer ({response.status_code})"