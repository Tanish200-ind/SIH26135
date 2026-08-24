"""Training-domain routes (providers + programmes, read endpoints)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.models import TrainingProgram, TrainingProvider, User
from backend.app.database.session import get_db
from backend.app.schemas.training import ProviderOut, TrainingProgramOut
from backend.app.security import require_roles

router = APIRouter(tags=["training"])


def _to_program_out(program: TrainingProgram) -> TrainingProgramOut:
    return TrainingProgramOut(
        id=program.id,
        provider_id=program.provider_id,
        provider_name=program.provider.name,
        name=program.name,
        description=program.description or "",
        duration_weeks=program.duration_weeks,
        status=program.status,
        skills=[
            {"id": s.id, "name": s.name, "category": s.category}
            for s in program.skills
        ],
    )


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(
    _current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> list[ProviderOut]:
    """List training providers (admin/government only)."""
    providers = db.query(TrainingProvider).order_by(TrainingProvider.id).all()
    return [ProviderOut.model_validate(p) for p in providers]


@router.get("/programs", response_model=list[TrainingProgramOut])
def list_programs(
    current_user: User = Depends(require_roles("admin", "provider")),
    db: Session = Depends(get_db),
) -> list[TrainingProgramOut]:
    """List programmes. Providers see only their own; admin sees all."""
    query = db.query(TrainingProgram)
    if current_user.role == "provider":
        query = query.join(TrainingProvider).filter(
            TrainingProvider.user_id == current_user.id
        )
    programs = query.order_by(TrainingProgram.id).all()
    return [_to_program_out(p) for p in programs]


@router.get("/programs/{program_id}", response_model=TrainingProgramOut)
def get_program(
    program_id: int,
    _current_user: User = Depends(require_roles("admin", "provider", "trainee")),
    db: Session = Depends(get_db),
) -> TrainingProgramOut:
    """Single programme with its skills taught."""
    program = (
        db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    )
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Programme not found"
        )
    return _to_program_out(program)