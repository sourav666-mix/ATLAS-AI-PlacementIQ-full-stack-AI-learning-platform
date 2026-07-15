# FILE: tests/test_roadmap_once.py
# BATCH 18 (new) - Critical path 2: "roadmap generation is a filter query,
# not a generator. It runs ONCE, at subscription time, and never again."
# (System Understanding §4). Calling generate twice must NOT duplicate
# user_topic_progress rows, and must make ZERO AI calls.

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

import helpers
from conftest import app


def _seed_curriculum(db):
    """Insert one domain + 3 topics + a plan + a subscription for the student.
    Returns (domain_id, plan_id)."""
    Domain = helpers.model_for_table("domains")
    Topic = helpers.model_for_table("roadmap_topics")
    Plan = helpers.model_for_table("subscription_plans")
    assert Domain is not None and Topic is not None, \
        "domains/roadmap_topics models not found"

    async def _run():
        async with db.session() as session:
            domain_id, plan_id = str(uuid.uuid4()), str(uuid.uuid4())
            d = Domain()
            helpers.set_first(d, domain_id, "id")
            helpers.set_first(d, "Data Science", "name", "title")
            helpers.set_first(d, "data-science", "slug")
            session.add(d)
            for i in range(3):
                t = Topic()
                helpers.set_first(t, str(uuid.uuid4()), "id")
                helpers.set_first(t, domain_id, "domain_id")
                helpers.set_first(t, f"Topic {i}", "name", "title")
                helpers.set_first(t, i, "sort_order", "order_index")
                helpers.set_first(t, 3, "min_plan_months")
                session.add(t)
            if Plan is not None:
                p = Plan()
                helpers.set_first(p, plan_id, "id")
                helpers.set_first(p, "3-Month", "name", "title")
                helpers.set_first(p, 3, "duration_months", "months")
                helpers.set_first(p, 447, "price", "price_inr", "amount")
                session.add(p)
            await session.commit()
            return domain_id, plan_id
    return db.run(_run())


def _progress_count(db, user_id):
    Progress = helpers.model_for_table("user_topic_progress")
    assert Progress is not None, "user_topic_progress model not found"
    ucol = helpers.col(Progress, "user_id")

    async def _run():
        async with db.session() as session:
            return int((await session.execute(
                select(func.count()).select_from(Progress)
                .where(ucol == user_id))).scalar() or 0)
    return db.run(_run())


def test_roadmap_generates_once_and_without_ai(client, student, db_session,
                                               ai_spy):
    domain_id, plan_id = _seed_curriculum(db_session)

    generate = (helpers.find_route(app, "POST", "roadmap", "generate")
                or helpers.find_route(app, "POST", "subscribe")
                or helpers.find_route(app, "POST", "subscription"))
    if not generate:
        pytest.skip("No roadmap-generate/subscribe POST route found — "
                    "report the actual path so we pin it")

    variants = [
        {"domain_id": domain_id, "plan_id": plan_id},
        {"domain_id": domain_id, "plan_months": 3},
        {"domain_slug": "data-science", "plan_months": 3},
        {"domain": "data-science", "months": 3},
    ]
    ai_spy.reset()
    first = helpers.request_with_variants(client, "POST", generate, variants,
                                          headers=student["headers"])
    assert first is not None and first.status_code < 400, \
        f"roadmap generation failed: {first.status_code} {first.text[:300]}"
    assert ai_spy.calls == 0, \
        f"roadmap generation must be a FILTER QUERY — it made " \
        f"{ai_spy.calls} AI call(s)"

    count_after_first = _progress_count(db_session, student["user_id"])
    assert count_after_first > 0, \
        "generation produced no user_topic_progress rows"

    second = helpers.request_with_variants(client, "POST", generate, variants,
                                           headers=student["headers"])
    count_after_second = _progress_count(db_session, student["user_id"])
    assert count_after_second == count_after_first, \
        f"roadmap ran twice and DUPLICATED rows " \
        f"({count_after_first} -> {count_after_second}); it must run once " \
        f"per subscription (second call returned {second.status_code})"