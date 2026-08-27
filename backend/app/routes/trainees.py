"""Trainee domain routes (read endpoints + self-service enrollment)."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.database.models import ProgramEnrollment, Trainee, TrainingProgram, User
from backend.app.database.session import get_db
from backend.app.schemas.employment import EmploymentOut
from backend.app.schemas.trainees import TraineeOut
from backend.app.schemas.training import (
    EnrolledProgramOut,
    EnrollmentCreate,
    EnrollmentOut,
)
from backend.app.security import get_current_user, require_roles

router = APIRouter(prefix="/trainees", tags=["trainees"])


def _load_trainee(trainee_id: int, db: Session) -> Trainee:
    trainee = db.query(Trainee).filter(Trainee.id == trainee_id).first()
    if trainee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trainee not found"
        )
    return trainee


def _serialize(trainee: Trainee) -> TraineeOut:
    return TraineeOut(
        id=trainee.id,
        user_id=trainee.user_id,
        district=trainee.district,
        education_level=trainee.education_level,
        skills=[
            {"id": s.id, "name": s.name, "category": s.category}
            for s in trainee.skills
        ],
    )


@router.get("", response_model=list[TraineeOut])
def list_trainees(
    _current_user: User = Depends(require_roles("admin", "provider")),
    db: Session = Depends(get_db),
) -> list[TraineeOut]:
    return [_serialize(t) for t in db.query(Trainee).order_by(Trainee.id).all()]


@router.get("/me", response_model=TraineeOut)
def get_own_trainee(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TraineeOut:
    """Resolve and return the authenticated trainee's own profile.

    Helper for the trainee role view (docs/API.md §3): the JWT carries the User
    id, not the linked Trainee id, so this maps user -> own trainee record.
    Read-only and RBAC-guarded (trainee, or admin for any resolution).
    """
    query = db.query(Trainee).filter(Trainee.user_id == current_user.id)
    trainee = query.first()
    if trainee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trainee profile linked to this account",
        )
    return _serialize(trainee)


def _enrollment_to_out(enrollment: ProgramEnrollment) -> EnrollmentOut:
    """Serialize an enrollment row together with its programme summary."""
    program = enrollment.program
    return EnrollmentOut(
        id=enrollment.id,
        trainee_id=enrollment.trainee_id,
        program_id=enrollment.program_id,
        completion_status=enrollment.completion_status,
        certification_status=enrollment.certification_status,
        enrolled_date=enrollment.enrolled_date,
        completion_date=enrollment.completion_date,
        program=(
            EnrolledProgramOut(
                id=program.id,
                name=program.name,
                duration_weeks=program.duration_weeks,
                status=program.status,
                provider_name=program.provider.name,
            )
            if program is not None
            else None
        ),
    )


def _load_own_trainee(current_user: User, db: Session) -> Trainee:
    """Resolve the trainee profile linked to the authenticated user."""
    trainee = db.query(Trainee).filter(Trainee.user_id == current_user.id).first()
    if trainee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trainee profile linked to this account",
        )
    return trainee


@router.get("/me/enrollments", response_model=list[EnrollmentOut])
def my_enrollments(
    current_user: User = Depends(require_roles("trainee")),
    db: Session = Depends(get_db),
) -> list[EnrollmentOut]:
    """List the authenticated trainee's own programme enrollments."""
    trainee = _load_own_trainee(current_user, db)
    rows = (
        db.query(ProgramEnrollment)
        .filter(ProgramEnrollment.trainee_id == trainee.id)
        .order_by(ProgramEnrollment.id)
        .all()
    )
    return [_enrollment_to_out(r) for r in rows]


@router.post("/me/enrollments", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll_self(
    payload: EnrollmentCreate,
    current_user: User = Depends(require_roles("trainee")),
    db: Session = Depends(get_db),
) -> EnrollmentOut:
    """Self-service enrollment: trainees enrol **themselves** only.

    - The trainee identity always comes from the JWT, so enrolling another
      trainee through this endpoint is impossible by construction.
    - Duplicates are rejected with 409 (also guarded by the DB unique
      constraint on (trainee_id, program_id)).
    """
    trainee = _load_own_trainee(current_user, db)
    program = (
        db.query(TrainingProgram)
        .filter(TrainingProgram.id == payload.program_id)
        .first()
    )
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Programme not found"
        )
    if program.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This programme is closed and no longer accepts enrollment",
        )

    duplicate = (
        db.query(ProgramEnrollment)
        .filter(
            ProgramEnrollment.trainee_id == trainee.id,
            ProgramEnrollment.program_id == program.id,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already enrolled in this programme",
        )

    enrollment = ProgramEnrollment(
        trainee_id=trainee.id,
        program_id=program.id,
        completion_status="enrolled",
        certification_status="none",
        enrolled_date=date.today(),
        completion_date=None,
    )
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError:  # defensive: the unique constraint still backs us up
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already enrolled in this programme",
        )
    db.refresh(enrollment)
    return _enrollment_to_out(enrollment)


@router.get("/{trainee_id}", response_model=TraineeOut)
def get_trainee(
    trainee_id: int,
    current_user: User = Depends(require_roles("admin", "provider", "trainee")),
    db: Session = Depends(get_db),
) -> TraineeOut:
    """Admin and provider: any trainee. Trainee: only their own profile."""
    trainee = _load_trainee(trainee_id, db)
    if current_user.role == "trainee" and trainee.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trainees may only view their own profile",
        )
    return _serialize(trainee)


@router.get("/{trainee_id}/employment", response_model=list[EmploymentOut])
def get_trainee_employment(
    trainee_id: int,
    current_user: User = Depends(require_roles("admin", "provider", "trainee")),
    db: Session = Depends(get_db),
) -> list[EmploymentOut]:
    """Trainee employment history (admin/provider, or the trainee themself)."""
    trainee = _load_trainee(trainee_id, db)
    if current_user.role == "trainee" and trainee.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trainees may only view their own employment history",
        )
    return [EmploymentOut.model_validate(r) for r in trainee.employment_records]