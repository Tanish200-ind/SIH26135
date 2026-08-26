"""Programme impact analysis: ranked outcome comparison across programmes.

docs/DATABASE.md §3.3: per programme, compute employment rate,
relevant-employment rate and retention rate among that programme's trainees
(same formulas as §3.1, reused from analytics.employment), then rank.

Framing: outcome comparison / correlation only - never causal proof.
"""

from typing import Optional

from sqlalchemy.orm import Session

from analytics.employment.service import per_program_outcomes

FRAMING = (
    "Program impact is an outcome comparison / correlation across the synthetic "
    "demo data only. It identifies high- and low-performing programmes but does "
    "not prove causal impact."
)


def program_impact_analysis(
    session: Session, program_id: Optional[int] = None
) -> dict:
    """Rank programmes by composite of employment, relevance and retention.

    Composite score = mean of the available rates (None when a programme has no
    rate data at all). Ranking is deterministic: score descending, then
    program_id ascending.
    """
    programs = per_program_outcomes(session, program_id=program_id)

    ranking = []
    for p in programs:
        rates = [
            r
            for r in (p["employment_rate"], p["relevant_employment_rate"], p["retention_rate"])
            if r is not None
        ]
        composite = round(sum(rates) / len(rates), 2) if rates else None
        ranking.append(
            {
                "program_id": p["program_id"],
                "program_name": p["program_name"],
                "provider_name": p["provider_name"],
                "enrolled_trainees": p["enrolled_trainees"],
                "completion_rate": p["completion_rate"],
                "employment_rate": p["employment_rate"],
                "relevant_employment_rate": p["relevant_employment_rate"],
                "retention_rate": p["retention_rate"],
                "composite_score": composite,
            }
        )

    def _sort_key(row: dict) -> tuple:
        score = -1.0 if row["composite_score"] is None else row["composite_score"]
        return (-score, row["program_id"])

    ranking.sort(key=_sort_key)

    # Split the ranking: top half = high-performing, bottom half = low-performing.
    split = (len(ranking) + 1) // 2
    high_performing = ranking[:split]
    low_performing = ranking[split:] if split < len(ranking) else []

    return {
        "framing": FRAMING,
        "ranking": ranking,
        "high_performing": high_performing,
        "low_performing": low_performing,
    }