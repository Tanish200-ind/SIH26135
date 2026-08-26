"""Skill-gap analytics: demand-vs-supply by skill and by district.

docs/DATABASE.md §3.2:
- Demand  = sum of JobDemand.demand_quantity per required_skill.
- Supply  = number of trainees holding that skill at proficiency >= threshold.
- Gap     = demand - supply (positive => skill gap). High |gap| skills flagged.
"""

from collections import defaultdict
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database.models import JobDemand, Skill, Trainee, trainee_skills

# Minimum proficiency level for a trainee to count as supply for a skill.
SKILL_PROFICIENCY_THRESHOLD = 3


def skill_gap_analysis(session: Session, district: Optional[str] = None) -> dict:
    """Compute skill-level and district-level gaps.

    Optional ``district`` narrows both demand and supply to one district.
    """
    # --- demand per required skill ---
    demand_q = (
        session.query(JobDemand.required_skill, func.sum(JobDemand.demand_quantity))
        .group_by(JobDemand.required_skill)
    )
    if district:
        demand_q = demand_q.filter(JobDemand.district == district)
    demand: dict[str, int] = {skill: int(qty) for skill, qty in demand_q.all()}

    # --- supply per skill (trainees with proficiency >= threshold) ---
    supply_q = (
        session.query(Skill.name)
        .join(trainee_skills, trainee_skills.c.skill_id == Skill.id)
        .join(Trainee, Trainee.id == trainee_skills.c.trainee_id)
        .filter(trainee_skills.c.proficiency_level >= SKILL_PROFICIENCY_THRESHOLD)
    )
    if district:
        supply_q = supply_q.filter(Trainee.district == district)
    supply: dict[str, int] = defaultdict(int)
    for (skill_name,) in supply_q.all():
        supply[skill_name] += 1

    skill_names = sorted(set(demand) | set(supply))
    gaps = []
    for name in skill_names:
        d, s = demand.get(name, 0), supply.get(name, 0)
        gap = d - s
        gaps.append(
            {
                "required_skill": name,
                "demand": d,
                "supply": s,
                "gap": gap,
                "status": "high-demand-low-supply" if gap > 0 else "balanced",
            }
        )
    gaps.sort(key=lambda g: (-g["gap"], g["required_skill"]))
    high_demand_low_supply = [g for g in gaps if g["gap"] > 0]

    # --- district-level roll-up ---
    district_demand_q = (
        session.query(
            JobDemand.district,
            JobDemand.required_skill,
            func.sum(JobDemand.demand_quantity),
        ).group_by(JobDemand.district, JobDemand.required_skill)
    )
    if district:
        district_demand_q = district_demand_q.filter(JobDemand.district == district)
    district_demand: dict[tuple[str, str], int] = {
        (d, s): int(qty) for d, s, qty in district_demand_q.all()
    }

    district_supply_q = (
        session.query(Trainee.district, Skill.name)
        .join(trainee_skills, trainee_skills.c.skill_id == Skill.id)
        .join(Trainee, Trainee.id == trainee_skills.c.trainee_id)
        .filter(trainee_skills.c.proficiency_level >= SKILL_PROFICIENCY_THRESHOLD)
    )
    if district:
        district_supply_q = district_supply_q.filter(Trainee.district == district)
    district_supply: dict[tuple[str, str], int] = defaultdict(int)
    for (d, skill_name) in district_supply_q.all():
        district_supply[(d, skill_name)] += 1

    districts = sorted(
        {d for d, _ in district_demand} | {d for d, _ in district_supply}
    )
    by_district = []
    for d in districts:
        skill_names_d = sorted(
            {s for dd, s in district_demand if dd == d}
            | {s for dd, s in district_supply if dd == d}
        )
        skill_rows = []
        for s in skill_names_d:
            dem = district_demand.get((d, s), 0)
            sup = district_supply.get((d, s), 0)
            gap = dem - sup
            skill_rows.append(
                {
                    "required_skill": s,
                    "demand": dem,
                    "supply": sup,
                    "gap": gap,
                    "status": "high-demand-low-supply" if gap > 0 else "balanced",
                }
            )
        skill_rows.sort(key=lambda g: (-g["gap"], g["required_skill"]))
        total_demand = sum(g["demand"] for g in skill_rows)
        total_supply = sum(g["supply"] for g in skill_rows)
        by_district.append(
            {
                "district": d,
                "total_demand": total_demand,
                "total_supply": total_supply,
                "total_gap": total_demand - total_supply,
                "skills": skill_rows,
            }
        )

    return {
        "proficiency_threshold": SKILL_PROFICIENCY_THRESHOLD,
        "skills": gaps,
        "high_demand_low_supply": high_demand_low_supply,
        "by_district": by_district,
    }