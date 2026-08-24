"""Minimal tests for the SQLAlchemy models and the demo-data seed script.

Run from the project root:

    python -m pytest backend/tests -q
"""

from datetime import date

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.app.database.models import (
    Base,
    Employment,
    JobDemand,
    ProgramEnrollment,
    Skill,
    Trainee,
    TrainingProgram,
    TrainingProvider,
    User,
)
from scripts import seed_demo_data as seed

EXPECTED_TABLES = {
    "users",
    "trainees",
    "training_providers",
    "training_programs",
    "skills",
    "program_enrollments",
    "trainee_skills",
    "program_skills",
    "employment",
    "job_demand",
}


@pytest.fixture()
def db_session():
    """In-memory SQLite with a fresh schema per test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_all_tables_are_created(db_session):
    """Every entity in docs/DATABASE.md must map to a table."""
    tables = set(inspect(db_session.bind).get_table_names())
    assert EXPECTED_TABLES <= tables


def test_relationships_user_trainee(db_session):
    """A User links one-to-one to a Trainee."""
    user = User(email="a@example.in", password_hash="x", role="trainee")
    trainee = Trainee(user=user, district="Pune", education_level="Graduate")
    db_session.add_all([user, trainee])
    db_session.commit()

    fetched = db_session.query(Trainee).one()
    assert fetched.user.email == "a@example.in"
    assert fetched.user.role == "trainee"


def test_relationships_program_enrollment_skills(db_session):
    """Program -> provider, program -> skills, trainee enrollment chain."""
    owner = User(email="p@example.in", password_hash="x", role="provider")
    provider = TrainingProvider(user=owner, name="Centre", district="Pune")
    python_skill = Skill(name="Python", category="IT")
    prog = TrainingProgram(
        provider=provider,
        name="Python Bootcamp",
        description="",
        duration_weeks=4,
        status="active",
    )
    prog.skills = [python_skill]

    tu = User(email="t@example.in", password_hash="x", role="trainee")
    trainee = Trainee(user=tu, district="Pune", education_level="12th")
    db_session.add_all([provider, python_skill, prog, trainee])
    db_session.flush()

    enrollment = ProgramEnrollment(
        trainee=trainee,
        program=prog,
        completion_status="completed",
        certification_status="awarded",
        enrolled_date=date(2024, 1, 1),
        completion_date=date(2024, 2, 1),
    )
    db_session.add(enrollment)
    db_session.commit()

    fetched = db_session.query(TrainingProgram).one()
    assert fetched.provider.name == "Centre"
    assert {s.name for s in fetched.skills} == {"Python"}
    assert fetched.enrollments[0].trainee.district == "Pune"


def test_employment_history_relationship(db_session):
    """A trainee can have multiple Employment rows (history for retention)."""
    tu = User(email="t@example.in", password_hash="x", role="trainee")
    trainee = Trainee(user=tu, district="Pune", education_level="12th")
    first = Employment(
        trainee=trainee,
        status="employed",
        job_role="Jr Dev",
        industry="IT",
        salary=300_000,
        start_date=date(2024, 3, 1),
        still_employed=True,
    )
    second = Employment(trainee=trainee, status="unemployed")
    db_session.add_all([tu, trainee, first, second])
    db_session.commit()

    fetched = db_session.query(Trainee).one()
    assert len(fetched.employment_records) == 2


def test_seed_demo_data_counts(db_session):
    """Seeding produces the expected row counts."""
    counts = seed.seed_data(db_session)

    assert counts["users"] == 3 + len(seed.PROVIDERS) + len(seed.TRAINEES)
    assert counts["skills"] == len(seed.SKILLS)
    assert counts["providers"] == len(seed.PROVIDERS)
    assert counts["programs"] == len(seed.PROGRAMS)
    assert counts["trainees"] == len(seed.TRAINEES)
    assert counts["enrollments"] == (
        len(seed.PRIMARY_ENROLLMENTS) + len(seed.SECONDARY_ENROLLMENTS)
    )
    assert counts["employment"] == len(seed.TRAINEES)
    assert counts["job_demand"] == len(seed.JOB_DEMAND)


def test_seed_creates_demo_users(db_session):
    """The three demo roles exist after seeding."""
    seed.seed_data(db_session)

    assert db_session.query(User).filter_by(email=seed.DEMO_ADMIN_EMAIL, role="admin").count() == 1
    assert db_session.query(User).filter_by(email=seed.DEMO_PROVIDER_EMAIL, role="provider").count() == 1
    assert db_session.query(User).filter_by(email=seed.DEMO_TRAINEE_EMAIL, role="trainee").count() == 1


def test_seed_creates_employment_and_demand(db_session):
    """Employment history + labour-market demand rows exist after seeding."""
    seed.seed_data(db_session)

    assert db_session.query(Employment).count() >= 1
    assert db_session.query(JobDemand).count() == len(seed.JOB_DEMAND)
    employed = db_session.query(Employment).filter_by(status="employed").count()
    unemployed = db_session.query(Employment).filter_by(status="unemployed").count()
    assert employed > 0
    assert unemployed > 0