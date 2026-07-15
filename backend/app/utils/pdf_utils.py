# pdf_utils.py - ReportLab helpers shared by resume + reports
# backend/app/utils/pdf_utils.py
"""
PDF/document utilities for Resume AI.

extract_text() : pull plain text out of an uploaded PDF / DOCX / TXT résumé.
build_resume_pdf() : render structured résumé JSON into a clean one-page ATS PDF
                     (reportlab). Returns raw PDF bytes.

Heavy imports are done lazily so importing this module is cheap.
"""
import io
from typing import Optional


def extract_text(file_bytes: bytes, filename: Optional[str]) -> str:
    """Extract text from a résumé upload. Supports .pdf, .docx, and plain text."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        import pdfplumber
        parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()
    if name.endswith(".docx"):
        import docx
        d = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in d.paragraphs).strip()
    # txt / unknown -> best-effort decode
    return file_bytes.decode("utf-8", errors="ignore").strip()


def build_resume_pdf(resume: dict, template: str = "classic_ats") -> bytes:
    """
    Render a one-page ATS-friendly résumé PDF from structured content.

    Expected `resume` keys (all optional except full_name):
        full_name, email, phone, location, summary,
        skills: [str],
        experience: [{title, company, dates, bullets: [str]}],
        education: [{degree, institution, year}],
        projects: [{name, description}]
    """
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    base = getSampleStyleSheet()
    accent = colors.HexColor("#1f3a5f")
    name_style = ParagraphStyle("Name", parent=base["Title"], fontSize=20, spaceAfter=2, alignment=TA_CENTER, textColor=accent)
    contact_style = ParagraphStyle("Contact", parent=base["Normal"], fontSize=9, alignment=TA_CENTER, textColor=colors.grey)
    section_style = ParagraphStyle("Section", parent=base["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=2, textColor=accent)
    body = ParagraphStyle("Body", parent=base["Normal"], fontSize=9.5, leading=13)
    item_head = ParagraphStyle("ItemHead", parent=body, fontName="Helvetica-Bold")
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=12, bulletIndent=2)

    story = []

    def section(title: str):
        story.append(Paragraph(title.upper(), section_style))
        story.append(HRFlowable(width="100%", thickness=0.6, color=accent, spaceAfter=4))

    # header
    story.append(Paragraph(resume.get("full_name", "Your Name"), name_style))
    contact_bits = [resume.get(k) for k in ("email", "phone", "location") if resume.get(k)]
    if contact_bits:
        story.append(Paragraph("  |  ".join(contact_bits), contact_style))
    story.append(Spacer(1, 6))

    if resume.get("summary"):
        section("Summary")
        story.append(Paragraph(resume["summary"], body))

    exp = resume.get("experience") or []
    if exp:
        section("Experience")
        for e in exp:
            head = f"{e.get('title', '')} — {e.get('company', '')}"
            dates = e.get("dates", "")
            story.append(Paragraph(f"{head}" + (f"  <font color='grey'>({dates})</font>" if dates else ""), item_head))
            for b in e.get("bullets", []) or []:
                story.append(Paragraph(b, bullet, bulletText="•"))
            story.append(Spacer(1, 4))

    proj = resume.get("projects") or []
    if proj:
        section("Projects")
        for p in proj:
            story.append(Paragraph(p.get("name", ""), item_head))
            if p.get("description"):
                story.append(Paragraph(p["description"], body))
            story.append(Spacer(1, 3))

    edu = resume.get("education") or []
    if edu:
        section("Education")
        for ed in edu:
            line = f"{ed.get('degree', '')} — {ed.get('institution', '')}"
            year = ed.get("year", "")
            story.append(Paragraph(line + (f"  <font color='grey'>({year})</font>" if year else ""), body))

    skills = resume.get("skills") or []
    if skills:
        section("Skills")
        story.append(Paragraph(", ".join(skills), body))

    doc.build(story)
    return buf.getvalue()


__all__ = ["extract_text", "build_resume_pdf"]