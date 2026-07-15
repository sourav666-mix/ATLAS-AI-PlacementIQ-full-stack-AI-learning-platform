# backend/app/schemas/lab_pro.py
"""
ATLAS AI 4.0 - v12 Live Lab Pro: request/response schemas.

Caps are enforced HERE first (Pydantic) and re-checked in services, so a
malicious client can never push binary blobs or unbounded text into the
autosave path.
"""

from typing import List, Optional, Literal

from pydantic import BaseModel, Field

MAX_CELLS = 200
MAX_CELL_CHARS = 50_000
MAX_OUTPUT_CHARS = 4_000
MAX_WS_FILES = 200
MAX_WS_FILE_CHARS = 200_000


# ------------------------- sessions / notebook -------------------------

class SessionCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    env: Literal["python", "sql"] = "python"


class CellIn(BaseModel):
    id: str = Field(max_length=40)
    cell_type: Literal["code", "markdown"]
    source: str = Field(default="", max_length=MAX_CELL_CHARS)
    # inline output TEXT only (tables/tracebacks); charts stay in-browser
    output_text: Optional[str] = Field(default=None, max_length=MAX_OUTPUT_CHARS)


class NotebookSaveRequest(BaseModel):
    cells: List[CellIn] = Field(max_length=MAX_CELLS)


class CellPatchRequest(BaseModel):
    cell: CellIn


class ModeRequest(BaseModel):
    mode: Literal["notebook", "workspace"]


class CellOut(BaseModel):
    id: str
    cell_type: str
    source: str
    output_text: Optional[str] = None


class NotebookSessionResponse(BaseModel):
    session_id: str
    title: str
    mode: str
    active_env: str
    cells: List[CellOut]
    updated_at: Optional[str] = None


class SessionSummary(BaseModel):
    session_id: str
    title: str
    active_env: str
    mode: str
    cell_count: int
    updated_at: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: List[SessionSummary]


# ------------------------------ workspace ------------------------------

class WorkspaceFileUpsert(BaseModel):
    path: str = Field(min_length=1, max_length=300)
    is_folder: bool = False
    content: str = Field(default="", max_length=MAX_WS_FILE_CHARS)


class WorkspaceRenameRequest(BaseModel):
    old_path: str = Field(min_length=1, max_length=300)
    new_path: str = Field(min_length=1, max_length=300)


class WorkspaceFileOut(BaseModel):
    path: str
    is_folder: bool
    size_chars: int


class WorkspaceTreeResponse(BaseModel):
    session_id: str
    files: List[WorkspaceFileOut]


class WorkspaceFileContentResponse(BaseModel):
    path: str
    content: str


# ------------------------------- copilot -------------------------------

class CopilotRequest(BaseModel):
    action: Literal["explain", "suggest", "fix", "review"]
    code: str = Field(min_length=1, max_length=30_000)
    error_text: Optional[str] = Field(default=None, max_length=8_000)
    goal: Optional[str] = Field(default=None, max_length=1_000)
    env: Literal["python", "sql"] = "python"


class CopilotResponse(BaseModel):
    action: str
    explanation: str
    suggestion: str
    fixed_code: Optional[str] = None      # NEVER auto-applied client-side
    cached: bool                           # True = served free from cache
    remaining_today: int


# ------------------------------ templates ------------------------------

class TemplateCard(BaseModel):
    env: str
    title: str
    description: str
    cell_count: int


class TemplateListResponse(BaseModel):
    templates: List[TemplateCard]