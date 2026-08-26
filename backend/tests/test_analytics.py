"""Day 4 tests: analytics computations + read-only analytics API.

Covers employment metrics, skill-gap calculation, programme comparison,
empty/missing-data cases, API response structure, admin-only access, and
unauthorised access. Run from the project root:

    python -m pytest backend/tests/test_analytics.py -q
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.models import (
    Base,
    Employment,
    JobDemand,
    Skill,
    Trainee,
    TrainingProgram,
    TrainingProvider,
    User,
    trainee_skills,
)
from backend.app.database.session import get_db
from backend.app.main import app

from analytics.employment.service import employment_outcomes
from analytics.program_impact.service import program_impact_analysis
from analytics.skill_gap.service import skill_gap_analysis

from scripts.seed_demo_data import (
    DEMO_ADMIN_EMAIL,
    DEMO_PASSWORD,
    DEMO_PROVIDER_EMAIL,
    DEMO_TRAINEE_EMAIL,
    seed_data,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------
@pytest.fixture()
def seeded_db():
    """In-memory SQLite populated by the demo-data seed script."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    seed_data(db)
    db.commit()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture()
def api(seeded_db):
    """TestClient with a fresh seeded in-memory DB and dependency override."""

    def _get_db():
        yield seeded_db

    app.dependency_overrides[get_db] = _get_db
    try:
        with TestClient(app) as client:
            yield client, seeded_db
    finally:
        app.dependency_overrides.pop(get_db, None)


