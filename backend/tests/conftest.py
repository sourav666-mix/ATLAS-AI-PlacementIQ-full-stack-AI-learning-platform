# conftest.py - pytest fixtures + test MySQL DB
# FILE: tests/conftest.py
# BATCH 18 (new) - Test bootstrap for the REAL app.
#
# Order matters: DATABASE_URL is forced to a local SQLite file BEFORE
# app.main is imported, so pydantic-settings picks it up (real env vars
# outrank .env). The whole app then runs against test_atlas.sqlite —
# no MySQL needed, nothing touches production.
#
# The `ai_spy` fixture is the heart of the cost-model tests: it replaces
# ai_provider_router.complete with a counting stub AND walks sys.modules to
# swap every already-imported alias (`from ... import complete as ask_ai`
# binds by identity, so patching the router module alone is not enough).

from __future__ import annotations

import asyncio
import os
import pathlib
import sys
import uuid

TEST_DB = pathlib.Path("./test_atlas.sqlite").resolve()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ.setdefault("TESTING", "1")

import pytest  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import helpers  # noqa: E402


def _fresh_db_file():
    if TEST_DB.exists():
        TEST_DB.unlink()


_fresh_db_file()

from app.main import app  # noqa: E402  (must come AFTER the env override)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def client(event_loop):
    """Create the schema on the test DB, then a TestClient for the real app."""
    Base = helpers.get_base()

    async def _create_all():
        try:
            from app.database import engine
        except Exception:
            from sqlalchemy.ext.asyncio import create_async_engine
            engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    event_loop.run_until_complete(_create_all())

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(event_loop):
    """Direct async session on the SAME test DB, for seeding + assertions."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    try:
        from app.database import engine
    except Exception:
        engine = create_async_engine(os.environ["DATABASE_URL"])
    maker = async_sessionmaker(engine, expire_on_commit=False)

    class Runner:
        def run(self, coro):
            return event_loop.run_until_complete(coro)

        def session(self):
            return maker()

    return Runner()


# ---------------------------------------------------------------------------
# AI spy — counts every gateway call; canned JSON keeps services functional
# ---------------------------------------------------------------------------
CANNED = {
    "default": '{"score": 7, "feedback": "Good attempt", "strengths": ["x"], '
               '"weaknesses": ["y"], "follow_up": false, '
               '"next_question": "Explain indexes.", '
               '"title": "Auto Problem", "statement": "Sum two numbers.", '
               '"difficulty": "Easy", "examples": [], "hints": ["h1"], '
               '"optimal_solution": "def f(a,b): return a+b", '
               '"questions": ["Q1", "Q2"], "report": {"strengths": [], '
               '"weaknesses": [], "plan": []}}'
}


class AISpy:
    def __init__(self):
        self.calls = 0
        self.prompts = []

    def reset(self):
        self.calls = 0
        self.prompts = []


@pytest.fixture()
def ai_spy():
    import inspect as _inspect  # noqa: F401
    from app.services import ai_provider_router as router

    spy = AISpy()
    originals = []  # (module, attr_name, original_fn)

    real_complete = getattr(router, "complete", None)
    real_score = getattr(router, "score_answer", None)

    async def fake_complete(*args, **kwargs):
        spy.calls += 1
        spy.prompts.append(str(args[:1]) + str(sorted(kwargs.keys())))
        return CANNED["default"]

    async def fake_score(*args, **kwargs):
        spy.calls += 1
        return CANNED["default"]

    targets = {id(real_complete): fake_complete}
    if real_score is not None:
        targets[id(real_score)] = fake_score

    for mod_name, mod in list(sys.modules.items()):
        if not mod_name.startswith("app.") or mod is None:
            continue
        for attr in dir(mod):
            try:
                value = getattr(mod, attr)
            except Exception:
                continue
            if id(value) in targets:
                originals.append((mod, attr, value))
                setattr(mod, attr, targets[id(value)])

    yield spy

    for mod, attr, value in originals:
        setattr(mod, attr, value)


# ---------------------------------------------------------------------------
# Student factory — register + login through the real auth surface
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def student(client):
    email = f"test_{uuid.uuid4().hex[:8]}@atlas.test"
    password = "Str0ng!Pass123"

    register = (helpers.find_route(app, "POST", "register")
                or helpers.find_route(app, "POST", "signup"))
    assert register, "No register/signup route found on the app"
    reg_variants = [
        {"email": email, "password": password, "full_name": "Test Student"},
        {"email": email, "password": password, "name": "Test Student"},
        {"email": email, "password": password, "full_name": "Test Student",
         "college": "Test College"},
    ]
    response = helpers.request_with_variants(client, "POST", register,
                                             reg_variants)
    assert response is not None and response.status_code < 500, \
        f"register failed: {response.status_code} {response.text[:300]}"

    login = helpers.find_route(app, "POST", "login")
    assert login, "No login route found on the app"
    response = client.post(login, json={"email": email, "password": password})
    if response.status_code == 422:
        response = client.post(login, data={"username": email,
                                            "password": password})
    assert response.status_code == 200, \
        f"login failed: {response.status_code} {response.text[:300]}"
    token = helpers.token_from(response.json())
    assert token, f"no token in login response: {response.text[:300]}"

    headers = {"Authorization": f"Bearer {token}"}
    me = helpers.find_route(app, "GET", "me") or helpers.find_route(
        app, "GET", "auth", "me")
    user_id = None
    if me:
        me_resp = client.get(me, headers=headers)
        if me_resp.status_code == 200:
            body = me_resp.json()
            user_id = body.get("id") or (body.get("user") or {}).get("id")
    return {"email": email, "password": password, "headers": headers,
            "user_id": user_id, "token": token}