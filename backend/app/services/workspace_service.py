# backend/app/services/workspace_service.py
"""
ATLAS AI 4.0 - v12 Live Lab Pro: VS Code-mode workspace files.

Type A - ZERO AI calls. Real project structure (main.py imports utils.py)
persisted as TEXT rows; execution and cross-file imports happen in the
client's Pyodide virtual FS, which the frontend syncs from this tree.

Path discipline (pure validation, applied before any DB write):
  * relative, forward-slash paths only; no '..', no leading '/', no '\\'
  * text extensions only (.py .sql .md .txt .json .csv-as-text) - anything
    else is rejected, keeping the never-store-binary rule structural.
"""

import re
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_pro import NotebookSession, WorkspaceFile
from app.schemas.lab_pro import MAX_WS_FILES, MAX_WS_FILE_CHARS

_ALLOWED_EXT = (".py", ".sql", ".md", ".txt", ".json", ".csv")
_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_\-. ]{1,80}$")


def validate_path(path: str, is_folder: bool) -> str:
    """Pure path validation. Raises ValueError on anything unsafe."""
    path = path.strip().strip("/")
    if not path or "\\" in path or "//" in path:
        raise ValueError("Invalid path")
    segments = path.split("/")
    if len(segments) > 8:
        raise ValueError("Folder tree too deep (max 8 levels)")
    for seg in segments:
        if seg in ("", ".", "..") or not _SEGMENT_RE.match(seg):
            raise ValueError(f"Invalid path segment: '{seg}'")
    if not is_folder and not path.lower().endswith(_ALLOWED_EXT):
        raise ValueError(
            f"Only text files allowed: {', '.join(_ALLOWED_EXT)}"
        )
    return path


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


async def _files(db: AsyncSession, session_id: str) -> List[WorkspaceFile]:
    return (
        await db.execute(
            select(WorkspaceFile)
            .where(WorkspaceFile.session_id == session_id)
            .order_by(WorkspaceFile.path)
        )
    ).scalars().all()


def _tree_payload(session_id: str, files: List[WorkspaceFile]) -> dict:
    return {"session_id": session_id, "files": [
        {"path": f.path, "is_folder": bool(f.is_folder),
         "size_chars": f.size_chars}
        for f in files
    ]}


# ------------------------------------------------------------------ API

async def get_tree(db: AsyncSession, user_id: str, session_id: str) -> dict:
    await _owned_session(db, user_id, session_id)
    return _tree_payload(session_id, await _files(db, session_id))


async def upsert_file(
    db: AsyncSession, user_id: str, session_id: str,
    path: str, is_folder: bool, content: str,
) -> dict:
    await _owned_session(db, user_id, session_id)
    path = validate_path(path, is_folder)
    content = "" if is_folder else (content or "")[:MAX_WS_FILE_CHARS]

    row = (
        await db.execute(
            select(WorkspaceFile).where(
                WorkspaceFile.session_id == session_id,
                WorkspaceFile.path == path,
            )
        )
    ).scalars().first()
    if row is None:
        count = len(await _files(db, session_id))
        if count >= MAX_WS_FILES:
            raise ValueError(f"Workspace file limit reached ({MAX_WS_FILES})")
        row = WorkspaceFile(session_id=session_id, path=path,
                            is_folder=is_folder)
        db.add(row)
    row.content = content
    row.size_chars = len(content)
    await db.commit()
    return _tree_payload(session_id, await _files(db, session_id))


async def read_file(
    db: AsyncSession, user_id: str, session_id: str, path: str
) -> dict:
    await _owned_session(db, user_id, session_id)
    row = (
        await db.execute(
            select(WorkspaceFile).where(
                WorkspaceFile.session_id == session_id,
                WorkspaceFile.path == path,
                WorkspaceFile.is_folder.is_(False),
            )
        )
    ).scalars().first()
    if row is None:
        raise ValueError("File not found")
    return {"path": row.path, "content": row.content or ""}


async def rename(
    db: AsyncSession, user_id: str, session_id: str,
    old_path: str, new_path: str,
) -> dict:
    """Rename a file OR a folder (folder rename re-prefixes children)."""
    await _owned_session(db, user_id, session_id)
    rows = await _files(db, session_id)
    target = next((f for f in rows if f.path == old_path), None)
    if target is None:
        raise ValueError("Path not found")
    new_path = validate_path(new_path, bool(target.is_folder))
    if any(f.path == new_path for f in rows):
        raise ValueError("A file with that path already exists")

    prefix = old_path + "/"
    for f in rows:
        if f.path == old_path:
            f.path = new_path
        elif target.is_folder and f.path.startswith(prefix):
            f.path = new_path + "/" + f.path[len(prefix):]
    await db.commit()
    return _tree_payload(session_id, await _files(db, session_id))


async def delete_path(
    db: AsyncSession, user_id: str, session_id: str, path: str
) -> dict:
    """Delete a file, or a folder with everything under it."""
    await _owned_session(db, user_id, session_id)
    await db.execute(
        delete(WorkspaceFile).where(
            WorkspaceFile.session_id == session_id,
            (WorkspaceFile.path == path)
            | (WorkspaceFile.path.like(path.replace("%", r"\%") + "/%")),
        )
    )
    await db.commit()
    return _tree_payload(session_id, await _files(db, session_id))