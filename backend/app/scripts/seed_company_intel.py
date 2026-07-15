# backend/app/scripts/seed_company_intel.py
"""Pre-warm Company Intel reports for a few flagship recruiters.

Run once (or occasionally) so the demo/dashboard has instant cached reports
instead of a cold first-view AI wait. Idempotent: skips companies whose cache
is still fresh unless you pass --force. Spreads calls across providers via the
same ask_ai rotation used everywhere else.

    py -3.11 -m app.scripts.seed_company_intel
    py -3.11 -m app.scripts.seed_company_intel --force
    py -3.11 -m app.scripts.seed_company_intel tcs infosys amazon
"""
from __future__ import annotations

import asyncio
import sys

# --- INTEGRATION POINT: async session factory from your database.py ---------
from app.database import AsyncSessionLocal  # adjust if yours is named differently
# ---------------------------------------------------------------------------
from app.services import company_intel_service, company_registry

# Sensible default demo set (kept small to respect free-tier limits).
DEFAULT_SLUGS = ["tcs", "infosys", "wipro", "accenture", "amazon", "microsoft"]


async def seed(slugs: list[str], force: bool) -> None:
    async with AsyncSessionLocal() as db:
        for raw in slugs:
            slug = company_registry.resolve_slug(raw)
            if not slug:
                print(f"  skip  {raw!r:20} (not in registry)")
                continue
            try:
                resp = await company_intel_service.get_report(db, slug, force=force)
                tag = "cached" if resp.cached else "generated"
                print(f"  ok    {slug:20} ({tag}, {len(resp.report.required_skills)} skills)")
            except Exception as exc:  # keep going on a single failure
                print(f"  FAIL  {slug:20} {type(exc).__name__}: {exc}")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    force = "--force" in sys.argv or "-f" in sys.argv
    slugs = args or DEFAULT_SLUGS
    print(f"Seeding Company Intel ({'force' if force else 'fresh-only'}): {', '.join(slugs)}")
    asyncio.run(seed(slugs, force))
    print("Done.")


if __name__ == "__main__":
    main()