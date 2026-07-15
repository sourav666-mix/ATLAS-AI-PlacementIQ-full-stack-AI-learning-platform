# FILE: tests/test_practice_cost_model.py
# BATCH 18 (new) - Critical path 3, THE flagship cost-model test:
#   * score_attempt is Type B  -> exactly ONE AI call
#   * reveal_answer is Type A  -> ZERO AI calls, pure DB read
# "If your AI assistant calls AI inside reveal_answer — stop it."
# (System Understanding §11)

from __future__ import annotations

import uuid

import pytest

import helpers
from conftest import app


def _seed_question(db):
    Question = helpers.model_for_table("topic_questions")
    Topic = helpers.model_for_table("roadmap_topics")
    assert Question is not None, "topic_questions model not found"

    async def _run():
        async with db.session() as session:
            topic_id = str(uuid.uuid4())
            if Topic is not None:
                t = Topic()
                helpers.set_first(t, topic_id, "id")
                helpers.set_first(t, "Reveal Topic", "name", "title")
                session.add(t)
            qid = str(uuid.uuid4())
            q = Question()
            helpers.set_first(q, qid, "id")
            helpers.set_first(q, topic_id, "topic_id")
            helpers.set_first(q, "What is a Python list?",
                              "question_text", "question", "prompt")
            helpers.set_first(q, "An ordered, mutable sequence.",
                              "model_answer", "answer", "solution")
            helpers.set_first(q, "Because ordering matters.", "why")
            helpers.set_first(q, "Use square brackets.", "how")
            helpers.set_first(q, "x = [1, 2, 3]", "example")
            helpers.set_first(q, "Confusing lists with tuples.",
                              "common_mistakes")
            helpers.set_first(q, "basic", "difficulty")
            helpers.set_first(q, "text", "question_kind", "kind")
            helpers.set_first(q, "published", "review_status", "status")
            session.add(q)
            await session.commit()
            return qid
    return db.run(_run())


def test_score_costs_one_call_and_reveal_costs_zero(client, student,
                                                    db_session, ai_spy):
    question_id = _seed_question(db_session)

    attempt = (helpers.find_route(app, "POST", "attempt")
               or helpers.find_route(app, "POST", "practice", "score"))
    reveal_post = helpers.find_route(app, "POST", "reveal")
    reveal_get = helpers.find_route(app, "GET", "reveal")
    if not attempt or not (reveal_post or reveal_get):
        pytest.skip(f"attempt route={attempt} reveal route="
                    f"{reveal_post or reveal_get} — report actual paths")

    # --- score_attempt: exactly ONE gateway call ---
    ai_spy.reset()
    response = helpers.request_with_variants(
        client, "POST", helpers.fill_path(attempt, question_id=question_id),
        [
            {"question_id": question_id, "answer": "A mutable sequence."},
            {"question_id": question_id, "user_answer": "A mutable sequence."},
            {"question_id": question_id, "answer_text": "A mutable sequence."},
        ],
        headers=student["headers"])
    assert response is not None and response.status_code < 400, \
        f"attempt failed: {response.status_code} {response.text[:300]}"
    assert ai_spy.calls == 1, \
        f"score_attempt must make exactly ONE AI call, made {ai_spy.calls}"

    # --- reveal_answer: ZERO gateway calls, content comes from the bank ---
    ai_spy.reset()
    if reveal_get:
        path = helpers.fill_path(reveal_get, question_id=question_id,
                                 id=question_id, qid=question_id)
        response = client.get(path, headers=student["headers"])
    else:
        response = helpers.request_with_variants(
            client, "POST",
            helpers.fill_path(reveal_post, question_id=question_id,
                              id=question_id),
            [{"question_id": question_id}, {}],
            headers=student["headers"])
    assert response is not None and response.status_code < 400, \
        f"reveal failed: {response.status_code} {response.text[:300]}"
    assert ai_spy.calls == 0, \
        f"REVEAL MADE {ai_spy.calls} AI CALL(S) — reveal_answer must be a " \
        f"pure DB read; fix weak content in seed_content.py, never with a " \
        f"live call"
    assert "mutable" in response.text.lower() or \
           "square brackets" in response.text.lower(), \
        "reveal did not return the pre-seeded bank content"