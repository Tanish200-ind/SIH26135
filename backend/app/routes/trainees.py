"""Trainee domain routes (read endpoints, RBAC-guarded)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.models import Trainee, User
from backend.app.database.session import get_db
from backend.app.schemas.employment import EmploymentOut
from backend.app.schemas.trainees import TraineeOut
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