"""Single source of truth for the analytics rate formulas (docs/DATABASE.md §3.1).

Every analytics module that reports a percentage must use ``rate`` or one of the
named wrappers below, so the whole codebase measures the same thing.

Formulas (verbatim from docs/DATABASE.md):

- Completion rate          = completed enrollments / total enrollments x 100
- Employment rate          = employed trainees / trainees available for work x 100
- Relevant-employment rate = employed-in-relevant-role trainees / employed trainees x 100
- Retention rate           = placed trainees still working after N months / placed trainees x 100
"""

from datetime import date, timedelta

# Retention window ("still working after N months").
RETENTION_MONTHS = 3
# 30 days per month, matching scripts/seed_demo_data.add_months.
_DAYS_PER_MONTH = 30


def rate(numerator: int, denominator: int) -> float | None:
    """Percentage (0-100, 2 decimal places) with safe division.

    Returns None when the denominator is zero (i.e. there are no records to
    base the rate on) so callers can render "no data" instead of a 0/0 error.
    """
    if numerator is None or not denominator:
        return None
    return round(numerator / denominator * 100, 2)


def completion_rate(completed: int, total: int) -> float | None:
    """Completed enrollments / total enrollments x 100."""
    return rate(completed, total)


def employment_rate(employed: int, available: int) -> float | None:
    """Employed trainees / trainees available for work x 100.

    "Available for work" = trainees with a recorded employment status
    (employed or unemployed).
    """
    return rate(employed, available)


def relevant_employment_rate(relevant: int, employed: int) -> float | None:
    """Employed-in-relevant-role trainees / employed trainees x 100."""
    return rate(relevant, employed)


def retention_rate(retained: int, placed: int) -> float | None:
    """Placed trainees still working after N months / placed trainees x 100.

    ``placed`` = trainees whose employment started at least ``RETENTION_MONTHS``
    before the as-of date (so the N-month mark has occurred).
    """
    return rate(retained, placed)


def months_before(reference: date, months: int) -> date:
    """``reference`` shifted back by ``months`` (30 days per month)."""
    return reference - timedelta(days=_DAYS_PER_MONTH * months)