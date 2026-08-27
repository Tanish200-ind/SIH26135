"""Training-domain schemas (providers, programmes, skills, enrollments)."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str


class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    district: str


class TrainingProgramOut(BaseModel):
    """A skilling programme with its skills taught."""

    id: int
    provider_id: int
    provider_name: str
    name: str
    description: str
    duration_weeks: int
    status: str
    skills: list[SkillOut] = []


class TrainingProgramCreate(BaseModel):
    """Payload for creating a programme (provider role only).

    Ownership is never taken from the client: the authenticated provider's own
    ``TrainingProvider`` record is resolved server-side from the JWT.
    """

    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    duration_weeks: int = Field(ge=1, le=200)
    status: Literal["active", "closed"] = "active"
    # Skills taught must reference existing Skill rows so the skill-gap
    # analytics stay coherent (free-text skills would fragment the supply side).
    skill_ids: list[int] = Field(min_length=1)


class AvailableProgramOut(TrainingProgramOut):
    """Programme as seen by a trainee, annotated with their enrollment state."""

    enrolled: bool = False
    enrollment_status: Optional[str] = None  # enrolled | completed | dropped | None


class EnrollmentCreate(BaseModel):
    """Trainee self-enrollment request (trainee id comes from the JWT)."""

    program_id: int


class EnrolledProgramOut(BaseModel):
    """Compact programme summary embedded in an enrollment row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration_weeks: int
    status: str
    provider_name: str


class EnrollmentOut(BaseModel):
    """A programme enrollment for dashboard/profile display."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    trainee_id: int
    program_id: int
    completion_status: str
    certification_status: str
    enrolled_date: date
    completion_date: Optional[date] = None
    program: Optional[EnrolledProgramOut] = None