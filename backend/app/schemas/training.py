"""Training-domain schemas (providers, programmes, skills)."""

from pydantic import BaseModel, ConfigDict


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