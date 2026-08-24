"""SQLAlchemy models for the SIH26135 prototype.

Follows docs/DATABASE.md as the single source of truth. Keep this file in sync
with the data model described there. All data stored is synthetic demo data.
"""

from datetime import date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ---------------------------------------------------------------------------
# Association tables (many-to-many)
# ---------------------------------------------------------------------------
trainee_skills = Table(
    "trainee_skills",
    Base.metadata,
    Column("trainee_id", Integer, ForeignKey("trainees.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
    Column("proficiency_level", Integer, nullable=False, default=1),
)

program_skills = Table(
    "program_skills",
    Base.metadata,
    Column("program_id", Integer, ForeignKey("training_programs.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
)


# ---------------------------------------------------------------------------
# Users & roles
# ---------------------------------------------------------------------------
class User(Base):
    """Single login identity. Role is one of: admin | provider | trainee."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)

    trainee = relationship("Trainee", back_populates="user", uselist=False)
    provider = relationship("TrainingProvider", back_populates="user", uselist=False)


class Trainee(Base):
    """A person being trained."""

    __tablename__ = "trainees"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    district = Column(String(100), nullable=False, index=True)
    education_level = Column(String(100), nullable=False)

    user = relationship("User", back_populates="trainee")
    skills = relationship("Skill", secondary=trainee_skills, back_populates="trainees")
    enrollments = relationship("ProgramEnrollment", back_populates="trainee")
    employment_records = relationship("Employment", back_populates="trainee")


class TrainingProvider(Base):
    """An organisation that runs skilling programmes."""

    __tablename__ = "training_providers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    district = Column(String(100), nullable=False)

    user = relationship("User", back_populates="provider")
    programs = relationship("TrainingProgram", back_populates="provider")
# ---------------------------------------------------------------------------
# Skills / programmes
# ---------------------------------------------------------------------------
class Skill(Base):
    """A skill with a category (e.g. 'IT/Software', 'Electrical')."""

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    category = Column(String(100), nullable=False)

    trainees = relationship("Trainee", secondary=trainee_skills, back_populates="skills")
    programs = relationship("TrainingProgram", secondary=program_skills, back_populates="skills")


class TrainingProgram(Base):
    """A skilling course run by a provider."""

    __tablename__ = "training_programs"

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("training_providers.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    duration_weeks = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active | closed

    provider = relationship("TrainingProvider", back_populates="programs")
    skills = relationship("Skill", secondary=program_skills, back_populates="programs")
    enrollments = relationship("ProgramEnrollment", back_populates="program")


class ProgramEnrollment(Base):
    """A trainee enrolled in a programme (many-to-many with attributes)."""

    __tablename__ = "program_enrollments"
    __table_args__ = (
        UniqueConstraint("trainee_id", "program_id", name="uq_enrollment_trainee_program"),
    )

    id = Column(Integer, primary_key=True)
    trainee_id = Column(Integer, ForeignKey("trainees.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    completion_status = Column(String(20), nullable=False, default="enrolled")
    # completion_status: enrolled | completed | dropped
    certification_status = Column(String(20), nullable=False, default="none")
    # certification_status: none | awarded | not_awarded
    enrolled_date = Column(Date, nullable=False)
    completion_date = Column(Date, nullable=True)

    trainee = relationship("Trainee", back_populates="enrollments")
    program = relationship("TrainingProgram", back_populates="enrollments")


# ---------------------------------------------------------------------------
# Employment / labour-market
# ---------------------------------------------------------------------------
class Employment(Base):
    """Employment history of a trainee (one trainee -> many records).

    Storing history (not just current status) lets us compute retention rates.
    """

    __tablename__ = "employment"

    id = Column(Integer, primary_key=True)
    trainee_id = Column(Integer, ForeignKey("trainees.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # employed | unemployed
    job_role = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    salary = Column(Integer, nullable=True)  # annual INR, demo data
    start_date = Column(Date, nullable=True)
    still_employed = Column(Boolean, nullable=False, default=True)

    trainee = relationship("Trainee", back_populates="employment_records")


class JobDemand(Base):
    """Labour-market demand, synthetic demo records (not a real government feed)."""

    __tablename__ = "job_demand"

    id = Column(Integer, primary_key=True)
    job_role = Column(String(100), nullable=False)
    industry = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    required_skill = Column(String(100), nullable=False, index=True)
    demand_quantity = Column(Integer, nullable=False)  # number of openings