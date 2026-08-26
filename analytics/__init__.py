"""SIH26135 analytics package.

employment outcomes · skill gaps · programme impact.

This is a **normal Python library imported by the FastAPI backend** — it is not
a separate service/microservice (see docs/ARCHITECTURE.md §3).

All calculations are deterministic, read-only statistics over the seeded demo
SQLite data and follow the formulas defined in docs/DATABASE.md §3. No machine
learning and no LLM are involved.
"""