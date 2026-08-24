# data/ — Synthetic Demo Data

## Purpose

All data in this project is **synthetic prototype data** for the SIH26135 demo. It is **not** real government/employment data and **no external API** provides it.

## Layout

```
data/
├── raw/         # synthetic source inputs / seed definitions used by the seed script
└── processed/   # generated demo SQLite DB (e.g. sih26135.db) + outputs
```

## How data is created

- `scripts/seed_demo_data.py` generates the demo dataset and the demo users (admin, provider, trainee).
- The generated `.db` file is **git-ignored**; it is always regenerated from the seed script, never committed.
- Raw seed definitions may live under `data/raw/` if the seed script needs input files.

## Honesty note

This is a college-hackathon prototype. Nothing here represents official government statistics. If a future real-data integration is ever added, it must be a clearly separated, documented new source — never mixed silently with demo data.