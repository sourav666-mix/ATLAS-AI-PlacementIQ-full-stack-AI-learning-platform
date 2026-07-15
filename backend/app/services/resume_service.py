# resume_service.py - [MOD] PDF/DOCX parse, NLP matcher, STAR, top-3 questions
# backend/app/services/resume_service.py
"""
Resume AI 2.0 — analyzer + builder.

analyze() : extract text from an uploaded résumé, then AI-analyze against a JD
            (ATS score, JD match, STAR feedback, predicted questions). Falls back
            to a deterministic heuristic when no AI provider is configured.
build()   : render structured résumé content into a real PDF (reportlab), persist
            the file, and store a ResumeDocument row.

Both modes feed the profile bar's resume_completeness (analyzed=50, built=100),
so completion triggers a profile-bar recompute.
"""
import base64
import json
import os
import re
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.resume_doc import ResumeDocument
from app.services import ai_provider_router, prompts, progress_engine
from app.utils import pdf_utils


def _resume_dir() -> str:
    path = os.path.join(settings.STORAGE_DIR, "resumes")
    os.makedirs(path, exist_ok=True)
    return path


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9\+\#]+", (text or "").lower()))


# common words to ignore when suggesting "missing" JD keywords in the fallback
_STOPWORDS = {
    "a", "an", "and", "or", "the", "for", "with", "in", "on", "of", "to", "as",
    "is", "are", "be", "you", "your", "we", "our", "who", "will", "looking",
    "skilled", "experience", "strong", "good", "must", "should", "have", "has",
    "using", "work", "role", "team", "ability", "including", "etc", "such",
}


# ============================================================================
# analyze
# ============================================================================
def _local_analysis(resume_text: str, jd_text: str) -> dict:
    r = _tokens(resume_text)
    jd = _tokens(jd_text)
    # ATS heuristic: rewards contact info + standard sections
    has_email = bool(re.search(r"[\w.\-]+@[\w.\-]+", resume_text))
    has_phone = bool(re.search(r"\d{7,}", resume_text))
    sections = sum(kw in r for kw in ("experience", "education", "skills", "projects", "summary"))
    ats = min(100, 30 + sections * 12 + (10 if has_email else 0) + (8 if has_phone else 0))
    # JD match: keyword overlap
    match = round(len(r & jd) / len(jd) * 100) if jd else 0
    missing = sorted(w for w in (jd - r) if len(w) > 2 and w not in _STOPWORDS)[:8]
    return {
        "ats_score": ats,
        "jd_match_score": match,
        "star_feedback": "Use the STAR format (Situation, Task, Action, Result) and quantify results "
                         "with numbers where possible.",
        "top_questions": [
            "Walk me through your most impactful project.",
            "Which skill on this JD are you strongest in, and why?",
            "Describe a time you improved a metric — what and by how much?",
        ],
        "strengths": [f"Covers {sections} standard résumé sections."] + (["Includes contact details."] if has_email else []),
        "improvements": (["Add or emphasize: " + ", ".join(missing)] if missing else
                         ["Add quantified achievements to each role."]),
    }


async def _ai_analysis(resume_text: str, jd_text: str) -> Optional[dict]:
    try:
        text = await ai_provider_router.complete(
            prompts.resume_analyze_system(),
            prompts.resume_analyze_user(resume_text, jd_text),
        )
        data = ai_provider_router.parse_json(text)
        return {
            "ats_score": int(max(0, min(100, int(data.get("ats_score", 0))))),
            "jd_match_score": int(max(0, min(100, int(data.get("jd_match_score", 0))))),
            "star_feedback": str(data.get("star_feedback", "")),
            "top_questions": list(data.get("top_questions", []))[:3],
            "strengths": list(data.get("strengths", [])),
            "improvements": list(data.get("improvements", [])),
        }
    except Exception:
        return None


def _skill_overlap(resume_text: str, jd_text: str) -> tuple[list[str], list[str]]:
    """JD terms present in / absent from the résumé (for the matcher chips)."""
    if not jd_text:
        return [], []
    r, jd = _tokens(resume_text), _tokens(jd_text)
    terms = [w for w in sorted(jd) if len(w) > 2 and w not in _STOPWORDS]
    return [w for w in terms if w in r][:12], [w for w in terms if w not in r][:8]


