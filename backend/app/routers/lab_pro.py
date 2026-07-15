# backend/app/routers/lab_pro.py
"""
ATLAS AI 4.0 - v12 Live Lab Pro: router. Registered under /labpro.

  GET    /labpro/templates                          Type A
  POST   /labpro/session                            Type A (clone template)
  GET    /labpro/sessions                           Type A
  GET    /labpro/session/{sid}                      Type A
  PUT    /labpro/session/{sid}/cells                Type A (autosave)
  PATCH  /labpro/session/{sid}/cell                 Type A (post-run save)
  PUT    /labpro/session/{sid}/mode                 Type A (Colab<->VSCode)
  GET    /labpro/session/{sid}/files                Type A
  GET    /labpro/session/{sid}/file                 Type A
  PUT    /labpro/session/{sid}/file                 Type A
  POST   /labpro/session/{sid}/file/rename          Type A
  DELETE /labpro/session/{sid}/file                 Type A
  POST   /labpro/copilot                            Type B (1 call, cached,
                                                    daily-capped)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.lab_pro import (
    CellPatchRequest,
    CopilotRequest,
    CopilotResponse,
    ModeRequest,
    NotebookSaveRequest,
    NotebookSessionResponse,
    SessionCreate,
    SessionListResponse,
    TemplateListResponse,
    WorkspaceFileContentResponse,
    WorkspaceFileUpsert,
    WorkspaceRenameRequest,
    WorkspaceTreeResponse,
)
from app.services import (
    labpro_copilot_service,
    notebook_service,
    workspace_service,
)

router = APIRouter(prefix="/labpro", tags=["Live Lab Pro"])


def _404(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


def _422(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


# ------------------------------ notebook -------------------------------

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(user=Depends(get_current_user)):
    return notebook_service.list_templates()


@router.post("/session", response_model=NotebookSessionResponse)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        return await notebook_service.create_session(
            db, user.id, payload.env, payload.title
        )
    except ValueError as exc:
        raise _422(exc) from exc


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    return await notebook_service.list_sessions(db, user.id)


@router.get("/session/{sid}", response_model=NotebookSessionResponse)
async def get_session(
    sid: str, db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        return await notebook_service.get_session(db, user.id, sid)
    except ValueError as exc:
        raise _404(exc) from exc


@router.put("/session/{sid}/cells", response_model=NotebookSessionResponse)
async def autosave_cells(
    sid: str, payload: NotebookSaveRequest,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    try:
        return await notebook_service.autosave_cells(
            db, user.id, sid, [c.model_dump() for c in payload.cells]
        )
    except ValueError as exc:
        raise _404(exc) from exc


@router.patch("/session/{sid}/cell", response_model=NotebookSessionResponse)
async def patch_cell(
    sid: str, payload: CellPatchRequest,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    try:
        return await notebook_service.patch_cell(
            db, user.id, sid, payload.cell.model_dump()
        )
    except ValueError as exc:
        raise _422(exc) from exc


@router.put("/session/{sid}/mode", response_model=NotebookSessionResponse)
async def set_mode(
    sid: str, payload: ModeRequest,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    try:
        return await notebook_service.set_mode(db, user.id, sid, payload.mode)
    except ValueError as exc:
        raise _404(exc) from exc


# ------------------------------ workspace ------------------------------

@router.get("/session/{sid}/files", response_model=WorkspaceTreeResponse)
async def get_tree(
    sid: str, db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        return await workspace_service.get_tree(db, user.id, sid)
    except ValueError as exc:
        raise _404(exc) from exc


@router.get("/session/{sid}/file", response_model=WorkspaceFileContentResponse)
async def read_file(
    sid: str, path: str = Query(...),
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    try:
        return await workspace_service.read_file(db, user.id, sid, path)
    except ValueError as exc:
        raise _404(exc) from exc


@router.put("/session/{sid}/file", response_model=WorkspaceTreeResponse)
async def upsert_file(
    sid: str, payload: WorkspaceFileUpsert,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    try:
        return await workspace_service.upsert_file(
            db, user.id, sid, payload.path, payload.is_folder, payload.content
        )
    except ValueError as exc:
        raise _422(exc) from exc


@router.post("/session/{sid}/file/rename", response_model=WorkspaceTreeResponse)
async def rename_path(
    sid: str, payload: WorkspaceRenameRequest,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    try:
        return await workspace_service.rename(
            db, user.id, sid, payload.old_path, payload.new_path
        )
    except ValueError as exc:
        raise _422(exc) from exc


@router.delete("/session/{sid}/file", response_model=WorkspaceTreeResponse)
async def delete_path(
    sid: str, path: str = Query(...),
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    try:
        return await workspace_service.delete_path(db, user.id, sid, path)
    except ValueError as exc:
        raise _404(exc) from exc


# ------------------------------- copilot -------------------------------

@router.post("/copilot", response_model=CopilotResponse)
async def copilot(
    payload: CopilotRequest,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    """Type B: exactly ONE AI call on cache miss; free on cache hit."""
    try:
        return await labpro_copilot_service.run_copilot(
            db, user_id=user.id, action=payload.action, code=payload.code,
            error_text=payload.error_text, goal=payload.goal, env=payload.env,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc