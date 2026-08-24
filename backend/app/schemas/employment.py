"""Employment-domain schemas (read endpoints)."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmploymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trainee_id: int
    status: str
    job_role: Optional[str] = None
    industry: Optional[str] = None
    salary: Optional[int] = None
    start_date: Optional[date] = None
    still_employed: bool