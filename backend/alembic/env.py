# env.py - alembic environment
# backend/alembic/env.py
"""
Alembic environment.

Alembic runs SYNCHRONOUSLY, so we derive a sync DB URL from the app's async
DATABASE_URL:  mysql+aiomysql://  ->  mysql+pymysql://   (and aiosqlite -> sqlite).
You keep a single DATABASE_URL in backend/.env; this file adapts it.

target_metadata = Base.metadata AFTER importing app.models, so every table is
registered and `alembic revision --autogenerate` sees the whole schema.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# --- make the app importable + load settings and ALL models ------------------
from app.config import settings
import app.models  # noqa: F401  (imports every model -> registers every table)
from app.database import Base

config = context.config


# Feed the resolved (sync) URL to Alembic.
def _sync_url(url: str) -> str:
    return url.replace("+aiomysql", "+pymysql").replace("+aiosqlite", "")


config.set_main_option("sqlalchemy.url", _sync_url(settings.DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a DB connection (alembic upgrade --sql)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()