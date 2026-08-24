"""Day 3 API tests: seeded login, JWT validation, role restrictions, read endpoints.

Run from the project root:

    python -m pytest backend/tests/test_api.py -q
"""

from typing import Any, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.models import Base, Employment, Trainee, User
from backend.app.database.session import get_db
from backend.app.main import app
from backend.app.security import create_access_token
from scripts.seed_demo_data import (
    DEMO_ADMIN_EMAIL,
    DEMO_PASSWORD,
    DEMO_PROVIDER_EMAIL,
    DEMO_TRAINEE_EMAIL,
    seed_data,
)


@pytest.fixture()
def api() -> Tuple[TestClient, Session]:
    """TestClient backed by a fresh in-memory seeded database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # share one in-memory DB across all threads
    )
    Base.metadata.create_all(engine)
    db_factory = sessionmaker(bind=engine)
    db = db_factory()
    seed_data(db)
    db.commit()

    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.pop(get_db, None)
        db.close()
        engine.dispose()


def _login(client: TestClient, email: str) -> dict[str, Any]:
    resp = client.post(
        "/api/auth/login", json={"email": email, "password": DEMO_PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Login (success + failure)
# ---------------------------------------------------------------------------
def test_login_success_admin(api):
    client, _ = api
    data = _login(client, DEMO_ADMIN_EMAIL)
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["email"] == DEMO_ADMIN_EMAIL
    assert len(data["access_token"]) > 20


def test_login_returns_no_password_hash(api):
    client, _ = api
    data = _login(client, DEMO_PROVIDER_EMAIL)
    assert "password_hash" not in data
    assert "hash" not in data


def test_login_success_for_each_role(api):
    client, _ = api
    for email, role in [
        (DEMO_ADMIN_EMAIL, "admin"),
        (DEMO_PROVIDER_EMAIL, "provider"),
        (DEMO_TRAINEE_EMAIL, "trainee"),
    ]:
        data = _login(client, email)
        assert data["role"] == role


def test_login_wrong_password(api):
    client, _ = api
    resp = client.post(
        "/api/auth/login",
        json={"email": DEMO_ADMIN_EMAIL, "password": "not-the-password"},
    )
    assert resp.status_code == 401


def test_login_unknown_email(api):
    client, _ = api
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody@sih.gov.in", "password": DEMO_PASSWORD},
    )
    assert resp.status_code == 401


def test_login_missing_fields_is_validation_error(api):
    client, _ = api
    resp = client.post("/api/auth/login", json={"email": DEMO_ADMIN_EMAIL})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------
def test_token_used_on_me_valid(api):
    client, _ = api
    data = _login(client, DEMO_ADMIN_EMAIL)
    resp = client.get("/api/auth/me", headers=_headers(data["access_token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == DEMO_ADMIN_EMAIL
    assert body["role"] == "admin"
    assert "password_hash" not in body


def test_me_without_token_is_401(api):
    client, _ = api
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_garbage_token_is_401(api):
    client, _ = api
    assert client.get("/api/auth/me", headers=_headers("not.a.jwt")).status_code == 401


def test_me_with_expired_token_is_401(api):
    client, db = api
    admin = db.query(User).filter(User.email == DEMO_ADMIN_EMAIL).one()
    token = create_access_token(admin.id, admin.role, admin.email, expires_minutes=-5)
    assert client.get("/api/auth/me", headers=_headers(token)).status_code == 401


# ---------------------------------------------------------------------------
# Role restrictions
# ---------------------------------------------------------------------------
def test_trainee_cannot_list_trainees(api):
    client, _ = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    assert client.get("/api/trainees", headers=_headers(token)).status_code == 403


def test_provider_cannot_list_providers(api):
    client, _ = api
    token = _login(client, DEMO_PROVIDER_EMAIL)["access_token"]
    assert client.get("/api/providers", headers=_headers(token)).status_code == 403


def test_trainee_cannot_list_providers(api):
    client, _ = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    assert client.get("/api/providers", headers=_headers(token)).status_code == 403


def test_admin_can_list_providers(api):
    client, _ = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]
    resp = client.get("/api/providers", headers=_headers(token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_trainee_can_see_own_profile_but_not_others(api):
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    trainee_user = db.query(User).filter(User.email == DEMO_TRAINEE_EMAIL).one()
    own = db.query(Trainee).filter(Trainee.user_id == trainee_user.id).one()

    resp = client.get(f"/api/trainees/{own.id}", headers=_headers(token))
    assert resp.status_code == 200
    assert resp.json()["district"] == own.district

    other = db.query(Trainee).filter(Trainee.id != own.id).first()
    assert other is not None
    resp = client.get(f"/api/trainees/{other.id}", headers=_headers(token))
    assert resp.status_code == 403


def test_trainee_cannot_view_others_employment_history(api):
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    trainee_user = db.query(User).filter(User.email == DEMO_TRAINEE_EMAIL).one()
    own = db.query(Trainee).filter(Trainee.user_id == trainee_user.id).one()
    other = db.query(Trainee).filter(Trainee.id != own.id).first()
    assert other is not None
    resp = client.get(f"/api/trainees/{other.id}/employment", headers=_headers(token))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Basic protected read endpoints
# ---------------------------------------------------------------------------
def test_admin_lists_trainees(api):
    client, _ = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]
    resp = client.get("/api/trainees", headers=_headers(token))
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 1
    assert {"id", "user_id", "district", "education_level", "skills"} <= rows[0].keys()


def test_provider_lists_programs_sees_own_subset(api):
    client, _ = api
    admin_token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]
    provider_token = _login(client, DEMO_PROVIDER_EMAIL)["access_token"]

    admin_programs = client.get("/api/programs", headers=_headers(admin_token)).json()
    provider_programs = client.get(
        "/api/programs", headers=_headers(provider_token)
    ).json()

    assert len(admin_programs) >= len(provider_programs) >= 1
    for prog in provider_programs:
        assert prog["provider_name"] == "Nagpur Skill Development Centre"


def test_trainee_can_read_program_detail(api):
    client, _ = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    resp = client.get("/api/programs/1", headers=_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == 1
    assert isinstance(body["skills"], list)


def test_admin_and_provider_read_employment(api):
    client, db = api
    for email in [DEMO_ADMIN_EMAIL, DEMO_PROVIDER_EMAIL]:
        token = _login(client, email)["access_token"]
        resp = client.get("/api/employment", headers=_headers(token))
        assert resp.status_code == 200
        assert len(resp.json()) == db.query(Employment).count()


def test_trainee_cannot_read_all_employment(api):
    client, _ = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    assert client.get("/api/employment", headers=_headers(token)).status_code == 403


def test_health_is_public(api):
    client, _ = api
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"