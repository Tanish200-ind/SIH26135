"""Employment-domain routes (read endpoints)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.models import Employment, User
from backend.app.database.session import get_db
from backend.app.schemas.employment import EmploymentOut
from backend.app.security import require_roles

router = APIRouter(prefix="/employment", tags=["employment"])


@router.get("", response_model=list[EmploymentOut])
def list_employment(
    _current_user: User = Depends(require_roles("admin", "provider")),
    db: Session = Depends(get_db),
) -> list[EmploymentOut]:
    """List all employment records (admin/provider)."""
    rows = db.query(Employment).order_by(Employment.id).all()
    return [EmploymentOut.model_validate(r) for r in rows]