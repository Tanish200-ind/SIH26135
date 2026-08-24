# ARCHITECTURE.md — SIH26135 Skilling Intelligence Platform

## 1. Design principles

1. **Simple & explainable** by a college team in ~5 minutes at presentation.
2. **Modular & maintainable** — clear layers and a small number of files; no duplication.
3. **No overengineering** — no microservices, Kafka, Redis, Docker, Kubernetes, blockchain, or predictive ML.
4. **Honest about data** — synthetic demo data, clearly separated from real-data concerns; no fake API claims.
5. **Core focus** — employment outcomes, skill gaps, programme impact, and the government dashboard.

---

## 2. Technology stack (final)

| Layer | Technology | Why |
| --- | --- | --- |
| Backend | **Python 3 + FastAPI + Uvicorn** | Minimal boilerplate; auto `/docs`; Pydantic validation built in |
| Database | **SQLite via SQLAlchemy ORM** | File-based, zero install, easy to demo & to explain |
| Validation | **Pydantic** | Ships with FastAPI; safe request/response contracts |
| Auth | **JWT + role-based access** | Simple, provable, no external identity provider |
| Analytics | **Plain Python + pandas** | Formulas are readable; only deterministic statistics |
| Frontend | **React + Vite + Recharts** | Fast bootstrap; Recharts for dashboard charts |
| Tests | **pytest** | Standard, low ceremony |
| AI (optional, P2) | **One OpenAI-compatible LLM call** given real metrics as context | Only for explanation; never for inventing numbers |

**Deliberately excluded:** predictive ML models, blockchain, microservices, Kafka, Redis, Docker, Kubernetes, real external government APIs. None are required for a demonstrable 6-day prototype, and each adds unaffordable setup/explanation cost.

---

## 3. Folder structure (target)

```
SIH26135/
├── README.md
├── .gitignore
├── docs/
│   ├── PROJECT.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── API.md
│   └── AI_RULES.md
├── scripts/
│   └── seed_demo_data.py        # generates synthetic demo data
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entry point
│       ├── config.py            # config from .env (single module)
│       ├── database/
│       │   ├── session.py
│       │   └── models.py        # SQLAlchemy entities
│       ├── schemas/             # Pydantic models
│       ├── routes/              # auth, trainees, training, employment, analytics, dashboard
│       ├── services/            # business logic + seed helper
│       └── .env.example         # config template (no secrets)
│   └── tests/                   # unit tests
├── analytics/
│   ├── common/                  # shared metric definitions/formulas
│   ├── employment/
│   ├── skill_gap/
│   └── program_impact/
├── frontend/                    # React application (Vite)
└── data/
    ├── raw/                     # synthetic source inputs
    ├── processed/               # generated demo DB
    └── README.md
```

**Rules:**
- Folders are created **only when** their first real module is implemented (no empty scaffolding).
- The top-level `analytics/` is an **imported Python library** used by the FastAPI app — it is **not** a separate service (no microservices).
- Tests live in one place: `backend/tests/`.
---

## 4. System architecture & data flow

```
Data entry (Trainee / Provider / seed script)
        │ React UI
        ▼
Frontend (React + Vite + Recharts)
        │ JSON over REST
        ▼
FastAPI Backend  →  Pydantic validation  →  Auth/RBAC gate (seeded accounts)
        │ SQLAlchemy
        ▼
SQLite Database
        │
        ▼
Analytics layer (plain Python + pandas; imported by backend)
        │  employment outcomes · skill-gap · programme impact
        ▼
Government Dashboard (charts + tables)

Optional AI assistant (P2 — post-core only):
Dashboard ──► real metrics from analytics API ──► LLM ──► plain-language explanation
              (LLM only rephrases app-computed numbers; never invents stats)
```

---

## 5. Analytics pipeline (input → processing → output)

Each family is a module under `analytics/` and shares helpers in `analytics/common/`.

| Step | Employment | Skill gap | Programme impact |
| --- | --- | --- | --- |
| **Input** | enrollments, certifications, employment rows | skills & labour demand (JobDemand demo) | programme → enrollment → employment joins |
| **Processing** | rates from timestamps & status | demand-vs-supply matching; district roll-up | per-program outcome comparison |
| **Output** | completion / employment / relevant-employment / retention rates | high-demand/low-supply list; district gaps | ranked high/low-performing programmes |

Formulas are defined precisely in `docs/DATABASE.md` **before** analytics coding begins, so the team measures the same thing everywhere.

---

## 6. Auth model (seeded accounts, no public registration)

- `scripts/seed_demo_data.py` inserts a **User per role** (admin/government, provider, trainee) with a known demo password.
- Login issues a **JWT** containing the user id + role.
- Route-level **role guard** (RBAC) controls access; only Admin/Government sees the dashboard.

---

## 7. Development workflow (per phase)

Before each phase: state the files to be created/modified and why → implement **only** that phase → test it → summarize. Use **small, meaningful Git commits**.

---

## 8. 6-day sequence

| Day | Scope |
| --- | --- |
| 1 | Docs + structure + Git (this commit) |
| 2 | SQLAlchemy models + `data/raw|processed` + `scripts/seed_demo_data.py` + `config.py` |
| 3 | Auth (seeded login + JWT + RBAC) + minimal trainee/training/employment routes |
| 4 | Analytics package + read-only analytics/report endpoints + tests |
| 5 | React scaffold + login + role views + **government dashboard (early)** |
| 6 | Dashboard polish + integration & UI testing + demo walkthrough; optional AI (P2) only if time |

**Dashboard-first note:** The government dashboard is prioritised **earlier** (Day 5) so integration and UI testing have enough time before final day — per approved modification.

---

## 9. Non-goals / deferred

- Predictive/ML modelling, forecasting
- Real government or external APIs
- Public user registration
- Microservices, Kafka, Redis, Docker, Kubernetes, blockchain
- Extensive reporting/export and extra chart types (nice-to-have only)
- AI assistant (P2 — only after the core system is working)