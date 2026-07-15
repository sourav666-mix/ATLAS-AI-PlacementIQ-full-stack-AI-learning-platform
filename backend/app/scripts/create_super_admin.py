# backend/app/scripts/create_super_admin.py
"""Bootstrap the FIRST super_admin (chicken-and-egg: /admin/admins needs one).

    py -3.11 -m app.scripts.create_super_admin admin@atlasai.in "StrongPass123" "Sourav"

Idempotent: if the email already exists, it offers a password reset instead of
duplicating. This admin's id also unblocks the Batch 12/13 seed scripts, which
need an admin_users row for their posted_by / created_by foreign keys.
"""
from __future__ import annotations

import asyncio
import sys
import uuid

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser
from app.services.admin_auth_service import hash_admin_password


async def run(email: str, password: str, name: str) -> None:
    email = email.strip().lower()
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(AdminUser).where(
            AdminUser.email == email))).scalar_one_or_none()
        if existing:
            existing.hashed_password = hash_admin_password(password)
            await db.commit()
            print(f"  admin '{email}' already existed — password reset. "
                  f"(id={existing.id}, role={existing.role})")
            return
        admin = AdminUser(id=str(uuid.uuid4()), email=email,
                          hashed_password=hash_admin_password(password),
                          role="super_admin")
        if hasattr(admin, "full_name"):
            admin.full_name = name
        db.add(admin)
        await db.commit()
        print(f"  super_admin created: {email}  (id={admin.id})")
        print(f"  -> login at POST /admin/login, then use this id for "
              f"seed_jobs.py --posted-by / seed_championship.py --created-by")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: py -3.11 -m app.scripts.create_super_admin "
              "<email> <password> [name]")
        sys.exit(1)
    email, password = sys.argv[1], sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "Super Admin"
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)
    asyncio.run(run(email, password, name))
    print("Done.")


if __name__ == "__main__":
    main()