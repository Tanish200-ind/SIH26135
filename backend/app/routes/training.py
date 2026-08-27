"""Training-domain routes (programmes: reads, provider creation, availability)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.models import (
    ProgramEnrollment,
    Skill,
    Trainee,
    TrainingProgram,
    TrainingProvider,
    User,
)
from backend.app.database.session import get_db
from backend.app.schemas.training import (
    AvailableProgramOut,
    ProviderOut,
    SkillOut,
    TrainingProgramCreate,
    TrainingProgramOut,
)
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


@router.get("/skills", response_model=list[SkillOut])
def list_skills(
    _current_user: User = Depends(require_roles("admin", "provider", "trainee")),
    db: Session = Depends(get_db),
) -> list[SkillOut]:
    """Skill catalog (used by the provider 'add programme' form)."""
    skills = db.query(Skill).order_by(Skill.name).all()
    return [SkillOut.model_validate(s) for s in skills]


@router.post(
    "/programs",
    response_model=TrainingProgramOut,
    status_code=status.HTTP_201_CREATED,
)
def create_program(
    payload: TrainingProgramCreate,
    current_user: User = Depends(require_roles("provider")),
    db: Session = Depends(get_db),
) -> TrainingProgramOut:
    """Create a programme owned by the **authenticated** provider.

    Ownership is always derived server-side from the JWT: the client cannot
    supply or spoof a provider id. Admin and trainee roles are rejected by
    ``require_roles("provider")`` before the handler runs.
    """
    provider = (
        db.query(TrainingProvider)
        .filter(TrainingProvider.user_id == current_user.id)
        .first()
    )
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No provider profile linked to this account",
        )

    # Skills must reference existing catalog rows (deduplicated, order kept).
    unique_skill_ids = list(dict.fromkeys(payload.skill_ids))
    skills = {s.id: s for s in db.query(Skill).filter(Skill.id.in_(unique_skill_ids)).all()}
    missing = [sid for sid in unique_skill_ids if sid not in skills]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown skill id(s): {missing}",
        )

    program = TrainingProgram(
        provider_id=provider.id,  # server-derived ownership, never client data
        name=payload.name.strip(),
        description=(payload.description or "").strip(),
        duration_weeks=payload.duration_weeks,
        status=payload.status,
    )
    program.skills = [skills[sid] for sid in unique_skill_ids]
    db.add(program)
    db.commit()
    db.refresh(program)
    return _to_program_out(program)


@router.get("/programs/available", response_model=list[AvailableProgramOut])
def available_programs(
    current_user: User = Depends(require_roles("trainee")),
    db: Session = Depends(get_db),
) -> list[AvailableProgramOut]:
    """Browse all programmes with the authenticated trainee's enrollment state.

    Active programmes are listed first. ``enrolled`` / ``enrollment_status``
    come from the trainee's own ProgramEnrollment rows so the UI shows
    "Enrolled" instead of permitting duplicate enrollment.
    """
    trainee = db.query(Trainee).filter(Trainee.user_id == current_user.id).first()
    enrolled_map: dict[int, str] = {}
    if trainee is not None:
        rows = (
            db.query(
                ProgramEnrollment.program_id,
                ProgramEnrollment.completion_status,
            )
            .filter(ProgramEnrollment.trainee_id == trainee.id)
            .all()
        )
        enrolled_map = {pid: st for pid, st in rows}

    programs = (
        db.query(TrainingProgram)
        .order_by(TrainingProgram.status.asc(), TrainingProgram.name.asc())
        .all()
    )
    result = []
    for program in programs:
        state = enrolled_map.get(program.id)
        result.append(
            AvailableProgramOut(
                **_to_program_out(program).model_dump(),
                enrolled=state is not None,
                enrollment_status=state,
            )
        )
    return result


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