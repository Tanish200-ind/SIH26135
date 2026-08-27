# SIH26135 — Demo Guide

Everything you need to run and present the **StatAvishkar** skilling-intelligence
prototype. All data shown anywhere in the app is **synthetic demo data** produced
by `scripts/seed_demo_data.py`.

---

## 1. Starting the application

**Prerequisites:** Python 3.12+, Node.js 18+, and

```bash
python -m pip install -r requirements.txt   # backend deps (incl. uvicorn)
cd frontend && npm install                  # one-time frontend install
```

### Backend (terminal 1, from repo root)

```bash
# Only if data/processed/sih26135.db does not exist yet:
python -m scripts.seed_demo_data

python -m uvicorn backend.app.main:app --port 8000
```

Verify: <http://localhost:8000/api/health> →
`{"status":"ok","app":...,"database":"connected"}` (503 means the database could
not be opened).

### Frontend (terminal 2)

```bash
cd frontend
npm run dev          # development server on http://localhost:5173
```

For a production-style run: `npm run build` then `npm run preview`.
The Vite dev/preview server proxies `/api/*` to `http://localhost:8000`
(see `frontend/vite.config.js`), so the browser talks to FastAPI same-origin.

---

## 2. Demo credentials (seeded, prototype-only)

| Role | Email | Password |
| --- | --- | --- |
| Admin / Government | `admin@sih.gov.in` | `demo123` |
| Training Provider | `provider@sih.gov.in` | `demo123` |
| Trainee | `trainee@sih.gov.in` | `demo123` |

The login screen has one-click pills that pre-fill each account.

---

## 3. Recommended demo sequence (~5 minutes)

1. **Login as Government admin.**
2. **Dashboard (home).** Watch the typewriter headline, metric cards count up,
   skill-gap bars animate. Point at the dashed **"Synthetic demo data"** pill.
3. **Employment outcomes** — four overall KPIs plus per-programme table.
4. **Skill gaps** — ranked high-demand/low-supply skills, full demand-vs-supply
   table, district roll-up.
5. **Programme impact** — outcome-comparison ranking; read the framing banner.
6. **Sign out**, log in as **Provider** — sees own programmes/trainees only;
   no analytics pages exist for this role.
7. Log in as **Trainee** — sees only own profile and employment history.
8. Optional negative demos: wrong password (friendly error); call
   `GET /api/analytics/employment` with a provider/trainee token → **403**.

---

## 4. What each screen demonstrates

| Screen (role) | Demonstrates |
| --- | --- |
| Login | Seeded-account JWT auth, role detection, graceful wrong-password errors |
| Dashboard (admin) | All three analytic areas in one view; every number fetched from `/api/analytics/*` |
| Employment outcomes (admin) | Training completion, employment, relevant-employment, retention rates — overall and per programme (`docs/DATABASE.md §3.1`) |
| Skill gaps (admin) | JobDemand-driven demand vs trained supply, gap = demand − supply, proficiency threshold, district views (`§3.2`) |
| Programme impact (admin) | Deterministic outcome comparison/ranking across programmes (**not** causal impact) |
| Provider overview | Role-scoped read access to own programmes and the trainee roster |
| My profile (trainee) | Self-service access to own record via `GET /api/trainees/me`; other trainees' data is forbidden |

## 5. Expected analytics (typical values for the current seed)

Employment: ~93% completion · ~87% employment · ~95% relevant employment ·
~100% retention over the window. Largest gaps: Python Programming (~108),
Solar Panel Installation (~103), Data Analysis (~98). Top-ranked programme:
Full-Stack Web Development. Districts covered: Pune, Nagpur, Nashik, Aurangabad.

> Exact figures vary with the seed generation run — always narrate them as
> *"computed live from the seeded dataset"* rather than quoting from memory.

---

## 6. What we can and cannot claim

**Can claim**

- End-to-end pipeline: SQLite → SQLAlchemy → deterministic analytics → read-only API → React dashboard.
- All displayed metrics are computed **live from the API** against the seeded database; nothing is hard-coded in the UI.
- Formula-defined metrics (documented in `docs/DATABASE.md §3`) and reproducible rankings.
- Role-based access control verified by automated tests (401 without token, 403 for unauthorised roles).

**Cannot claim**

- The numbers represent real Maharashtra skilling data — the dataset is synthetic.
- Causal proof that any programme *caused* its outcomes — programme "impact" is an **outcome comparison/correlation**.
- Production security, scalability, or real-world integration readiness.

---

## 7. Troubleshooting / backup plan

| Symptom | Cause & fix |
| --- | --- |
| Vite logs `http proxy error ... ECONNREFUSED` | Backend is not running on :8000 — start it (§1). This was observed live during Day-6 testing. |
| `/api/health` returns **503 Database unavailable** | Database file missing or locked — re-run `python -m scripts.seed_demo_data`, or delete `data/processed/sih26135.db` first. |
| Port already in use | Use `--port 8001` on uvicorn **and** update the Vite proxy target in `frontend/vite.config.js`. |
| Blank dashboard with "This view is unavailable" | Signed-in role lacks access (analytics are admin-only) or the token expired (default 8 h) — sign out and back in. |
| Seed script complains about existing rows | Delete `data/processed/sih26135.db` and re-run it (the seeder targets a fresh file). |
| No internet at venue | Not a problem: the app is fully local; there are **no external API calls** (the optional AI assistant was intentionally omitted — see `docs/AI_RULES.md`). |

Last resort: present `docs/DATABASE.md` formulas plus `day4` representative
outputs from the test suite instead of the live UI.
