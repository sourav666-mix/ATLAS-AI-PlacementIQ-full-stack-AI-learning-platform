# FILE: tests/test_arena_generate_once.py
# BATCH 18 (new) - Critical path 4: Code Arena generate-once-cache-forever.
# On an EMPTY bank cell the first request may generate ONCE (source='auto',
# saved to arena_problems); the second identical request must be served from
# the bank with ZERO AI calls.

from __future__ import annotations

import pytest
from sqlalchemy import select

import helpers
from conftest import app


def _auto_rows(db):
    Problem = helpers.model_for_table("arena_problems")
    assert Problem is not None, "arena_problems model not found"
    source = helpers.col(Problem, "source")

    async def _run():
        async with db.session() as session:
            stmt = select(Problem)
            if source is not None:
                stmt = stmt.where(source == "auto")
            return (await session.execute(stmt)).scalars().all()
    return db.run(_run())


def test_generate_once_then_serve_from_bank(client, student, db_session,
                                            ai_spy):
    get_problem = (helpers.find_route(app, "GET", "arena", "problem")
                   or helpers.find_route(app, "POST", "arena", "problem"))
    if not get_problem:
        pytest.skip("No arena problem route found — report the actual path")

    params = {"category": "dsa", "difficulty": "Easy"}

    def fetch():
        if helpers.find_route(app, "GET", "arena", "problem"):
            return client.get(get_problem, params=params,
                              headers=student["headers"])
        return helpers.request_with_variants(
            client, "POST", get_problem,
            [params, {"category": "dsa", "level": "Easy"}],
            headers=student["headers"])

    # First hit on the empty cell: at most ONE generation call
    ai_spy.reset()
    first = fetch()
    assert first is not None and first.status_code < 400, \
        f"arena problem fetch failed: {first.status_code} {first.text[:300]}"
    first_calls = ai_spy.calls
    assert first_calls <= 1, \
        f"empty-cell fetch made {first_calls} AI calls; generate-once means " \
        f"at most 1"

    if first_calls == 1:
        autos = _auto_rows(db_session)
        assert autos, "generation ran but no arena_problems row with " \
                      "source='auto' was cached"

    # Second identical hit: MUST come from the bank, zero AI
    ai_spy.reset()
    second = fetch()
    assert second is not None and second.status_code < 400, second.text[:300]
    assert ai_spy.calls == 0, \
        f"second fetch made {ai_spy.calls} AI call(s) — the cached problem " \
        f"must be served from arena_problems forever"