"""Employment-outcome metrics: overall + per-program (docs/DATABASE.md §3.1).

All metrics are computed only from the DB (seeded demo data). The functions
here are pure and read-only; the FastAPI route layer adds RBAC on top.
"""

from collections import defaultdict
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.database.models import (
    Employment,
    ProgramEnrollment,
    Skill,
    Trainee,
    TrainingProgram,
    program_skills,
)
from analytics.common.ratios import (
    RETENTION_MONTHS,
    completion_rate,
    employment_rate,
    months_before,
    relevant_employment_rate,
    retention_rate,
)
from analytics.common.relevance import (
    demand_role_skill_map,
    is_relevant_role,
)


def as_of_date(session: Session) -> date:
    """Deterministic reference "today": the latest employment start date in data.

    Keeps retention results stable regardless of when the API is called, and
    makes the calculation reproducible for a given database.
    """
    latest = (
        session.query(Employment.start_date)
        .filter(Employment.start_date.isnot(None))
        .order_by(Employment.start_date.desc())
        .first()
    )
    return latest[0] if latest and latest[0] else date.today()


def latest_employment_by_trainee(session: Session) -> dict[int, Employment]:
    """trainee_id -> most recent Employment row (their "current status")."""
    rows = (
        session.query(Employment)
        .order_by(
            Employment.trainee_id,
            Employment.start_date.desc(),
            Employment.id.desc(),
        )
        .all()
    )
    latest: dict[int, Employment] = {}
    for row in rows:
        latest.setdefault(row.trainee_id, row)
    return latest


def completed_skill_names_by_trainee(session: Session) -> dict[int, set[str]]:
    """trainee_id -> set of skill names taught in programmes they completed."""
    rows = (
        session.query(ProgramEnrollment.trainee_id, Skill.name)
        .join(TrainingProgram, TrainingProgram.id == ProgramEnrollment.program_id)
        .join(program_skills, program_skills.c.program_id == TrainingProgram.id)
        .join(Skill, Skill.id == program_skills.c.skill_id)
        .filter(ProgramEnrollment.completion_status == "completed")
        .all()
    )
    trained: dict[int, set[str]] = defaultdict(set)
    for trainee_id, skill_name in rows:
        trained[trainee_id].add(skill_name)
    return trained


def employment_outcomes(
    session: Session,
    district: Optional[str] = None,
    program_id: Optional[int] = None,
) -> dict:
    """Employment outcomes: overall metrics + per-program breakdown.

    Optional ``district`` narrows the trainees/enrollments considered; optional
    ``program_id`` narrows the per-program list.
    """
    trainees_q = session.query(Trainee).order_by(Trainee.id)
    if district:
        trainees_q = trainees_q.filter(Trainee.district == district)
    trainees = trainees_q.all()
    trainee_ids = {t.id for t in trainees}

    latest = latest_employment_by_trainee(session)
    trained_skills = completed_skill_names_by_trainee(session)
    role_skill_map = demand_role_skill_map(session)
    as_of = as_of_date(session)
    cutoff = months_before(as_of, RETENTION_MONTHS)

    # --- completion rate (enrollment level) ---
    enroll_q = session.query(ProgramEnrollment)
    if district:
        enroll_q = enroll_q.join(Trainee, Trainee.id == ProgramEnrollment.trainee_id).filter(
            Trainee.district == district
        )
    total_enrollments = enroll_q.count()
    completed_enrollments = enroll_q.filter(
        ProgramEnrollment.completion_status == "completed"
    ).count()

    # --- trainee-level employment buckets ---
    available_ids = [t.id for t in trainees if t.id in latest]
    employed_ids = [tid for tid in available_ids if latest[tid].status == "employed"]
    placed_ids = [
        tid
        for tid in employed_ids
        if latest[tid].start_date is not None and latest[tid].start_date <= cutoff
    ]
    retained_ids = [tid for tid in placed_ids if latest[tid].still_employed]
    relevant_ids = [
        tid
        for tid in employed_ids
        if is_relevant_role(
            latest[tid].job_role, trained_skills.get(tid, set()), role_skill_map
        )
    ]

    overall = {
        "completion": {
            "completed_enrollments": completed_enrollments,
            "total_enrollments": total_enrollments,
            "completion_rate": completion_rate(completed_enrollments, total_enrollments),
        },
        "employment": {
            "employed": len(employed_ids),
            "available": len(available_ids),
            "employment_rate": employment_rate(len(employed_ids), len(available_ids)),
        },
        "relevant_employment": {
            "relevant": len(relevant_ids),
            "employed": len(employed_ids),
            "relevant_employment_rate": relevant_employment_rate(
                len(relevant_ids), len(employed_ids)
            ),
        },
        "retention": {
            "retained": len(retained_ids),
            "placed": len(placed_ids),
            "retention_months": RETENTION_MONTHS,
            "as_of": as_of.isoformat(),
            "retention_rate": retention_rate(len(retained_ids), len(placed_ids)),
        },
    }

    by_program = per_program_outcomes(
        session,
        district=district,
        program_id=program_id,
        latest=latest,
        role_skill_map=role_skill_map,
        as_of=as_of,
    )
    return {
        "as_of": as_of.isoformat(),
        "retention_months": RETENTION_MONTHS,
        "overall": overall,
        "by_program": by_program,
    }