def _login(client: TestClient, email: str) -> dict:
    resp = client.post(
        "/api/auth/login", json={"email": email, "password": DEMO_PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _blank_session():
    """Empty in-memory SQLite session (schema only, no rows)."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


# ---------------------------------------------------------------------------
# Employment-outcome calculations (docs/DATABASE.md §3.1)
# ---------------------------------------------------------------------------
def test_employment_overall_metrics_against_seed(seeded_db):
    """Overall rates agree with manually-counted seeded demo numbers."""
    result = employment_outcomes(seeded_db)
    overall = result["overall"]

    # Seed: 28 enrollments, 26 completed => 92.86%.
    assert overall["completion"]["total_enrollments"] == 28
    assert overall["completion"]["completed_enrollments"] == 26
    assert overall["completion"]["completion_rate"] == round(26 / 28 * 100, 2)

    # Seed: all 24 trainees have an employment status; 21 are employed.
    assert overall["employment"]["available"] == 24
    assert overall["employment"]["employed"] == 21
    assert overall["employment"]["employment_rate"] == 87.5

    # Every employed trainee is relevant except the Data Entry Operator.
    assert overall["relevant_employment"]["employed"] == 21
    assert overall["relevant_employment"]["relevant"] == 20
    assert overall["relevant_employment"]["relevant_employment_rate"] == round(20 / 21 * 100, 2)

    # Retention is a bounded rate (0..100) with placed <= employed.
    assert 0 <= overall["retention"]["placed"] <= 21
    assert 0 <= overall["retention"]["retained"] <= overall["retention"]["placed"]
    retention_value = overall["retention"]["retention_rate"]
    assert retention_value is None or 0.0 <= retention_value <= 100.0

    # Per-program breakdown covers all seven seeded programmes.
    assert {p["program_id"] for p in result["by_program"]} == {1, 2, 3, 4, 5, 6, 7}
    prog0 = next(p for p in result["by_program"] if p["program_id"] == 1)
    assert prog0["completed_enrollments"] == 6
    assert prog0["total_enrollments"] == 6


def test_employment_per_program_row_structure(seeded_db):
    result = employment_outcomes(seeded_db)
    row = result["by_program"][0]
    assert {
        "program_id", "program_name", "provider_name", "status",
        "enrolled_trainees", "total_enrollments", "completed_enrollments",
        "completion_rate", "employed", "available", "employment_rate",
        "relevant", "relevant_employment_rate", "placed", "retained",
        "retention_rate",
    } <= set(row)


def test_employment_retention_deterministic_custom():
    """Retention window is exact on a hand-built dataset with known dates."""
    engine, eng = _blank_session()
    owner = User(email="p@x.in", password_hash="x", role="provider")
    provider = TrainingProvider(user=owner, name="C", district="Pune")
    prog = TrainingProgram(
        provider=provider, name="P", description="", duration_weeks=4, status="active"
    )
    skill = Skill(name="Python", category="IT")
    prog.skills = [skill]
    eng.add_all([owner, skill, prog])
    eng.flush()

    specs = [
        ("employed", date(2024, 1, 1), True),
        ("employed", date(2024, 1, 1), False),
        ("employed", date(2025, 8, 1), True),  # too recent for the window
        ("unemployed", None, False),
    ]
    for i, (status, start, still) in enumerate(specs):
        tu = User(email=f"t{i}@x.in", password_hash="x", role="trainee")
        trainee = Trainee(user=tu, district="Pune", education_level="12th")
        emp = Employment(
            trainee=trainee, status=status, job_role="Developer",
            industry="IT", start_date=start, still_employed=still,
        )
        eng.add_all([tu, trainee, emp])
        eng.flush()
        eng.execute(
            trainee_skills.insert().values(
                trainee_id=trainee.id, skill_id=skill.id, proficiency_level=3
            )
        )
    eng.commit()

    # as_of = 2025-08-01 (max start); cutoff = -90 days = 2025-05-03.
    # Placed = trainees 0,1 (started <= cutoff & employed); retained = only 0.
    result = employment_outcomes(eng)
    assert result["overall"]["employment"]["available"] == 4
    assert result["overall"]["employment"]["employed"] == 3
    assert result["overall"]["employment"]["employment_rate"] == 75.0
    assert result["overall"]["retention"]["placed"] == 2
    assert result["overall"]["retention"]["retained"] == 1
    assert result["overall"]["retention"]["retention_rate"] == 50.0
    eng.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# Skill-gap calculations (docs/DATABASE.md §3.2)
# ---------------------------------------------------------------------------
def test_skill_gap_against_seed(seeded_db):
    """Gap = demand - supply; skills with no trained supply are flagged."""
    result = skill_gap_analysis(seeded_db)

    # Seed demand for Python Programming is 120 (Pune, Software Developer).
    py = next(s for s in result["skills"] if s["required_skill"] == "Python Programming")
    assert py["demand"] == 120
    assert py["supply"] > 0
    assert py["gap"] == py["demand"] - py["supply"]
    assert py["status"] == "high-demand-low-supply"

    # Plumbing and Tailoring have demand but zero trained supply.
    plumbing = next(s for s in result["skills"] if s["required_skill"] == "Plumbing")
    assert plumbing["demand"] == 45
    assert plumbing["supply"] == 0
    assert plumbing["gap"] == 45

    # Every skill row obeys gap = demand - supply.
    for s in result["skills"]:
        assert s["gap"] == s["demand"] - s["supply"]

    # High-demand/low-supply list is sorted by gap desc and non-empty.
    flagged = result["high_demand_low_supply"]
    assert flagged and all(g["gap"] > 0 for g in flagged)
    assert [g["gap"] for g in flagged] == sorted((g["gap"] for g in flagged), reverse=True)

    # District roll-up is present and consistent.
    districts = {d["district"] for d in result["by_district"]}
    assert districts <= {"Pune", "Nagpur", "Nashik", "Aurangabad"}
    for d in result["by_district"]:
        assert d["total_gap"] == d["total_demand"] - d["total_supply"]
        for s in d["skills"]:
            assert s["gap"] == s["demand"] - s["supply"]


def test_skill_gap_deterministic_custom():
    """Exact gap math on a hand-built dataset (incl. proficiency threshold)."""
    engine, eng = _blank_session()

    py = Skill(name="Python", category="IT")
    plumb = Skill(name="Plumbing", category="Construction")
    eng.add_all([py, plumb])
    eng.flush()

    def _trainee(email, district):
        u = User(email=email, password_hash="x", role="trainee")
        t = Trainee(user=u, district=district, education_level="10th")
        eng.add_all([u, t])
        eng.flush()
        return t

    t1 = _trainee("t1@x.in", "Pune")  # skilled (proficiency 3)
    t2 = _trainee("t2@x.in", "Pune")  # below threshold (proficiency 1)
    t3 = _trainee("t3@x.in", "Nagpur")  # skilled (proficiency 3)

    eng.execute(
        trainee_skills.insert().values(trainee_id=t1.id, skill_id=py.id, proficiency_level=3)
    )
    eng.execute(
        trainee_skills.insert().values(trainee_id=t2.id, skill_id=py.id, proficiency_level=1)
    )
    eng.execute(
        trainee_skills.insert().values(trainee_id=t3.id, skill_id=py.id, proficiency_level=3)
    )
    eng.add_all(
        [
            JobDemand(job_role="Dev", industry="IT", district="Pune",
                      required_skill="Python", demand_quantity=10),
            JobDemand(job_role="Dev", industry="IT", district="Nagpur",
                      required_skill="Python", demand_quantity=5),
            JobDemand(job_role="Plumber", industry="Construction", district="Pune",
                      required_skill="Plumbing", demand_quantity=3),
        ]
    )
    eng.commit()

    result = skill_gap_analysis(eng)

    py_row = next(s for s in result["skills"] if s["required_skill"] == "Python")
    # Demand 15; supply counts only proficiency >= 3 => t1 + t3 = 2.
    assert py_row["demand"] == 15
    assert py_row["supply"] == 2
    assert py_row["gap"] == 13

    plumb_row = next(s for s in result["skills"] if s["required_skill"] == "Plumbing")
    assert plumb_row == {
        "required_skill": "Plumbing", "demand": 3, "supply": 0,
        "gap": 3, "status": "high-demand-low-supply",
    }

    by_district = {d["district"]: d for d in result["by_district"]}
    pune_py = next(s for s in by_district["Pune"]["skills"] if s["required_skill"] == "Python")
    assert pune_py["demand"] == 10 and pune_py["supply"] == 1 and pune_py["gap"] == 9
    nagpur_py = next(s for s in by_district["Nagpur"]["skills"] if s["required_skill"] == "Python")
    assert nagpur_py["demand"] == 5 and nagpur_py["supply"] == 1 and nagpur_py["gap"] == 4
    eng.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# Programme impact / comparison (docs/DATABASE.md §3.3)
# ---------------------------------------------------------------------------
def test_program_impact_ranking_against_seed(seeded_db):
    result = program_impact_analysis(seeded_db)

    assert "correlation" in result["framing"].lower()
    assert {r["program_id"] for r in result["ranking"]} == {1, 2, 3, 4, 5, 6, 7}

    # Ranking is sorted by composite_score descending.
    scores = [r["composite_score"] for r in result["ranking"] if r["composite_score"] is not None]
    assert scores == sorted(scores, reverse=True)

    # high + low partition the ranking (no overlap, same members).
    high_ids = [r["program_id"] for r in result["high_performing"]]
    low_ids = [r["program_id"] for r in result["low_performing"]]
    ranking_ids = [r["program_id"] for r in result["ranking"]]
    assert sorted(high_ids + low_ids) == sorted(ranking_ids)
    assert len(set(ranking_ids)) == 7

    # Each row carries the expected outcome fields.
    row = result["ranking"][0]
    assert {
        "program_id", "program_name", "provider_name", "enrolled_trainees",
        "completion_rate", "employment_rate", "relevant_employment_rate",
        "retention_rate", "composite_score",
    } <= set(row)


def test_program_impact_is_deterministic(seeded_db):
    first = program_impact_analysis(seeded_db)
    second = program_impact_analysis(seeded_db)
    assert [r["program_id"] for r in first["ranking"]] == [r["program_id"] for r in second["ranking"]]


def test_program_impact_program_id_filter(seeded_db):
    result = program_impact_analysis(seeded_db, program_id=3)
    assert [r["program_id"] for r in result["ranking"]] == [3]


# ---------------------------------------------------------------------------
# Empty / missing-data cases
# ---------------------------------------------------------------------------
def test_employment_empty_database():
    engine, eng = _blank_session()
    result = employment_outcomes(eng)
    overall = result["overall"]
    assert overall["completion"]["total_enrollments"] == 0
    assert overall["completion"]["completion_rate"] is None
    assert overall["employment"]["available"] == 0
    assert overall["employment"]["employment_rate"] is None
    assert overall["relevant_employment"]["relevant_employment_rate"] is None
    assert overall["retention"]["retention_rate"] is None
    assert result["by_program"] == []
    eng.close()
    engine.dispose()


def test_skill_gap_empty_database():
    engine, eng = _blank_session()
    result = skill_gap_analysis(eng)
    assert result["skills"] == []
    assert result["high_demand_low_supply"] == []
    assert result["by_district"] == []
    eng.close()
    engine.dispose()


def test_program_impact_empty_database():
    engine, eng = _blank_session()
    result = program_impact_analysis(eng)
    assert result["ranking"] == []
    assert result["high_performing"] == []
    assert result["low_performing"] == []
    eng.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# Analytics API: RBAC + response structure (docs/API.md §6)
# ---------------------------------------------------------------------------
def test_admin_can_read_all_analytics_endpoints(api):
    client, _ = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]

    for path in ["/api/analytics/employment",
                 "/api/analytics/skill-gap",
                 "/api/analytics/program-impact"]:
        resp = client.get(path, headers=_headers(token))
        assert resp.status_code == 200, resp.text


def test_provider_cannot_read_analytics(api):
    client, _ = api
    token = _login(client, DEMO_PROVIDER_EMAIL)["access_token"]
    for path in ["/api/analytics/employment",
                 "/api/analytics/skill-gap",
                 "/api/analytics/program-impact"]:
        assert client.get(path, headers=_headers(token)).status_code == 403


def test_trainee_cannot_read_analytics(api):
    client, _ = api
    token = _login(client, DEMO_TRAINEE_EMAIL)["access_token"]
    for path in ["/api/analytics/employment",
                 "/api/analytics/skill-gap",
                 "/api/analytics/program-impact"]:
        assert client.get(path, headers=_headers(token)).status_code == 403


def test_analytics_requires_auth(api):
    client, _ = api
    for path in ["/api/analytics/employment",
                 "/api/analytics/skill-gap",
                 "/api/analytics/program-impact"]:
        assert client.get(path).status_code in (401, 403)


def test_employment_api_structure(api):
    client, _ = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]
    body = client.get("/api/analytics/employment", headers=_headers(token)).json()
    assert {"as_of", "retention_months", "overall", "by_program"} <= set(body)
    assert {"completion", "employment", "relevant_employment", "retention"} <= set(body["overall"])
    assert body["by_program"], "expected at least one program row"
    assert "employment_rate" in body["by_program"][0]


def test_skill_gap_api_structure(api):
    client, _ = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]
    body = client.get("/api/analytics/skill-gap", headers=_headers(token)).json()
    assert {"proficiency_threshold", "skills", "high_demand_low_supply", "by_district"} <= set(body)
    assert body["skills"]
    assert {"required_skill", "demand", "supply", "gap", "status"} <= set(body["skills"][0])


def test_program_impact_api_structure_and_framing(api):
    client, _ = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]
    body = client.get("/api/analytics/program-impact", headers=_headers(token)).json()
    assert {"framing", "ranking", "high_performing", "low_performing"} <= set(body)
    assert body["ranking"]
    assert "correlation" in body["framing"].lower()


def test_employment_api_district_filter(api):
    client, _ = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]
    body = client.get(
        "/api/analytics/employment", params={"district": "Pune"}, headers=_headers(token)
    ).json()
    assert body["overall"]["employment"]["available"] > 0


def test_analytics_endpoints_are_read_only(api):
    """Calling analytics endpoints must not mutate any database rows."""
    client, db = api
    token = _login(client, DEMO_ADMIN_EMAIL)["access_token"]

    from backend.app.database.models import Employment, JobDemand, ProgramEnrollment

    def snapshot():
        return (
            db.query(Employment).count(),
            db.query(JobDemand).count(),
            db.query(ProgramEnrollment).count(),
        )

    before = snapshot()
    for path in ["/api/analytics/employment",
                 "/api/analytics/skill-gap",
                 "/api/analytics/program-impact"]:
        assert client.get(path, headers=_headers(token)).status_code == 200
    assert snapshot() == before