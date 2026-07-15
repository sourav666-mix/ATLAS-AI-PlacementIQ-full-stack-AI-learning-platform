# test_auth.py - auth + JWT flow
# FILE: tests/test_auth.py
# BATCH 18 (new) - Critical path 1: register -> login -> me, wrong password
# rejected, protected routes reject missing tokens.

from __future__ import annotations

import helpers
from conftest import app


def test_register_login_me(client, student):
    # The session-scoped `student` fixture already exercised register + login.
    assert student["token"], "login must return a bearer token"
    me = helpers.find_route(app, "GET", "me") or helpers.find_route(
        app, "GET", "auth", "me")
    if not me:
        import pytest
        pytest.skip("No /me route found — report so we pin the auth surface")
    response = client.get(me, headers=student["headers"])
    assert response.status_code == 200, response.text[:300]
    assert student["email"].split("@")[0] in response.text or \
        "email" in response.text.lower()


def test_wrong_password_rejected(client, student):
    login = helpers.find_route(app, "POST", "login")
    response = client.post(login, json={"email": student["email"],
                                        "password": "definitely-wrong"})
    if response.status_code == 422:
        response = client.post(login, data={"username": student["email"],
                                            "password": "definitely-wrong"})
    assert response.status_code in (400, 401, 403), \
        f"wrong password must be rejected, got {response.status_code}"


def test_protected_route_requires_token(client):
    me = helpers.find_route(app, "GET", "me") or helpers.find_route(
        app, "GET", "dashboard")
    if not me:
        import pytest
        pytest.skip("No protected route discovered to probe")
    response = client.get(me)
    assert response.status_code in (401, 403), \
        f"missing token must be rejected, got {response.status_code}"