def per_program_outcomes(
    session: Session,
    district: Optional[str] = None,
    program_id: Optional[int] = None,
    latest: Optional[dict[int, Employment]] = None,
    role_skill_map: Optional[dict] = None,
    as_of: Optional[date] = None,
) -> list[dict]:
    """Per-program employment-outcome metrics for every programme.

    Exposed separately so the program-impact module can reuse the exact same
    per-program numbers (no duplicated calculation logic).
    """
    latest = latest if latest is not None else latest_employment_by_trainee(session)
    role_skill_map = (
        role_skill_map
        if role_skill_map is not None
        else demand_role_skill_map(session)
    )
    as_of = as_of or as_of_date(session)
    cutoff = months_before(as_of, RETENTION_MONTHS)

    trainee_district = dict(session.query(Trainee.id, Trainee.district).all())

    prog_q = session.query(TrainingProgram).order_by(TrainingProgram.id)
    if program_id is not None:
        prog_q = prog_q.filter(TrainingProgram.id == program_id)
    programs = prog_q.all()
    if not programs:
        return []

    enrollments = (
        session.query(ProgramEnrollment)
        .filter(ProgramEnrollment.program_id.in_([p.id for p in programs]))
        .all()
    )
    enroll_by_program: dict[int, list[ProgramEnrollment]] = defaultdict(list)
    for enr in enrollments:
        enroll_by_program[enr.program_id].append(enr)

    by_program = []
    for prog in programs:
        prog_enrolls = enroll_by_program.get(prog.id, [])
        member_ids = {e.trainee_id for e in prog_enrolls}
        if district:
            member_ids = {
                tid for tid in member_ids if trainee_district.get(tid) == district
            }
        prog_enrolls = [e for e in prog_enrolls if e.trainee_id in member_ids]

        total = len(prog_enrolls)
        completed = sum(1 for e in prog_enrolls if e.completion_status == "completed")

        available = [tid for tid in member_ids if tid in latest]
        employed = [tid for tid in available if latest[tid].status == "employed"]
        placed = [
            tid
            for tid in employed
            if latest[tid].start_date is not None and latest[tid].start_date <= cutoff
        ]
        retained = [tid for tid in placed if latest[tid].still_employed]

        prog_skill_names = {s.name for s in prog.skills}
        relevant = [
            tid
            for tid in employed
            if is_relevant_role(latest[tid].job_role, prog_skill_names, role_skill_map)
        ]

        by_program.append(
            {
                "program_id": prog.id,
                "program_name": prog.name,
                "provider_name": prog.provider.name,
                "status": prog.status,
                "enrolled_trainees": len(member_ids),
                "total_enrollments": total,
                "completed_enrollments": completed,
                "completion_rate": completion_rate(completed, total),
                "employed": len(employed),
                "available": len(available),
                "employment_rate": employment_rate(len(employed), len(available)),
                "relevant": len(relevant),
                "relevant_employment_rate": relevant_employment_rate(
                    len(relevant), len(employed)
                ),
                "placed": len(placed),
                "retained": len(retained),
                "retention_rate": retention_rate(len(retained), len(placed)),
            }
        )
    return by_program