async def analyze(db: AsyncSession, user_id: str, file_bytes: bytes, filename: str, jd_text: str) -> dict:
    resume_text = pdf_utils.extract_text(file_bytes, filename)
    if not resume_text:
        raise ValueError("Could not read any text from the uploaded file.")

    analysis = await _ai_analysis(resume_text, jd_text) or _local_analysis(resume_text, jd_text)
    matched, missing = _skill_overlap(resume_text, jd_text)

    doc = ResumeDocument(
        user_id=user_id, mode="analyzed", source_file=filename,
        jd_text=jd_text or None, analysis_json=analysis,
        # keep the extracted text so /resume/rebuild can restructure it later
        resume_json={"resume_text": resume_text[:20000]},
    )
    db.add(doc)
    await db.flush()
    await progress_engine.recompute_profile_bar(db, user_id)
    await db.commit()
    await db.refresh(doc)

    return {
        "document_id": doc.id,
        "analysis_id": doc.id,
        "match_score": analysis.get("jd_match_score") if jd_text else None,
        "matched_skills": matched,
        "missing_skills": missing,
        **analysis,
    }


# ============================================================================
# build
# ============================================================================
async def build(db: AsyncSession, user_id: str, resume_json: dict, template: str, pages: int = 1) -> ResumeDocument:
    doc = ResumeDocument(
        user_id=user_id, mode="built", resume_json=resume_json,
        template=template, pages=pages,
    )
    db.add(doc)
    await db.flush()  # get doc.id

    pdf_bytes = pdf_utils.build_resume_pdf(resume_json, template)
    path = os.path.join(_resume_dir(), f"{doc.id}.pdf")
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    doc.pdf_url = f"/resume/{doc.id}/download"

    await progress_engine.recompute_profile_bar(db, user_id)
    await db.commit()
    await db.refresh(doc)
    return doc


def pdf_path_for(doc_id: str) -> str:
    return os.path.join(_resume_dir(), f"{doc_id}.pdf")


def pdf_base64_for(doc_id: str) -> Optional[str]:
    """Base64 of the stored PDF, so the SPA can offer a data-URL download."""
    path = pdf_path_for(doc_id)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


# ============================================================================
# builder (Mode B): guided form -> AI draft -> edited draft -> PDF
# ============================================================================
def _fallback_draft(form: dict) -> dict:
    """Deterministic draft when no AI provider is configured."""
    skills = [s for s in (form.get("skills") or []) if s]
    spec = form.get("specialization") or "Software"
    summary = (
        f"{spec} candidate with hands-on project experience in "
        f"{', '.join(skills[:4]) if skills else 'modern tooling'}. "
        "Focused on shipping measurable, production-quality work and learning fast."
    )
    projects = []
    for p in form.get("projects") or []:
        if not (p.get("name") or p.get("description")):
            continue
        desc = (p.get("description") or "").strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", desc) if s.strip()]
        bullets = [s.rstrip(".") + "." for s in sentences[:3]] or [
            f"Built {p.get('name') or 'the project'} using {p.get('tech') or 'modern tools'}."
        ]
        projects.append({"name": p.get("name") or "Project",
                         "tech": p.get("tech") or "", "bullets": bullets})
    experience = []
    for e in form.get("experience") or []:
        if not (e.get("role") or e.get("company")):
            continue
        details = (e.get("details") or "").strip()
        experience.append({
            "title": e.get("role") or "", "company": e.get("company") or "",
            "dates": e.get("duration") or "",
            "bullets": [details] if details else [],
        })
    return {"summary": summary, "projects": projects, "experience": experience}


async def draft_resume(form: dict) -> dict:
    """Form inputs -> editable draft (the LivePreview shape). AI with fallback."""
    generated = None
    try:
        text = await ai_provider_router.complete(
            prompts.resume_draft_system(),
            prompts.resume_draft_user(json.dumps(form, ensure_ascii=False)),
        )
        data = ai_provider_router.parse_json(text)
        if data.get("summary") or data.get("projects"):
            generated = data
    except Exception:
        generated = None
    if generated is None:
        generated = _fallback_draft(form)

    return {
        "full_name": form.get("full_name") or "",
        "email": form.get("email") or "",
        "phone": form.get("phone") or "",
        "address": form.get("address") or "",
        "linkedin": form.get("linkedin") or "",
        "github": form.get("github") or "",
        "skills": [s for s in (form.get("skills") or []) if s],
        "education": form.get("education") or [],
        "summary": generated.get("summary") or "",
        "projects": generated.get("projects") or [],
        "experience": generated.get("experience") or [],
    }


