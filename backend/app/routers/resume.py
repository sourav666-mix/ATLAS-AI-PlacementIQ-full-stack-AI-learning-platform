# resume.py - [MOD] analyze / rebuild / builder draft+export / documents
# backend/app/routers/resume.py
"""
Resume AI 2.0 routes (mounted at /resume).

    POST /resume/analyze          -> upload résumé (+ optional JD) -> analysis
    POST /resume/rebuild          -> analyzed doc -> improved ATS PDF
    POST /resume/builder/draft    -> guided-form inputs -> AI-drafted résumé JSON
    POST /resume/builder/export   -> edited draft + template -> PDF
    POST /resume/build            -> structured content -> PDF (legacy shape)
    GET  /resume/{id}/download    -> download the generated PDF
    GET  /resume/documents        -> the student's résumé documents
    GET  /resume/history          -> alias of /documents (legacy)
"""
import os
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.resume import (
    AnalyzeResult, BuildIn, BuildResult, BuilderExportIn, BuiltPdfOut,
    RebuildIn, ResumeDocOut,
)
from app.services import resume_service
from app.utils import pdf_utils

router = APIRouter()


def _built_pdf_out(doc) -> BuiltPdfOut:
    # No pdf_url here on purpose: the SPA's DownloadLink prefers a url over the
    # base64 payload, and a bare <a href> can't send the bearer token the
    # /download route requires. The data-URL download always works.
    return BuiltPdfOut(
        document_id=doc.id, template=doc.template, pages=doc.pages,
        pdf_base64=resume_service.pdf_base64_for(doc.id),
    )


@router.post("/analyze", response_model=AnalyzeResult)
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(""),
    job_description_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    jd_text = job_description
    if job_description_file is not None:
        jd_bytes = await job_description_file.read()
        jd_text = pdf_utils.extract_text(jd_bytes, job_description_file.filename) or jd_text
    file_bytes = await resume.read()
    try:
        result = await resume_service.analyze(db, current_user.id, file_bytes, resume.filename, jd_text)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return result


@router.post("/rebuild", response_model=BuiltPdfOut)
async def rebuild(
    payload: RebuildIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        doc = await resume_service.rebuild(db, current_user.id, payload.analysis_id, payload.template)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _built_pdf_out(doc)


@router.post("/builder/draft")
async def builder_draft(
    form: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
):
    draft = await resume_service.draft_resume(form)
    return {"draft": draft}


@router.post("/builder/export", response_model=BuiltPdfOut)
async def builder_export(
    payload: BuilderExportIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    resume_json = resume_service.draft_to_resume_json(payload.resume)
    doc = await resume_service.build(db, current_user.id, resume_json, payload.template, payload.pages)
    return _built_pdf_out(doc)


@router.post("/build", response_model=BuildResult)
async def build(
    payload: BuildIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await resume_service.build(db, current_user.id, payload.model_dump(exclude={"template"}), payload.template)
    return BuildResult(document_id=doc.id, template=doc.template, pdf_url=doc.pdf_url, pages=doc.pages)


@router.get("/documents", response_model=List[ResumeDocOut])
@router.get("/history", response_model=List[ResumeDocOut])
async def documents(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await resume_service.get_history(db, current_user.id, limit)


@router.get("/{doc_id}/download")
async def download(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await resume_service.get_document(db, current_user.id, doc_id)
    if doc is None or doc.mode != "built":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Résumé PDF not found.")
    path = resume_service.pdf_path_for(doc_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file missing on disk.")
    return FileResponse(path, media_type="application/pdf", filename=f"resume_{doc_id}.pdf")
