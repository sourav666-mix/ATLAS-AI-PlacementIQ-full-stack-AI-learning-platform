# backend/app/scripts/seed_content_library.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — author the 5 shared modules ONCE + map them into domains.

STRUCTURAL seeding only (module_key, title, subtopic list, display_order). NO AI call here —
the AI-authored content (learn cards, questions) attaches to roadmap_topics via the other two
seeders. Idempotent + resumable: re-running only refreshes titles/mappings, never duplicates.

Run:  python -m app.scripts.seed_content_library
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.domain import Domain
from app.models.content_library import ContentLibrary
from app.services import content_dedup_service

# The 5 shared modules (v12 Section 3.1). Subtopics stored as [{name, order}].
SHARED_MODULES = {
    "python": ("Python", ["List", "String", "Loops", "Functions", "Dictionary", "OOP", "Tuple", "Set"]),
    "numpy": ("NumPy", ["Array", "Indexing", "Slicing", "Math Operations", "Aggregation"]),
    "pandas": ("Pandas", ["Data Structures", "Data Inspection", "Selection & Filtering",
                          "Data Cleaning", "Data Transformation", "Grouping & Aggregation",
                          "Combining Datasets", "Time Series"]),
    "dataviz": ("Data Visualization", ["Matplotlib", "Seaborn", "Plotly"]),
    "stats_linalg": ("Statistics, Probability & Linear Algebra",
                     ["Distributions", "Bayes' Theorem", "A/B Testing", "Hypothesis Testing", "Linear Algebra"]),
}

# Which domain (by slug) shows which modules, and in what order (v12 Phase 19).
DOMAIN_MODULE_MAP = {
    "data_science":   [("python", 1), ("numpy", 2), ("pandas", 3), ("dataviz", 4), ("stats_linalg", 5)],
    "data_analysis":  [("python", 1), ("pandas", 2), ("dataviz", 3), ("stats_linalg", 4)],
    "ai":             [("python", 1), ("numpy", 2), ("pandas", 3), ("stats_linalg", 4)],
    "backend_developer": [("python", 1)],
    "cloud_computing":   [("python", 1)],
}


async def _upsert_module(db, key, title, subtopics):
    row = (await db.execute(
        select(ContentLibrary).where(ContentLibrary.module_key == key)
    )).scalar_one_or_none()
    subtopics_json = [{"name": n, "order": i + 1} for i, n in enumerate(subtopics)]
    if row:
        row.title = title
        row.subtopics_json = subtopics_json
    else:
        db.add(ContentLibrary(module_key=key, title=title, subtopics_json=subtopics_json))
    await db.flush()


async def main():
    async with AsyncSessionLocal() as db:
        # 1) author the shared modules once
        for key, (title, subs) in SHARED_MODULES.items():
            await _upsert_module(db, key, title, subs)
        await db.commit()

        # 2) map each module into its domains
        domains = (await db.execute(select(Domain))).scalars().all()
        slug_to_id = {getattr(d, "slug", ""): d.id for d in domains}

        for slug, mods in DOMAIN_MODULE_MAP.items():
            domain_id = slug_to_id.get(slug)
            if not domain_id:
                print(f"[skip] domain slug '{slug}' not found")
                continue
            for module_key, order in mods:
                await content_dedup_service.map_module_into_domain(db, domain_id, module_key, order)
            print(f"[ok] mapped {len(mods)} modules into {slug}")
        await db.commit()
    print("seed_content_library: done")


if __name__ == "__main__":
    asyncio.run(main())