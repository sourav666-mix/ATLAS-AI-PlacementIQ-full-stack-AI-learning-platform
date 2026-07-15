# FILE: tests/test_studio_privacy.py
# BATCH 18 (new) - Critical path 6: Interview Studio privacy (System
# Understanding §10, NON-NEGOTIABLE): "Video is never uploaded and never
# recorded. Only the text transcript and scores are stored."
# Two independent assertions:
#   1. SCHEMA: interview_studio_sessions has NO binary/BLOB column at all.
#   2. DATA: after a full session, no stored value looks like media
#      (base64 video/image payloads, data: URLs, or >100KB blobs).

from __future__ import annotations

import pytest
from sqlalchemy import LargeBinary, inspect as sa_inspect, select

import helpers
from conftest import app


def test_schema_has_no_binary_columns():
    Studio = helpers.model_for_table("interview_studio_sessions")
    assert Studio is not None, "interview_studio_sessions model not found"
    for attr in sa_inspect(Studio).mapper.column_attrs:
        column = attr.columns[0]
        assert not isinstance(column.type, LargeBinary), \
            f"interview_studio_sessions.{attr.key} is a BINARY column — " \
            f"media storage is forbidden by design"
        assert "blob" not in str(column.type).lower(), \
            f"interview_studio_sessions.{attr.key} is {column.type} — " \
            f"media storage is forbidden by design"


def _looks_like_media(value) -> bool:
    if isinstance(value, (bytes, bytearray)):
        return True
    if not isinstance(value, str):
        return False
    lowered = value[:60].lower()
    if lowered.startswith(("data:video", "data:image", "data:audio")):
        return True
    return len(value) > 100_000  # a transcript is text, not a payload dump


def test_full_session_stores_transcript_and_scores_only(client, student,
                                                        db_session, ai_spy):
    start = helpers.find_route(app, "POST", "studio", "start")
    finish = helpers.find_route(app, "POST", "studio", "finish")
    turn = helpers.find_route(app, "POST", "studio", "turn")
    if not start:
        pytest.skip("No studio start route found — report the actual path")

    response = helpers.request_with_variants(
        client, "POST", start,
        [{"domain": "Data Science", "level": "medium", "question_count": 2},
         {"domain": "data-science", "level": "medium", "count": 2}],
        headers=student["headers"])
    assert response is not None and response.status_code < 400, \
        f"studio start failed: {response.status_code} {response.text[:300]}"
    body = response.json() if response.headers.get(
        "content-type", "").startswith("application/json") else {}
    session_id = (body.get("session_id") or body.get("id")
                  or (body.get("session") or {}).get("id"))

    if turn and session_id:
        helpers.request_with_variants(
            client, "POST", helpers.fill_path(turn, session_id=session_id,
                                              id=session_id),
            [{"session_id": session_id,
              "transcript": "I would use a hash map.",
              "presence_pct": 92},
             {"session_id": session_id,
              "answer": "I would use a hash map."}],
            headers=student["headers"])
    if finish and session_id:
        helpers.request_with_variants(
            client, "POST", helpers.fill_path(finish, session_id=session_id,
                                              id=session_id),
            [{"session_id": session_id}, {}],
            headers=student["headers"])

    Studio = helpers.model_for_table("interview_studio_sessions")
    ucol = helpers.col(Studio, "user_id")

    async def _rows():
        async with db_session.session() as session:
            return (await session.execute(
                select(Studio).where(ucol == student["user_id"])
            )).scalars().all()
    rows = db_session.run(_rows())
    assert rows, "no interview_studio_sessions row was stored"

    for row in rows:
        for attr in sa_inspect(type(row)).mapper.column_attrs:
            value = getattr(row, attr.key)
            assert not _looks_like_media(value), \
                f"interview_studio_sessions.{attr.key} contains what looks " \
                f"like MEDIA ({str(value)[:60]!r}...) — only transcript " \
                f"text + scores may be stored"