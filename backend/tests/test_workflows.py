"""Provider -> create-programme and Trainee -> self-enrollment workflow tests.

Covers the two functional workflows added after the Day-5 demo review:
  * Provider creates a training programme (ownership forced server-side),
  * Trainee browses available programmes and enrols themselves.

Run from the project root:

    python -m pytest backend/tests/test_workflows.py -q
"""

from typing import Any, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.models import (
    Base,
    ProgramEnrollment,
    Skill,
    Trainee,
    TrainingProgram,
    TrainingProvider,
    User,
)
from backend.app.database.session import get_db
from backend.app.main import app
from scripts.seed_demo_data import (
    DEMO_ADMIN_EMAIL,
    DEMO_PASSWORD,
    DEMO_PROVIDER_EMAIL,
    DEMO_TRAINEE_EMAIL,
    seed_data,
)

PROVIDER2_EMAIL = "provider2@sih.gov.in"  # seeded owner of providers[1]
TRAINEE2_EMAIL = "trainee02@example.in"   # seeded owner of trainees[1]


@pytest.fixture()
def api() -> Tuple[TestClient, Session]:
    """TestClient backed by a fresh in-memory seeded database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # share one in-memory DB across all threads
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
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


def _user_id(db: Session, email: str) -> int:
    return db.query(User).filter(User.email == email).one().id


def _own_provider(db: Session, user_id: int) -> TrainingProvider:
    return db.query(TrainingProvider).filter(TrainingProvider.user_id == user_id).one()


def _own_trainee(db: Session, user_id: int) -> Trainee:
    return db.query(Trainee).filter(Trainee.user_id == user_id).one()


def _valid_payload(db: Session, **overrides) -> dict[str, Any]:
    skill_ids = [s.id for s in db.query(Skill).order_by(Skill.id).limit(2)]
    payload: dict[str, Any] = {
        "name": "Synthetic Data Entry Skills",
        "description": "Demo programme created by a workflow test",
        "duration_weeks": 6,
        "status": "active",
        "skill_ids": skill_ids,
    }
    payload.update(overrides)
    return payload


def _first_open_program(db: Session, exclude_program_ids) -> TrainingProgram | None:
    return (
        db.query(TrainingProgram)
        .filter(
            TrainingProgram.status == "active",
            ~TrainingProgram.id.in_(list(exclude_program_ids or [-1])),
        )
        .order_by(TrainingProgram.id)
        .first()
    )


# ---------------------------------------------------------------------------
# Provider: skill catalog + programme creation
# ---------------------------------------------------------------------------
def test_skills_catalog_endpoint(api):
    client, db = api
    token = _login(client, DEMO_PROVIDER_EMAIL)["access_token"]
    resp = client.get("/api/skills", headers=_headers(token))
    assert resp.status_code == 200
    catalog = resp.json()
    assert len(catalog) == db.query(Skill).count() == 10
    assert {"id", "name", "category"} <= set(catalog[0])


def test_provider_can_create_program(api):
    """Provider creates a programme linked to their own provider record."""
    client, db = api
    token = _login(client, DEMO_PROVIDER_EMAIL)["access_token"]
    provider_id = _user_id(db, DEMO_PROVIDER_EMAIL)

    resp = client.post(
        "/api/programs", json=_valid_payload(db), headers=_headers(token)
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()

    own_provider = _own_provider(db, provider_id)
    assert body["provider_id"] == own_provider.id
    assert body["name"] == "Synthetic Data Entry Skills"
    assert body["duration_weeks"] == 6
    assert body["status"] == "active"
    assert len(body["skills"]) == 2

    row = db.query(TrainingProgram).filter(TrainingProgram.id == body["id"]).one()
    assert row.provider_id == own_provider.id          # persisted with JWT-derived owner
    assert sorted(s.id for s in row.skills) == sorted(_valid_payload(db)["skill_ids"])

    listed = client.get("/api/programs", headers=_headers(token)).json()
    assert any(p["id"] == body["id"] for p in listed)


def test_provider_cannot_create_program_for_another_provider(api):
    """Client-supplied ownership hints are ignored; owner always comes from JWT."""
    client, db = api
    token = _login(client, DEMO_PROVIDER_EMAIL)["access_token"]
    other_provider = _own_provider(db, _user_id(db, PROVIDER2_EMAIL))

    payload = _valid_payload(db, provider_id=other_provider.id)  # attacker-supplied field
    resp = client.post("/api/programs", json=payload, headers=_headers(token))
    assert resp.status_code == 201
    created = resp.json()

    own_provider = _own_provider(db, _user_id(db, DEMO_PROVIDER_EMAIL))
    assert created["provider_id"] == own_provider.id != other_provider.id
    assert (
        db.query(TrainingProgram).get(created["id"]).provider_id == own_provider.id
    )


def test_trainee_cannot_create_program(api):
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    resp = client.post(
        "/api/programs",
        json={"name": "Hack", "duration_weeks": 4, "skill_ids": [1]},
        headers=_headers(token),
    )
    assert resp.status_code == 403
    assert db.query(TrainingProgram).count() == 7      # nothing was created


def test_admin_cannot_create_program(api):
    client, db = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]
    resp = client.post(
        "/api/programs",
        json={"name": "Gov", "duration_weeks": 4, "skill_ids": [1]},
        headers=_headers(token),
    )
    assert resp.status_code == 403
    assert db.query(TrainingProgram).count() == 7


def test_unauthenticated_cannot_create_program(api):
    client, _ = api
    resp = client.post("/api/programs", json={"name": "X"})
    assert resp.status_code == 401


def test_create_program_validates_input(api):
    client, db = api
    token = _login(client, DEMO_PROVIDER_EMAIL)["access_token"]

    bad_payloads = [
        {"name": "", "duration_weeks": 4, "skill_ids": [1]},       # empty name
        {"name": "X", "duration_weeks": 0, "skill_ids": [1]},      # duration < 1
        {"name": "X", "duration_weeks": 4, "skill_ids": []},       # no skills taught
        {"name": "X", "duration_weeks": 4, "status": "paused"},    # invalid status
        {"name": "X"},                                             # missing fields
    ]
    for payload in bad_payloads:
        resp = client.post("/api/programs", json=payload, headers=_headers(token))
        assert resp.status_code == 422, payload

    # unknown skill reference: rejected after parsing with a clear 404
    resp = client.post(
        "/api/programs",
        json={"name": "X", "duration_weeks": 4, "skill_ids": [99999]},
        headers=_headers(token),
    )
    assert resp.status_code == 404
    assert db.query(TrainingProgram).count() == 7                  # no partial writes


def test_new_program_hidden_from_other_providers_list(api):
    """Another provider neither sees nor owns the newly created programme."""
    client, db = api
    t1 = _login(client, DEMO_PROVIDER_EMAIL)["access_token"]
    t2 = _login(client, PROVIDER2_EMAIL)["access_token"]

    mine_before = {p["name"] for p in client.get("/api/programs", headers=_headers(t2)).json()}
    other_provider = _own_provider(db, _user_id(db, PROVIDER2_EMAIL))
    resp = client.post(
        "/api/programs",
        json=_valid_payload(db, name="Beekeeping Basics", provider_id=other_provider.id),
        headers=_headers(t1),
    )
    assert resp.status_code == 201
    created_id = resp.json()["id"]

    visible_to_other = client.get("/api/programs", headers=_headers(t2)).json()
    assert created_id not in {p["id"] for p in visible_to_other}
    assert {p["name"] for p in visible_to_other} == mine_before


# ---------------------------------------------------------------------------
# Trainee: available programmes + self-enrollment
# ---------------------------------------------------------------------------
def test_trainee_sees_available_programs_with_enrollment_state(api):
    """The trainee catalog lists every programme annotated with own state."""
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    resp = client.get("/api/programs/available", headers=_headers(token))
    assert resp.status_code == 200
    programs = resp.json()

    assert len(programs) == db.query(TrainingProgram).count()
    assert {p["status"] for p in programs} <= {"active", "closed"}
    assert all({"provider_name", "duration_weeks", "skills"} <= set(p) for p in programs)

    mine = {
        e.program_id: e.completion_status
        for e in db.query(ProgramEnrollment).filter_by(trainee_id=_own_trainee(db, _user_id(db, DEMO_TRAINEE_EMAIL)).id)
    }
    for p in programs:
        assert p["enrolled"] is (p["id"] in mine)
        assert p["enrollment_status"] == mine.get(p["id"])
        if p["enrolled"]:
            assert p["enrollment_status"] in ("enrolled", "completed", "dropped")


def test_available_programs_active_first_then_alphabetical(api):
    client, _ = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    programs = client.get("/api/programs/available", headers=_headers(token)).json()
    keys = [(p["status"], p["name"]) for p in programs]
    assert keys == sorted(keys, key=lambda k: (k[0] != "active", k[1]))


def test_admin_and_provider_cannot_browse_trainee_catalog(api):
    client, _ = api
    for email in (DEMO_ADMIN_EMAIL, DEMO_PROVIDER_EMAIL):
        token = _login(client, email)["access_token"]
        resp = client.get("/api/programs/available", headers=_headers(token))
        assert resp.status_code == 403


def test_trainee_can_enroll_themselves(api):
    """Self-enrolment persists, shows on the dashboard, and flips the flag."""
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    own_trainee = _own_trainee(db, _user_id(db, DEMO_TRAINEE_EMAIL))
    already = [
        e.program_id for e in db.query(ProgramEnrollment).filter_by(trainee_id=own_trainee.id)
    ]
    program = _first_open_program(db, already)
    assert program is not None, "seed leaves no open programme to enrol into"

    resp = client.post(
        "/api/trainees/me/enrollments",
        json={"program_id": program.id},
        headers=_headers(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["trainee_id"] == own_trainee.id
    assert body["program_id"] == program.id
    assert body["completion_status"] == "enrolled"
    assert body["certification_status"] == "none"
    assert body["completion_date"] is None
    assert body["program"]["name"] == program.name          # nested programme summary

    row = (
        db.query(ProgramEnrollment)
        .filter_by(trainee_id=own_trainee.id, program_id=program.id)
        .one()
    )                                                       # actually stored in the DB
    assert row.completion_status == "enrolled"

    listed = client.get("/api/trainees/me/enrollments", headers=_headers(token)).json()
    assert program.id in [e["program_id"] for e in listed]

    avail = {
        p["id"]: p
        for p in client.get("/api/programs/available", headers=_headers(token)).json()
    }
    assert avail[program.id]["enrolled"] is True
    assert avail[program.id]["enrollment_status"] == "enrolled"


def test_duplicate_enrollment_is_rejected(api):
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    own_trainee = _own_trainee(db, _user_id(db, DEMO_TRAINEE_EMAIL))
    already = [
        e.program_id for e in db.query(ProgramEnrollment).filter_by(trainee_id=own_trainee.id)
    ]
    program = _first_open_program(db, already)

    first = client.post(
        "/api/trainees/me/enrollments",
        json={"program_id": program.id},
        headers=_headers(token),
    )
    assert first.status_code == 201

    before = db.query(ProgramEnrollment).count()
    second = client.post(
        "/api/trainees/me/enrollments",
        json={"program_id": program.id},
        headers=_headers(token),
    )
    assert second.status_code == 409
    assert db.query(ProgramEnrollment).count() == before    # no duplicate row


def test_cannot_enroll_in_nonexistent_program(api):
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    before = db.query(ProgramEnrollment).count()
    resp = client.post(
        "/api/trainees/me/enrollments",
        json={"program_id": 99999},
        headers=_headers(token),
    )
    assert resp.status_code == 404
    assert db.query(ProgramEnrollment).count() == before


def test_cannot_enroll_in_closed_program(api):
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    closed = db.query(TrainingProgram).filter(TrainingProgram.status == "closed").first()
    assert closed is not None, "seed should contain a closed programme"
    own_trainee_id = _own_trainee(db, _user_id(db, DEMO_TRAINEE_EMAIL)).id
    already = [
        e.program_id for e in db.query(ProgramEnrollment).filter_by(trainee_id=own_trainee_id)
    ]
    if closed.id in already:
        pytest.skip("demo trainee is already enrolled in the closed programme")

    before = db.query(ProgramEnrollment).count()
    resp = client.post(
        "/api/trainees/me/enrollments",
        json={"program_id": closed.id},
        headers=_headers(token),
    )
    assert resp.status_code == 409
    assert db.query(ProgramEnrollment).count() == before


def test_trainee_cannot_enroll_someone_else(api):
    """No client-side identity field exists; foreign ids cannot be injected."""
    client, db = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    stranger = _own_trainee(db, _user_id(db, TRAINEE2_EMAIL))
    before = db.query(ProgramEnrollment).filter_by(trainee_id=stranger.id).count()
    stranger_program_ids = [
        e.program_id for e in db.query(ProgramEnrollment).filter_by(trainee_id=stranger.id)
    ]
    program = _first_open_program(db, stranger_program_ids)

    resp = client.post(
        "/api/trainees/me/enrollments",
        json={"program_id": program.id, "trainee_id": stranger.id},  # injection attempt
        headers=_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["trainee_id"] != stranger.id         # enroled self, not the stranger
    assert (
        db.query(ProgramEnrollment).filter_by(trainee_id=stranger.id).count() == before
    )                                                       # stranger untouched


def test_provider_and_admin_cannot_use_self_enrollment(api):
    client, _ = api
    for email in (DEMO_ADMIN_EMAIL, DEMO_PROVIDER_EMAIL):
        token = _login(client, email)["access_token"]
        resp = client.post(
            "/api/trainees/me/enrollments",
            json={"program_id": 1},
            headers=_headers(token),
        )
        assert resp.status_code == 403


def test_workflow_endpoints_require_auth(api):
    client, _ = api
    assert client.get("/api/programs/available").status_code == 401
    assert client.get("/api/skills").status_code == 401
    assert client.get("/api/trainees/me/enrollments").status_code == 401
    assert (
        client.post("/api/trainees/me/enrollments", json={"program_id": 1}).status_code
        == 401
    )
