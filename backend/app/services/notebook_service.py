# backend/app/services/notebook_service.py
"""
ATLAS AI 4.0 - v12 Live Lab Pro: notebook sessions + cell autosave.

Type A throughout - ZERO AI calls. The Pyodide kernel is the client's;
this service only persists TEXT so closing the tab never loses work.

Text-only guard: any cell source/output containing a data-URI or base64
blob is stripped of that payload before save - the platform never stores
binary, screenshots, datasets or model files (v11 storage rule, locked).
"""

import re
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_pro import NotebookSession
from app.schemas.lab_pro import (MAX_CELLS, MAX_CELL_CHARS,
                                 MAX_OUTPUT_CHARS)
from app.services.labpro_templates import TEMPLATES

_DATA_URI_RE = re.compile(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]{64,}")
_B64_BLOB_RE = re.compile(r"[A-Za-z0-9+/=]{2048,}")


def _text_only(value: Optional[str], cap: int) -> Optional[str]:
    """Strip binary payloads, enforce the char cap. Pure function."""
    if value is None:
        return None
    value = _DATA_URI_RE.sub("[binary output stays in your browser]", value)
    value = _B64_BLOB_RE.sub("[binary output stays in your browser]", value)
    return value[:cap]


def _clean_cells(cells: List[dict]) -> List[dict]:
    out = []
    for c in cells[:MAX_CELLS]:
        out.append({
            "_id": str(c["id"])[:40],
            "_type": c["cell_type"],
            "_source": _text_only(c.get("source", ""), MAX_CELL_CHARS) or "",
            "_output": _text_only(c.get("output_text"), MAX_OUTPUT_CHARS),
        })
    return out


def _cells_out(cells_json) -> List[dict]:
    return [
        {"id": c.get("_id", ""), "cell_type": c.get("_type", "code"),
         "source": c.get("_source", ""), "output_text": c.get("_output")}
        for c in (cells_json or [])
    ]


def _session_payload(s: NotebookSession) -> dict:
    return {
        "session_id": s.id,
        "title": s.title,
        "mode": s.mode,
        "active_env": s.active_env,
        "cells": _cells_out(s.cells_json),
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


async def _owned_session(
    db: AsyncSession, user_id: str, session_id: str
) -> NotebookSession:
    s = (
        await db.execute(
            select(NotebookSession).where(
                NotebookSession.id == session_id,
                NotebookSession.user_id == user_id,
            )
        )
    ).scalars().first()
    if s is None:
        raise ValueError("Session not found")
    return s


# ------------------------------------------------------------------ API

async def create_session(
    db: AsyncSession, user_id: str, env: str, title: Optional[str]
) -> dict:
    """Clone the env starter template into a fresh session. Type A -
    templates are pure data, so no seeding step is ever required."""
    template = TEMPLATES.get(env)
    if template is None:
        raise ValueError(f"Unknown environment: {env}")
    s = NotebookSession(
        user_id=user_id,
        title=(title or template["title"])[:200],
        active_env=env,
        mode="notebook",
        cells_json=[dict(c) for c in template["cells"]],   # deep-enough copy
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _session_payload(s)


async def list_sessions(db: AsyncSession, user_id: str) -> dict:
    rows = (
        await db.execute(
            select(NotebookSession)
            .where(NotebookSession.user_id == user_id,
                   NotebookSession.status == "active")
            .order_by(NotebookSession.updated_at.desc())
        )
    ).scalars().all()
    return {"sessions": [
        {"session_id": s.id, "title": s.title, "active_env": s.active_env,
         "mode": s.mode, "cell_count": len(s.cells_json or []),
         "updated_at": s.updated_at.isoformat() if s.updated_at else None}
        for s in rows
    ]}


async def get_session(db: AsyncSession, user_id: str, session_id: str) -> dict:
    return _session_payload(await _owned_session(db, user_id, session_id))


async def autosave_cells(
    db: AsyncSession, user_id: str, session_id: str, cells: List[dict]
) -> dict:
    """Whole-notebook autosave (debounced client-side). Text only."""
    s = await _owned_session(db, user_id, session_id)
    s.cells_json = _clean_cells(cells)
    await db.commit()
    await db.refresh(s)
    return _session_payload(s)


async def patch_cell(
    db: AsyncSession, user_id: str, session_id: str, cell: dict
) -> dict:
    """Single-cell save right after a run - cheaper than a full save."""
    s = await _owned_session(db, user_id, session_id)
    cells = list(s.cells_json or [])
    clean = _clean_cells([cell])[0]
    for i, existing in enumerate(cells):
        if existing.get("_id") == clean["_id"]:
            cells[i] = clean
            break
    else:
        if len(cells) >= MAX_CELLS:
            raise ValueError(f"Cell limit reached ({MAX_CELLS})")
        cells.append(clean)
    s.cells_json = cells
    await db.commit()
    await db.refresh(s)
    return _session_payload(s)


async def set_mode(
    db: AsyncSession, user_id: str, session_id: str, mode: str
) -> dict:
    """Toggle Colab <-> VS Code surface. ONE kernel - switching modes
    never loses variables; the backend only records the surface."""
    s = await _owned_session(db, user_id, session_id)
    s.mode = mode
    await db.commit()
    await db.refresh(s)
    return _session_payload(s)


def list_templates() -> dict:
    return {"templates": [
        {"env": env, "title": t["title"], "description": t["description"],
         "cell_count": len(t["cells"])}
        for env, t in TEMPLATES.items()
    ]}