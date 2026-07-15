# FILE: app/services/lab_service.py
# BATCH 20 / v11 Phase 13 (new) - Lab catalog + deterministic grading
# orchestration + progress hook.
# COST MODEL: everything in this file is Type A — ZERO AI calls. The hidden
# tests run in the student's browser (Pyodide); the backend only RECORDS
# which tasks passed. Points flow through progress_engine (the single spine).
# PRIVACY: text + metadata only; any payload that smells like a binary/base64
# upload is rejected.

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab, LabDataset, LabSession

logger = logging.getLogger("atlas.lab")

LAB_COMPLETION_POINTS = 20  # per completed lab; flows through the spine


def _reject_non_text(snapshot: Optional[str]) -> None:
    if not snapshot:
        return
    head = snapshot[:100].lower()
    if head.startswith(("data:video", "data:image", "data:audio",
                        "data:application")):
        raise HTTPException(status_code=413,
                            detail="Binary/base64 payloads are not stored — "
                                   "the Live Lab keeps code TEXT only.")


def _tasks_of(lab: Lab) -> list:
    tasks = lab.graded_tasks_json or []
    return tasks if isinstance(tasks, list) else []


async def list_labs(db: AsyncSession, domain_id: Optional[str] = None) -> list:
    stmt = select(Lab).where(Lab.review_status == "published")
    if domain_id:
        stmt = stmt.where(Lab.domain_id == domain_id)
    stmt = stmt.order_by(Lab.title)
    return (await db.execute(stmt)).scalars().all()


async def _dataset_for(db: AsyncSession, ref: Optional[str]) -> Optional[dict]:
    if not ref:
        return None
    row = (await db.execute(select(LabDataset).where(
        (LabDataset.id == ref) | (LabDataset.name == ref)))).scalars().first()
    if row is None:
        return {"name": ref, "file_url": ref} if ref.startswith("http") else None
    return {"id": row.id, "name": row.name, "file_url": row.file_url,
            "rows_est": row.rows_est, "size_kb": row.size_kb,
            "description": row.description}


async def get_or_create_session(db: AsyncSession, user_id: str,
                                lab_id: str) -> LabSession:
    session = (await db.execute(select(LabSession).where(
        LabSession.user_id == user_id,
        LabSession.lab_id == lab_id))).scalars().first()
    if session is None:
        session = LabSession(user_id=user_id, lab_id=lab_id,
                             tasks_passed_json={}, artifact_meta_json=[])
        db.add(session)
        await db.flush()
    return session


async def get_lab(db: AsyncSession, user_id: str, lab_id: str) -> dict:
    lab = await db.get(Lab, lab_id)
    if lab is None or lab.review_status != "published":
        raise HTTPException(status_code=404, detail="Lab not found")
    session = await get_or_create_session(db, user_id, lab_id)
    await db.commit()
    # Hidden test code stays hidden: strip test bodies, keep task metadata
    public_tasks = [{k: v for k, v in task.items() if k != "test_code"}
                    for task in _tasks_of(lab)]
    return {
        "id": lab.id, "title": lab.title, "lab_type": lab.lab_type,
        "starter_code": lab.starter_code, "dataset_ref": lab.dataset_ref,
        "graded_tasks": public_tasks, "needs_gpu": bool(lab.needs_gpu),
        "dataset": await _dataset_for(db, lab.dataset_ref),
        "session": {
            "id": session.id, "status": session.status,
            "tasks_passed": session.tasks_passed_json or {},
            "code_snapshot": session.code_snapshot,
            "launched_colab": bool(session.launched_colab),
            "points_awarded": session.points_awarded,
        },
    }


async def hidden_tests(db: AsyncSession, lab_id: str) -> list:
    """Test code for the BROWSER runner — served once per grade run so the
    frontend can execute them in Pyodide. (They never run on the server.)"""
    lab = await db.get(Lab, lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    return [{"id": task.get("id"), "test_code": task.get("test_code", "")}
            for task in _tasks_of(lab)]


async def record_grade(db: AsyncSession, user_id: str, lab_id: str,
                       tasks_passed: dict, code_snapshot: Optional[str],
                       artifacts: Optional[list]) -> dict:
    """NO AI. Merge browser-reported pass/fail into the session."""
    lab = await db.get(Lab, lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    _reject_non_text(code_snapshot)

    session = await get_or_create_session(db, user_id, lab_id)
    merged = dict(session.tasks_passed_json or {})
    valid_ids = {str(task.get("id")) for task in _tasks_of(lab)}
    for task_id, passed in (tasks_passed or {}).items():
        if str(task_id) in valid_ids:
            merged[str(task_id)] = bool(passed)
    session.tasks_passed_json = merged
    if code_snapshot is not None:
        session.code_snapshot = code_snapshot
    if artifacts is not None:
        session.artifact_meta_json = [
            {"name": a["name"], "size_kb": a["size_kb"],
             "kind": a.get("kind")} for a in artifacts]
    total = len(valid_ids)
    passed_count = sum(1 for tid in valid_ids if merged.get(tid))
    await db.commit()
    return {"lab_id": lab_id, "passed": passed_count, "total": total,
            "all_passed": total > 0 and passed_count == total,
            "status": session.status}


async def complete(db: AsyncSession, user_id: str, lab_id: str) -> dict:
    """Finalize: all graded tasks must have passed; award points ONCE via
    progress_engine (the single scoring spine)."""
    lab = await db.get(Lab, lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    session = await get_or_create_session(db, user_id, lab_id)

    if session.status == "completed":
        return {"lab_id": lab_id, "status": "completed",
                "points_awarded": session.points_awarded,
                "note": "already completed — points are never double-awarded"}

    valid_ids = {str(task.get("id")) for task in _tasks_of(lab)}
    merged = session.tasks_passed_json or {}
    missing = [tid for tid in valid_ids if not merged.get(tid)]
    if missing:
        raise HTTPException(status_code=409,
                            detail=f"{len(missing)} graded task(s) not "
                                   f"passed yet: {sorted(missing)}")

    points = LAB_COMPLETION_POINTS
    try:
        import inspect
        from app.services import progress_engine
        result = progress_engine.record_event(
            db, user_id, "lab_completed",
            {"lab_id": lab_id, "lab_type": lab.lab_type, "points": points})
        if inspect.isawaitable(result):
            await result
    except Exception as exc:
        # Never lose the completion; surface the spine mismatch loudly.
        logger.error("progress_engine.record_event('lab_completed') failed: "
                     "%s — session updated, spine NOT credited", exc)
    session.status = "completed"
    session.points_awarded = points
    await db.commit()
    return {"lab_id": lab_id, "status": "completed",
            "points_awarded": points}