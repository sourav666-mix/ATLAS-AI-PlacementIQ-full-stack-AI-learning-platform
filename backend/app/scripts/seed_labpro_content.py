# backend/app/scripts/seed_labpro_content.py
"""
ATLAS AI 4.0 - v12 Live Lab Pro: OFFLINE content seed.

Run once (or re-run any time - fully idempotent):

    cd backend
    python -m app.scripts.seed_labpro_content

Seeds ONLY metadata:
  * the curated starter dataset catalog into lab_datasets (name, url,
    rows_est, size_kb - the CSV files themselves ship as static assets)

Notebook starter templates need NO seeding at all - they are pure data in
services/labpro_templates.py, cloned into a session at create time.
Zero AI calls in this script.
"""

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal as SessionLocal
from app.models.lab import LabDataset
from app.services.labpro_templates import STARTER_DATASETS, TEMPLATES


async def seed() -> None:
    created, skipped = 0, 0
    async with SessionLocal() as db:
        for spec in STARTER_DATASETS:
            exists = (
                await db.execute(
                    select(LabDataset).where(LabDataset.name == spec["name"])
                )
            ).scalars().first()
            if exists:
                skipped += 1
                continue
            db.add(LabDataset(**spec))
            created += 1
        await db.commit()

    print("Live Lab Pro seed complete")
    print(f"  datasets: {created} created, {skipped} already present")
    summary = ", ".join(
        f"{key} ({len(tpl['cells'])} cells)" for key, tpl in TEMPLATES.items()
    )
    print(f"  templates (no DB rows needed): {summary}")


if __name__ == "__main__":
    asyncio.run(seed())