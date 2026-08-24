"""Trainee domain schemas (profile + linked skills)."""

from pydantic import BaseModel


class TraineeSkillOut(BaseModel):
    """A skill held by a trainee at a proficiency level."""

    id: int
    name: str
    category: str


class TraineeOut(BaseModel):
    """Read-only trainee profile."""

    id: int
    user_id: int
    district: str
    education_level: str
    skills: list[TraineeSkillOut] = []