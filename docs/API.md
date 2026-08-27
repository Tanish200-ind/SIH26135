# API.md — SIH26135 Planned Endpoint Contract

> Prototype API contract. Endpoints and request/response shapes are agreed here before implementation so frontend and backend stay aligned. Subject to refinement during building.

## 1. Conventions

- Base URL: `http://localhost:8000`
- All payloads are **JSON**; validation by Pydantic.
- Auth: JWT `/login` returns a token; protected routes require `Authorization: Bearer <token>`.
- Role guard (RBAC): `admin`, `provider`, `trainee`. Only `admin` (Government) may access dashboard/analytics endpoints.

---

## 2. Auth (seeded accounts, no public registration)

There is **no `/register`** endpoint. Demo users are seeded by `scripts/seed_demo_data.py`.

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | public | Accept email+password, return JWT + role |
| GET | `/api/auth/me` | any | Return current user info + role |

**Seeded demo accounts (demonstration-only credentials, do not treat as production):**

| Role | Email | Password |
| --- | --- | --- |
| Admin/Government | `admin@sih.gov.in` | `demo123` |
| Training provider | `provider@sih.gov.in` | `demo123` |
| Trainee | `trainee@sih.gov.in` | `demo123` |

All three are created by `scripts/seed_demo_data.py`; the JWT signing secret is never committed (see `backend/app/config.py`).

---

## 3. Trainee domain (minimal CRUD)

| Method | Path | Auth (role) | Description |
| --- | --- | --- | --- |
| GET | `/api/trainees` | admin, provider | List trainees |
| GET | `/api/trainees/{id}` | admin, provider, trainee(own) | Trainee detail (profile, skills, education) |
| POST | `/api/trainees` | admin, provider | Create trainee (and linked User) |
| PATCH | `/api/trainees/{id}` | admin, trainee(own) | Update trainee profile |
| PUT | `/api/trainees/{id}/skills` | admin, trainee(own) | Set trainee skills |
| PUT | `/api/trainees/{id}/education` | admin, trainee(own) | Set education level |

---

## 4. Training domain

| Method | Path | Auth (role) | Description |
| --- | --- | --- | --- |
| GET | `/api/providers` | admin | List providers |
| GET | `/api/programs` | admin, provider(view own) | List training programmes |
| **POST** | `/api/programs` | **provider** | Create programme — provider identity always resolved server-side from the JWT (client-supplied ownership is ignored); `skill_ids` must reference `/api/skills`; body: `{name, description?, duration_weeks, status(active\|closed), skill_ids}` |
| GET | `/api/skills` | admin, provider, trainee | Skill catalog (used by the add-programme form) |
| GET | `/api/programs/available` | **trainee** | All programmes annotated with the caller's enrollment state (`enrolled`, `enrollment_status`); active listed first |
| GET | `/api/programs/{id}` | admin, provider, trainee | Programme + skills taught |
| GET | `/api/trainees/me/enrollments` | **trainee** | The authenticated trainee's own enrollments |
| **POST** | `/api/trainees/me/enrollments` | **trainee** | Self-enrollment `{program_id}`; closed programme or duplicate ⇒ 409, unknown programme ⇒ 404 |

Not implemented in the prototype (planned-only): `POST /api/programs/{id}/skills`, `POST /api/programs/{id}/enroll`, `PATCH /api/enrollments/{id}`. Skills are attached at creation time; enrollment is self-service (trainees enrol themselves).

---

## 5. Employment domain

| Method | Path | Auth (role) | Description |
| --- | --- | --- | --- |
| GET | `/api/employment` | admin, provider | List employment records (history) |
| GET | `/api/trainees/{id}/employment` | admin, provider, trainee(own) | Trainee employment history |
| POST | `/api/employment` | admin, provider | Record employment (status, role, industry, salary, start_date, still_employed) |
| PATCH | `/api/employment/{id}` | admin, provider, trainee(own) | Update employment / retention status |

---

## 6. Analytics & dashboard (read-only; admin/government only)

Formulas per `docs/DATABASE.md`.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/analytics/employment` | Completion, employment, relevant-employment, retention rates (overall + per program) |
| GET | `/api/analytics/skill-gap` | High-demand/low-supply skills; district-wise gaps |
| GET | `/api/analytics/program-impact` | Per-program outcomes; high/low performing programmes |
| GET | `/api/dashboard/summary` | Consolidated headline numbers for the Government dashboard |

Query params (planned): `district`, `program_id`, `from_date`, `to_date`.

---

## 7. Non-goals

- No `/register`, no public signup.
- No real external integrations.
- Analytics/dashboard endpoints are **strictly read-only** (no mutation).