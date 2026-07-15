# backend/app/scripts/seed_jobs.py
"""Seed a handful of verified, platform-wide job/internship postings.

Because posting normally requires the (not-yet-built) admin app, this script is
the supported way to populate the board today. It inserts curated postings
directly, attributed to an existing admin user.

    py -3.11 -m app.scripts.seed_jobs
    py -3.11 -m app.scripts.seed_jobs --posted-by <admin_users.id>

posted_by must reference an existing admin_users row (FK). If you have not
created an admin yet, pass one explicitly with --posted-by, or create a
super_admin first. Idempotent: skips a posting if the same title+company exists.
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import date, timedelta

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.job import JobPosting

_D = (date.today() + timedelta(days=30)).isoformat()

SEED = [
    dict(kind="job", title="Graduate Software Engineer", company="TCS",
         location="Multiple (India)", work_mode="onsite", ctc_band="3.5–7 LPA",
         required_skills=["Data Structures", "SQL", "OOP", "Aptitude"],
         eligibility={"batches": ["2025", "2026"], "min_cgpa": "6.0+",
                      "branches": ["CSE", "IT", "ECE"]},
         description="Entry-level engineering role via the TCS NQT pipeline.",
         apply_url="https://example.com/apply/tcs"),
    dict(kind="job", title="SDE-1", company="Amazon",
         location="Bengaluru", work_mode="hybrid", ctc_band="18–32 LPA",
         required_skills=["Data Structures", "Algorithms", "System Design", "Python"],
         eligibility={"batches": ["2025"], "min_cgpa": "7.0+",
                      "branches": ["CSE", "IT"]},
         description="Build and own services at scale. Strong DSA expected.",
         apply_url="https://example.com/apply/amazon"),
    dict(kind="internship", title="Data Science Intern", company="Flipkart",
         location="Bengaluru", work_mode="onsite", stipend="₹40,000/mo",
         required_skills=["Python", "SQL", "Machine Learning", "Statistics"],
         eligibility={"batches": ["2026"], "min_cgpa": "7.5+",
                      "branches": ["CSE", "Data Science"]},
         description="6-month internship on the recommendations team.",
         apply_url="https://example.com/apply/flipkart"),
    dict(kind="job", title="Associate Software Engineer", company="Infosys",
         location="Pune / Mysuru", work_mode="onsite", ctc_band="4–6 LPA",
         required_skills=["Java", "SQL", "OOP", "Aptitude"],
         eligibility={"batches": ["2025", "2026"], "min_cgpa": "6.0+",
                      "branches": ["CSE", "IT", "ECE", "EEE"]},
         description="Foundation-program role across Infosys delivery units.",
         apply_url="https://example.com/apply/infosys"),
    dict(kind="internship", title="Cloud Engineering Intern", company="Microsoft",
         location="Hyderabad", work_mode="hybrid", stipend="₹80,000/mo",
         required_skills=["Cloud Computing", "Kubernetes", "Python", "Data Structures"],
         eligibility={"batches": ["2026"], "min_cgpa": "8.0+",
                      "branches": ["CSE", "IT"]},
         description="Azure platform internship with a return-offer track.",
         apply_url="https://example.com/apply/microsoft"),
]


async def _resolve_admin_id(db, override: str | None) -> str | None:
    if override:
        return override
    try:
        from app.models.admin_user import AdminUser
        row = (await db.execute(select(AdminUser).limit(1))).scalars().first()
        return getattr(row, "id", None) if row else None
    except Exception:
        return None


async def seed(posted_by: str | None) -> None:
    async with AsyncSessionLocal() as db:
        admin_id = await _resolve_admin_id(db, posted_by)
        if not admin_id:
            print("  No admin_users row found. Create a super_admin first, or pass "
                  "--posted-by <admin_users.id>. (posted_by is a NOT NULL FK.)")
            return
        for item in SEED:
            exists = (await db.execute(select(JobPosting).where(
                JobPosting.title == item["title"],
                JobPosting.company == item["company"]))).scalar_one_or_none()
            if exists:
                print(f"  skip  {item['company']:12} {item['title']}")
                continue
            db.add(JobPosting(
                id=str(uuid.uuid4()), posted_by=admin_id, college_id=None,
                visibility="all", kind=item["kind"], title=item["title"],
                company=item["company"], location=item.get("location", ""),
                work_mode=item.get("work_mode", "onsite"),
                ctc_band=item.get("ctc_band", ""), stipend=item.get("stipend", ""),
                required_skills_json=item["required_skills"],
                eligibility_json=item["eligibility"],
                description=item.get("description", ""),
                apply_url=item.get("apply_url", ""),
                deadline=date.today() + timedelta(days=30), status="active"))
            print(f"  ok    {item['company']:12} {item['title']}")
        await db.commit()


def main() -> None:
    posted_by = None
    if "--posted-by" in sys.argv:
        i = sys.argv.index("--posted-by")
        if i + 1 < len(sys.argv):
            posted_by = sys.argv[i + 1]
    print("Seeding verified job postings...")
    asyncio.run(seed(posted_by))
    print("Done.")


if __name__ == "__main__":
    main()