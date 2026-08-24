"""Seed the SIH26135 prototype database with clearly-labelled synthetic demo data.

Usage (from the project root):  python -m scripts.seed_demo_data

This creates data/processed/sih26135.db (overwrites if present) and inserts:
  - demo user accounts (admin / provider / trainee) for login,
  - skills, providers, programmes, trainees, enrollments,
  - employment records and labour-market (job demand) records.

All data is synthetic and is NOT real government data. See docs/DATABASE.md
and docs/PROJECT.md for the demo-data / honesty policy.
"""

from datetime import date, timedelta
import hashlib

from sqlalchemy.orm import Session

from backend.app.config import DATABASE_URL
from backend.app.database.models import (
    Employment,
    JobDemand,
    ProgramEnrollment,
    Skill,
    Trainee,
    TrainingProgram,
    TrainingProvider,
    User,
    trainee_skills,
)
from backend.app.database.session import SessionLocal, init_db

# ---------------------------------------------------------------------------
# Demo accounts (used for login from Day 3 onward; see docs/API.md)
# ---------------------------------------------------------------------------
DEMO_ADMIN_EMAIL = "admin@sih.gov.in"
DEMO_PROVIDER_EMAIL = "provider@sih.gov.in"
DEMO_TRAINEE_EMAIL = "trainee@sih.gov.in"
DEMO_PASSWORD = "demo123"


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 hash (Python stdlib only, no extra dependency).

    The Day 3 login layer must verify passwords with the same algorithm.
    """
    salt = b"sih26135-demo-salt"
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000).hex()

# ---------------------------------------------------------------------------
# Synthetic catalog: skills, providers, programmes, trainees
# ---------------------------------------------------------------------------
SKILLS = [
    ("Python Programming", "IT/Software"),
    ("Data Analysis", "IT/Software"),
    ("Digital Marketing", "IT/Software"),
    ("Spoken English", "Soft Skills"),
    ("Solar Panel Installation", "Renewable Energy"),
    ("Electric Wiring", "Electrical"),
    ("Plumbing", "Construction"),
    ("Tailoring", "Textile & Apparel"),
    ("Food Processing", "Agriculture"),
    ("AC Repair & Servicing", "Home Services"),
]

PROVIDERS = [
    ("Nagpur Skill Development Centre", "Nagpur"),
    ("Pune IT Training Institute", "Pune"),
    ("Maharashtra Rural Livelihood Mission", "Nashik"),
]

PROGRAMS = [
    # (name, provider_index, duration_weeks, status, [skill indexes])
    ("Full-Stack Web Development", 1, 16, "active", [0, 1]),
    ("Data Analyst Associate", 1, 12, "active", [1, 0]),
    ("Digital Marketing Associate", 1, 8, "active", [2, 3]),
    ("Solar Panel Installer", 2, 6, "active", [4, 5]),
    ("Electric Wiring & Repair", 0, 6, "closed", [5]),
    ("AC Repair & Servicing", 2, 8, "active", [9]),
    ("Food Processing Technician", 2, 4, "closed", [8]),
]

TRAINEES = [
    ("Aarav Sharma", "Pune", "Graduate"),
    ("Priya Patel", "Pune", "12th"),
    ("Rohan Verma", "Pune", "Diploma"),
    ("Sneha Iyer", "Pune", "Graduate"),
    ("Kunal Deshmukh", "Pune", "10th"),
    ("Anjali Kulkarni", "Nagpur", "12th"),
    ("Suresh Rane", "Nagpur", "10th"),
    ("Manisha Gupta", "Nagpur", "12th"),
    ("Ravi Thakre", "Nagpur", "10th"),
    ("Pooja Meshram", "Nagpur", "Graduate"),
    ("Vijay Korante", "Nashik", "10th"),
    ("Neha Pawar", "Nashik", "10th"),
    ("Sachin Jadhav", "Nashik", "12th"),
    ("Kavita Bhosale", "Nashik", "Diploma"),
    ("Amit Nikam", "Aurangabad", "10th"),
    ("Sanjay Kale", "Aurangabad", "12th"),
    ("Rekha Bansode", "Aurangabad", "10th"),
    ("Sunil Chaudhari", "Aurangabad", "Diploma"),
    ("Priyanka Wanjale", "Nagpur", "Graduate"),
    ("Nitin Khandare", "Nagpur", "12th"),
    ("Bhagyashree Auti", "Pune", "12th"),
    ("Vaibhav Lande", "Pune", "Diploma"),
    ("Shraddha Bawane", "Nashik", "Graduate"),
    ("Prakash Mehta", "Pune", "10th"),
]

# ---------------------------------------------------------------------------
# Enrollments: (trainee_index, program_index, completion, certification,
#              start_year, start_month). completion_date = start + duration.
# ---------------------------------------------------------------------------
PRIMARY_ENROLLMENTS = [
    # Full-Stack Web Development (program 0)
    (0, 0, "completed", "awarded", 2024, 6),
    (1, 0, "completed", "awarded", 2024, 6),
    (2, 0, "completed", "awarded", 2024, 6),
    (3, 0, "completed", "awarded", 2024, 7),
    (20, 0, "completed", "awarded", 2024, 9),
    (21, 0, "completed", "awarded", 2024, 11),
    # Data Analyst Associate (program 1)
    (4, 1, "completed", "awarded", 2024, 6),
    (5, 1, "completed", "awarded", 2024, 6),
    (7, 1, "completed", "awarded", 2024, 8),
    (9, 1, "completed", "awarded", 2024, 8),
    (18, 1, "completed", "awarded", 2024, 9),
    (19, 1, "completed", "awarded", 2024, 10),
    # Digital Marketing Associate (program 2)
    (22, 2, "completed", "awarded", 2025, 1),
    (23, 2, "enrolled", "none", 2025, 4),
    # Solar Panel Installer (program 3)
    (10, 3, "completed", "awarded", 2024, 7),
    (11, 3, "completed", "awarded", 2024, 7),
    (12, 3, "completed", "not_awarded", 2024, 8),
    (13, 3, "completed", "awarded", 2024, 8),
    (14, 3, "completed", "awarded", 2024, 9),
    # Electric Wiring & Repair (program 4)
    (6, 4, "completed", "awarded", 2024, 6),
    (8, 4, "dropped", "none", 2024, 7),
    (15, 4, "completed", "not_awarded", 2024, 9),
    # AC Repair & Servicing (program 5)
    (17, 5, "completed", "awarded", 2024, 10),
    # Food Processing Technician (program 6)
    (16, 6, "completed", "awarded", 2025, 2),
]

SECONDARY_ENROLLMENTS = [
    (13, 5, "completed", "awarded", 2024, 11),
    (19, 2, "completed", "awarded", 2025, 1),
    (20, 3, "completed", "awarded", 2025, 2),
    (16, 3, "completed", "awarded", 2025, 4),
]

# Employment: trainee_index -> (job_role, industry, salary, months offset, still)
EMPLOYMENT_DEMO = {
    0: ("Junior Software Developer", "Web Services", 320_000, 1, True),
    1: ("Software Developer", "IT Services", 410_000, 2, True),
    2: ("Software Developer", "Product Company", 470_000, 1, True),
    3: ("Web Developer", "Web Studio", 370_000, 2, True),
    4: ("Data Analyst", "Business Services", 390_000, 1, True),
    5: ("Data Entry Operator", "Business Services", 230_000, 2, True),
    7: ("Data Analyst", "Retail Analytics", 350_000, 1, True),
    9: ("Junior Data Analyst", "Analytics Co", 330_000, 1, True),
    10: ("Solar Technician", "Renewable Energy", 240_000, 1, True),
    11: ("Solar Installer", "Solar EPC", 220_000, 2, True),
    12: ("Solar Technician", "Solar Farm", 210_000, 1, True),
    13: ("Solar Technician", "Renewable Energy", 230_000, 2, True),
    14: ("Solar Installer", "Solar EPC", 190_000, 3, True),
    18: ("Data Analyst", "E-commerce", 360_000, 2, False),  # left job (not retained)
    19: ("Data Analyst", "Business Services", 350_000, 1, True),
    20: ("Junior Analyst", "IT Services", 320_000, 1, True),
    21: ("Junior Developer", "Web Studio", 300_000, 1, True),
    22: ("Digital Marketing Associate", "Media Agency", 260_000, 1, True),
    17: ("AC Technician", "Home Services", 200_000, 2, True),
    6: ("Electrician", "Electrical Services", 190_000, 1, True),
    15: ("Electrician", "Electrical Services", 180_000, 2, True),
}

# Labour-market demand: (required_skill, job_role, industry, district, qty)
JOB_DEMAND = [
    ("Python Programming", "Software Developer", "IT Services", "Pune", 120),
    ("Data Analysis", "Data Analyst", "Business Services", "Pune", 70),
    ("Data Analysis", "Data Analyst", "Business Services", "Nagpur", 40),
    ("Digital Marketing", "Digital Marketing Executive", "Media Agency", "Pune", 60),
    ("Solar Panel Installation", "Solar Installer", "Renewable Energy", "Nashik", 110),
    ("Electric Wiring", "Electrician", "Electrical Services", "Nagpur", 65),
    ("Plumbing", "Plumber", "Construction", "Nagpur", 45),
    ("Tailoring", "Tailor", "Textile & Apparel", "Nashik", 35),
    ("AC Repair & Servicing", "AC Technician", "Home Services", "Aurangabad", 40),
    ("Food Processing", "Food Processor", "Agriculture", "Nashik", 50),
    ("Spoken English", "Customer Support", "Business Services", "Pune", 80),
    ("Electric Wiring", "Electrician", "Electrical Services", "Aurangabad", 30),
]

def add_months(day: date, months: int) -> date:
    """Return ``day`` shifted by ``months`` (approx. 30 days per month)."""
    return day + timedelta(days=30 * months)


def seed_data(session: Session) -> dict:
    """Insert all synthetic demo data into the given session/DB.

    Returns a small summary dict of row counts. Also works against an
    in-memory SQLite database (used in tests).
    """
    admin_user = User(email=DEMO_ADMIN_EMAIL, password_hash=hash_password(DEMO_PASSWORD), role="admin")
    provider_user = User(email=DEMO_PROVIDER_EMAIL, password_hash=hash_password(DEMO_PASSWORD), role="provider")
    trainee_user = User(email=DEMO_TRAINEE_EMAIL, password_hash=hash_password(DEMO_PASSWORD), role="trainee")
    users = [admin_user, provider_user, trainee_user]

    for i in range(len(PROVIDERS)):
        users.append(User(
            email=f"provider{i + 1}@sih.gov.in",
            password_hash=hash_password(DEMO_PASSWORD),
            role="provider",
        ))
    for i in range(len(TRAINEES)):
        users.append(User(
            email=f"trainee{i + 1:02d}@example.in",
            password_hash=hash_password(DEMO_PASSWORD),
            role="trainee",
        ))
    session.add_all(users)
    session.flush()

    skills = [Skill(name=n, category=c) for n, c in SKILLS]
    session.add_all(skills)
    session.flush()

    providers = []
    for i, (name, district) in enumerate(PROVIDERS):
        owner = provider_user if i == 0 else users[3 + i]
        providers.append(TrainingProvider(user_id=owner.id, name=name, district=district))
    session.add_all(providers)
    session.flush()

    programs = []
    for name, p_idx, duration, status, skill_idxs in PROGRAMS:
        prog = TrainingProgram(
            provider_id=providers[p_idx].id,
            name=name,
            description=f"Synthetic demo programme: {name}",
            duration_weeks=duration,
            status=status,
        )
        prog.skills = [skills[i] for i in skill_idxs]
        programs.append(prog)
    session.add_all(programs)
    session.flush()

    trainees = []
    for i, (name, district, education) in enumerate(TRAINEES):
        user = trainee_user if i == 0 else users[3 + len(PROVIDERS) + i]
        trainees.append(Trainee(user_id=user.id, district=district, education_level=education))
    session.add_all(trainees)
    session.flush()

    def _make_enrollment(tra_idx, prog_idx, completion, certification, year, month):
        enrolled = date(year, month, 1)
        completion_date = None
        if completion == "completed":
            completion_date = enrolled + timedelta(weeks=PROGRAMS[prog_idx][2])
        return ProgramEnrollment(
            trainee_id=trainees[tra_idx].id,
            program_id=programs[prog_idx].id,
            completion_status=completion,
            certification_status=certification,
            enrolled_date=enrolled,
            completion_date=completion_date,
        )

    enrollments = [_make_enrollment(*row) for row in PRIMARY_ENROLLMENTS]
    enrollments += [_make_enrollment(*row) for row in SECONDARY_ENROLLMENTS]
    session.add_all(enrollments)
    session.flush()

    # Trainee skills: a trainee is "skilled" in the skills of each programme
    # they are enrolled in, at proficiency level 3 (demo).
    for tra in trainees:
        seen_program_ids = {enr.program_id for enr in enrollments if enr.trainee_id == tra.id}
        for prog in programs:
            if prog.id in seen_program_ids:
                for sk in prog.skills:
                    session.execute(
                        trainee_skills.insert().values(
                            trainee_id=tra.id, skill_id=sk.id, proficiency_level=3
                        )
                    )
    session.flush()

    # Employment history (employed or unemployed) for every trainee.
    last_completion = {}
    for enr in enrollments:
        if enr.completion_date:
            previous = last_completion.get(enr.trainee_id)
            if previous is None or enr.completion_date > previous:
                last_completion[enr.trainee_id] = enr.completion_date

    employment_rows = []
    for idx, trainee in enumerate(trainees):
        if idx in EMPLOYMENT_DEMO:
            role, industry, salary, months_offset, still = EMPLOYMENT_DEMO[idx]
            start = last_completion.get(trainee.id, date(2024, 7, 1))
            employment_rows.append(Employment(
                trainee_id=trainee.id,
                status="employed",
                job_role=role,
                industry=industry,
                salary=salary,
                start_date=add_months(start, months_offset),
                still_employed=still,
            ))
        else:
            employment_rows.append(Employment(
                trainee_id=trainee.id, status="unemployed", still_employed=False,
            ))
    session.add_all(employment_rows)

    demand_rows = [
        JobDemand(
            required_skill=skill, job_role=role, industry=industry,
            district=district, demand_quantity=qty,
        )
        for skill, role, industry, district, qty in JOB_DEMAND
    ]
    session.add_all(demand_rows)

    session.commit()

    return {
        "users": session.query(User).count(),
        "skills": session.query(Skill).count(),
        "providers": session.query(TrainingProvider).count(),
        "programs": session.query(TrainingProgram).count(),
        "trainees": session.query(Trainee).count(),
        "enrollments": session.query(ProgramEnrollment).count(),
        "employment": session.query(Employment).count(),
        "job_demand": session.query(JobDemand).count(),
    }


def main() -> None:
    """CLI entry point: (re)create the demo database and populate it."""
    init_db()
    print(f"[seed] Creating schema and seeding demo data -> {DATABASE_URL}")
    with SessionLocal() as session:
        counts = seed_data(session)

    print("\n[seed] Demo database ready. Row counts:")
    for label, count in counts.items():
        print(f"    {label:<12} {count}")
    print("\n    Demo logins (docs/API.md; all password 'demo123'):")
    print(f"    {'Admin   ':12} {DEMO_ADMIN_EMAIL}")
    print(f"    {'Provider':12} {DEMO_PROVIDER_EMAIL}")
    print(f"    {'Trainee ':12} {DEMO_TRAINEE_EMAIL}")


if __name__ == "__main__":
    main()
