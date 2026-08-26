"""Read-only analytics routes (admin/government only) - docs/API.md §6.

Endpoints in this module only compute aggregate statistics; they never insert,
update or delete database rows. Access is restricted to the existing RBAC
``admin`` role via ``require_roles``.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from analytics.employment.service import employment_outcomes
from analytics.program_impact.service import program_impact_analysis
from analytics.skill_gap.service import skill_gap_analysis
from backend.app.database.models import User
from backend.app.database.session import get_db
from backend.app.schemas.analytics import (
    EmploymentAnalyticsOut,
    ProgramImpactAnalyticsOut,
    SkillGapAnalyticsOut,
)
from backend.app.security import require_roles

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/employment", response_model=EmploymentAnalyticsOut)
def get_employment_analytics(
    district: Optional[str] = None,
    program_id: Optional[int] = None,
    _current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    """Employment outcomes: overall + per-program rates (docs/DATABASE.md §3.1)."""
    return employment_outcomes(db, district=district, program_id=program_id)


@router.get("/skill-gap", response_model=SkillGapAnalyticsOut)
def get_skill_gap_analytics(
    district: Optional[str] = None,
    _current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    """Demand-vs-supply skill gaps including district roll-up (§3.2)."""
    return skill_gap_analysis(db, district=district)


@router.get("/program-impact", response_model=ProgramImpactAnalyticsOut)
def get_program_impact_analytics(
    program_id: Optional[int] = None,
    _current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    """Programme outcome comparison / ranking (docs/DATABASE.md §3.3).

    Framed as corpus-level outcome comparison, never as causal proof.
    """
    return program_impact_analysis(db, program_id=program_id)