def draft_to_resume_json(draft: dict) -> dict:
    """Map the edited LivePreview draft to the shape build_resume_pdf expects."""
    projects = []
    for p in draft.get("projects") or []:
        name = p.get("name") or "Project"
        if p.get("tech"):
            name = f"{name} ({p['tech']})"
        description = p.get("description") or " ".join(p.get("bullets") or [])
        projects.append({"name": name, "description": description})
    experience = []
    for e in draft.get("experience") or []:
        bullets = e.get("bullets") or ([e["details"]] if e.get("details") else [])
        experience.append({
            "title": e.get("title") or e.get("role") or "",
            "company": e.get("company") or "",
            "dates": e.get("dates") or e.get("duration") or "",
            "bullets": [b for b in bullets if b],
        })
    education = []
    for ed in draft.get("education") or []:
        degree = ed.get("degree") or ""
        if ed.get("score"):
            degree = f"{degree} ({ed['score']})" if degree else str(ed["score"])
        education.append({"degree": degree, "institution": ed.get("institution") or "",
                          "year": ed.get("year") or ""})
    return {
        "full_name": draft.get("full_name") or "Your Name",
        "email": draft.get("email") or None,
        "phone": draft.get("phone") or None,
        "location": draft.get("address") or draft.get("location") or None,
        "summary": draft.get("summary") or None,
        "skills": [s for s in (draft.get("skills") or []) if s],
        "experience": [e for e in experience if e["title"] or e["company"]],
        "education": [e for e in education if any(e.values())],
        "projects": [p for p in projects if p["name"] != "Project" or p["description"]],
    }


# ============================================================================
# rebuild (Mode A follow-up): analyzed doc -> improved ATS PDF
# ============================================================================
def _heuristic_structuring(resume_text: str) -> dict:
    """No-AI fallback: pull contact details and use the text as the summary."""
    lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]
    email = re.search(r"[\w.\-]+@[\w.\-]+", resume_text)
    phone = re.search(r"\+?\d[\d\s\-]{7,}\d", resume_text)
    name = next((ln for ln in lines[:5] if "@" not in ln and len(ln.split()) <= 5),
                "Your Name")
    return {
        "full_name": name,
        "email": email.group(0) if email else None,
        "phone": phone.group(0).strip() if phone else None,
        "summary": " ".join(lines)[:600],
        "skills": [], "experience": [], "education": [], "projects": [],
    }


async def rebuild(db: AsyncSession, user_id: str, analysis_id: str, template: str) -> ResumeDocument:
    src = await get_document(db, user_id, analysis_id)
    if src is None or src.mode != "analyzed":
        raise ValueError("Analysis not found — run Analyze first.")
    resume_text = (src.resume_json or {}).get("resume_text") or ""
    if not resume_text:
        raise ValueError("The original résumé text is no longer stored — please re-analyze the file.")

    improvements = (src.analysis_json or {}).get("improvements", [])
    resume_json = None
    try:
        text = await ai_provider_router.complete(
            prompts.resume_rebuild_system(),
            prompts.resume_rebuild_user(resume_text, src.jd_text or "", improvements),
        )
        data = ai_provider_router.parse_json(text)
        if data.get("full_name") or data.get("summary") or data.get("experience"):
            resume_json = data
    except Exception:
        resume_json = None
    if resume_json is None:
        resume_json = _heuristic_structuring(resume_text)

    return await build(db, user_id, resume_json, template)


# ============================================================================
# reads
# ============================================================================
async def get_document(db: AsyncSession, user_id: str, doc_id: str) -> Optional[ResumeDocument]:
    doc = await db.get(ResumeDocument, doc_id)
    if doc is None or doc.user_id != user_id:
        return None
    return doc


async def get_history(db: AsyncSession, user_id: str, limit: int = 20) -> list[ResumeDocument]:
    rows = (
        await db.execute(
            select(ResumeDocument)
            .where(ResumeDocument.user_id == user_id)
            .order_by(desc(ResumeDocument.created_at))
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)


__all__ = [
    "analyze", "build", "draft_resume", "draft_to_resume_json", "rebuild",
    "get_document", "get_history", "pdf_path_for", "pdf_base64_for",
]