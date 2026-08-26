"""Role -> skill relevance matching (used by the relevant-employment rate).

docs/DATABASE.md §3.1 defines "relevant" as:

    trainee's job_role matches a skill taught in their completed programme

``JobDemand`` is the canonical mapping from a job role to the skill it requires.
A trainee's employment is therefore relevant when:

    1. their job_role matches a ``JobDemand`` job_role, and
    2. that role's required skill was taught in a programme the trainee completed.

Matching is deterministic string/keyword overlap - a simple, explainable rule,
not fuzzy ML:

    role_a matches role_b  <=  exact (case-insensitive)  OR
                               substring containment      OR
                               shared keyword token (>=3 chars, non-generic)

Generic words (junior/senior/associate/data/... ) are ignored so that e.g.
"Data Entry Operator" does not false-positive against "Data Analyst".
"""

import re
from collections import defaultdict
from typing import Dict, Set

from sqlalchemy.orm import Session

from backend.app.database.models import JobDemand

# Words that carry no skill meaning when two job titles share them.
_IGNORED_ROLE_TOKENS = {
    "assistant", "associate", "coordinator", "data", "entry", "executive",
    "general", "junior", "lead", "manager", "operator", "representative",
    "senior", "service", "services", "specialist", "staff", "support",
    "technician",
}


def demand_role_skill_map(session: Session) -> Dict[str, Set[str]]:
    """Canonical JobDemand job_role -> set of required skill names."""
    mapping: dict[str, set[str]] = defaultdict(set)
    rows = session.query(JobDemand.job_role, JobDemand.required_skill).all()
    for role, skill in rows:
        mapping[role].add(skill)
    return mapping


def _tokens(text: str) -> set[str]:
    """Keyword tokens (>=3 chars) excluding generic job-title words."""
    return {
        token
        for token in re.split(r"[\s\-/&,()]+", text.lower())
        if len(token) >= 3 and token not in _IGNORED_ROLE_TOKENS
    }


def roles_match(role_a: str, role_b: str) -> bool:
    """Deterministic job-title match: exact, substring, or shared keyword."""
    a, b = role_a.lower().strip(), role_b.lower().strip()
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    return bool(_tokens(a) & _tokens(b))


def is_relevant_role(
    job_role: str | None,
    trained_skill_names: Set[str],
    role_skill_map: Dict[str, Set[str]],
) -> bool:
    """True when ``job_role`` maps (via JobDemand) to a taught skill.

    ``trained_skill_names`` should be the skill names of the programme(s) the
    trainee completed. Returns False when there is no role, no trained skill,
    or no demand mapping for the role.
    """
    if not job_role or not trained_skill_names:
        return False
    for demand_role, required_skills in role_skill_map.items():
        if roles_match(job_role, demand_role) and required_skills & trained_skill_names:
            return True
    return False