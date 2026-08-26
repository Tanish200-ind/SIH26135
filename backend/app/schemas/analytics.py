"""Response schemas for the read-only analytics endpoints (docs/API.md §6).

These mirror the dicts returned by the ``analytics/`` package. Tokens / hashes
are never exposed; only aggregate statistics are returned.
"""

from typing import Optional

from pydantic import BaseModel


class CompletionOut(BaseModel):
    completed_enrollments: int
    total_enrollments: int
    completion_rate: Optional[float] = None


class EmploymentOut(BaseModel):
    employed: int
    available: int
    employment_rate: Optional[float] = None


class RelevantEmploymentOut(BaseModel):
    relevant: int
    employed: int
    relevant_employment_rate: Optional[float] = None


class RetentionOut(BaseModel):
    retained: int
    placed: int
    retention_months: int
    as_of: str
    retention_rate: Optional[float] = None


class OverallOut(BaseModel):
    completion: CompletionOut
    employment: EmploymentOut
    relevant_employment: RelevantEmploymentOut
    retention: RetentionOut


class ProgramEmploymentOut(BaseModel):
    program_id: int
    program_name: str
    provider_name: str
    status: str
    enrolled_trainees: int
    total_enrollments: int
    completed_enrollments: int
    completion_rate: Optional[float] = None
    employed: int
    available: int
    employment_rate: Optional[float] = None
    relevant: int
    relevant_employment_rate: Optional[float] = None
    placed: int
    retained: int
    retention_rate: Optional[float] = None


class EmploymentAnalyticsOut(BaseModel):
    as_of: str
    retention_months: int
    overall: OverallOut
    by_program: list[ProgramEmploymentOut]


class SkillGapRowOut(BaseModel):
    required_skill: str
    demand: int
    supply: int
    gap: int
    status: str


class DistrictGapOut(BaseModel):
    district: str
    total_demand: int
    total_supply: int
    total_gap: int
    skills: list[SkillGapRowOut]


class SkillGapAnalyticsOut(BaseModel):
    proficiency_threshold: int
    skills: list[SkillGapRowOut]
    high_demand_low_supply: list[SkillGapRowOut]
    by_district: list[DistrictGapOut]


class ProgramImpactRowOut(BaseModel):
    program_id: int
    program_name: str
    provider_name: str
    enrolled_trainees: int
    completion_rate: Optional[float] = None
    employment_rate: Optional[float] = None
    relevant_employment_rate: Optional[float] = None
    retention_rate: Optional[float] = None
    composite_score: Optional[float] = None


class ProgramImpactAnalyticsOut(BaseModel):
    framing: str
    ranking: list[ProgramImpactRowOut]
    high_performing: list[ProgramImpactRowOut]
    low_performing: list[ProgramImpactRowOut]