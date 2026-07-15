# backend/app/main.py
"""
FastAPI application entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000
Docs:
    http://localhost:8000/docs

Routers are registered in the "ROUTERS" block below. Each future build batch
uncomments its line as that router file is created (service before router,
router before frontend — the project's golden build order).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import company
from app.config import settings
from app.routers import jobs
from app.routers.admin import jobs_admin
from app.routers import championship
from app.routers.admin import championship_admin
from app.routers import interview_studio
from app.routers.admin import auth as admin_auth
from app.routers.admin import colleges as admin_colleges
from app.routers.admin import students as admin_students
#          (the line that imports admin_auth / admin_colleges / admin_students):
from app.routers import dashboard
from app.routers.admin import (
    content as admin_content,
    analytics as admin_analytics,
    providers as admin_providers,
)
from app.models import lab  # noqa: F401

app = FastAPI(
    title=settings.APP_NAME,
    version="10.0.0",
    debug=settings.DEBUG,
)

# --- CORS -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health -----------------------------------------------------------------
@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENVIRONMENT}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

# --- v12 SkillPath Reforged ------------------------------------------------
from app.routers import skillpath_v12

app.include_router(skillpath_v12.router)   # prefix /skillpath is on the router
# --- ROUTERS ----------------------------------------------------------------
# Uncomment each line as the router file is built in its batch.
#
# --- ROUTERS ----------------------------------------------------------------
from app.routers import auth
app.include_router(auth.router, prefix="/auth", tags=["auth"])
from app.routers import daily_progress, domains, plans
app.include_router(daily_progress.router, prefix="/progress", tags=["progress"])
app.include_router(domains.router,        prefix="/domains",  tags=["catalog"])
app.include_router(plans.router,          prefix="/plans",    tags=["catalog"])
from app.routers import roadmap, practice
app.include_router(roadmap.router,  prefix="/roadmap",  tags=["roadmap"])
app.include_router(practice.router, prefix="/practice", tags=["practice"])
from app.routers import tutor_global
app.include_router(tutor_global.router, prefix="/tutor", tags=["assistant"])
from app.routers import assessment
app.include_router(assessment.router, prefix="/assessment", tags=["assessment"])
from app.routers import arena
app.include_router(arena.router, prefix="/arena", tags=["arena"])
from app.routers import resume
app.include_router(resume.router, prefix="/resume", tags=["resume"])
app.include_router(company.router, tags=["company"])

app.include_router(jobs.router)          # student board  -> /jobs
app.include_router(jobs_admin.router)    # admin posting  -> /admin/jobs


app.include_router(championship.router)              # student -> /championship
app.include_router(championship_admin.router)        # admin   -> /admin/championship



app.include_router(interview_studio.router)   # -> /studio

app.include_router(admin_auth.router)        # -> /admin/login, /admin/me, /admin/admins
app.include_router(admin_colleges.router)    # -> /admin/colleges
app.include_router(admin_students.router)    # -> /admin/students
app.include_router(admin_content.router)
app.include_router(admin_analytics.router)
app.include_router(admin_providers.router)
app.include_router(dashboard.router)

# v12 — routers declare their own prefixes (/skillpath, /enrollment)
from app.routers import skillpath_v3, domains_enrollment
app.include_router(skillpath_v3.router)
app.include_router(domains_enrollment.router)

# STEP 1 — add with the existing router imports:

from app.routers import lab as lab_router

# STEP 2 — add with the existing app.include_router(...) block:

app.include_router(lab_router.router)

# --- v12 Live Lab Pro --------------------------------------------------
from app.routers import lab_pro

app.include_router(lab_pro.router)   # prefix /labpro is on the router

# --- v12 content QA ------------------------------------------------------
from app.routers import admin_content_qa

app.include_router(admin_content_qa.router)

# --- v12 Career Target & Gap Engine -----------------------------------------
from app.routers import career

app.include_router(career.router)

# Uncomment each line as the router file is built in its batch.
# ... (leave the rest as-is)
# FILE: app/main.py — BATCH 19 ADDITIVE SNIPPET ONLY (do NOT replace the file)
#
# Add this endpoint anywhere below `app = FastAPI(...)`:

@app.get("/health", tags=["ops"])
async def health():
    """Railway healthcheck — also verifies the DB is reachable."""
    from sqlalchemy import text
    from app.database import engine
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "up"}
    except Exception as exc:
        return {"status": "degraded", "db": f"down: {exc.__class__.__name__}"}

# ALSO (edit, not add): find your existing CORSMiddleware block and make the
# origins list env-driven so Vercel domains work without a code change:
#
#   allow_origins=[o.strip() for o in
#                  os.getenv("FRONTEND_ORIGINS",
#                            "http://localhost:5173,http://localhost:5174"
#                            ).split(",")]
#
# (add `import os` at the top if missing)
#
# from app.routers import code_arena, resume, assessment, company, jobs
# from app.routers import championship, interview_studio, tutor_global, leaderboard
# ...
# Admin subpackage:
# from app.routers.admin import auth as admin_auth
# app.include_router(admin_auth.router,    prefix="/admin/auth", tags=["admin"])