# PROJECT AUDIT REPORT

**Project:** Budget Bloom — Expense & Budget Tracker
**Audit Date:** 2026-06-18
**Auditor:** Kiro AI (Senior Software Engineer / Architect / QA / DevOps)

---

## 1. Project Type

Full-stack web application — personal finance tracker.

| Layer     | Technology                                |
|-----------|-------------------------------------------|
| Backend   | Python 3.11 · FastAPI 0.115 · SQLAlchemy 2.0 |
| Frontend  | Vanilla HTML5 + CSS3 + JavaScript (ES2022) |
| Database  | SQLite (local dev) / PostgreSQL via Supabase |
| Auth      | JWT (HS256) · PBKDF2-SHA256 password hash  |
| Server    | Uvicorn (ASGI)                             |

---

## 2. Frameworks Detected

- **FastAPI 0.115.6** — async REST API framework
- **SQLAlchemy 2.0.36** — ORM with DeclarativeBase (modern style)
- **Pydantic v2.10.4** — request/response validation
- **python-jose 3.3.0** — JWT encode/decode
- **python-dotenv 1.0.1** — `.env` file loading
- **Uvicorn 0.34.0** — production-grade ASGI server

---

## 3. Dependencies Detected

From `backend/requirements.txt`:

| Package | Pinned Version | Purpose |
|---------|---------------|---------|
| fastapi | 0.115.6 | Web framework |
| uvicorn[standard] | 0.34.0 | ASGI server |
| SQLAlchemy | 2.0.36 | ORM |
| psycopg[binary] | 3.2.3 | PostgreSQL driver v3 |
| psycopg2-binary | 2.9.9 | PostgreSQL driver v2 fallback |
| python-jose[cryptography] | 3.3.0 | JWT |
| cryptography | 42.0.8 | Crypto primitives (pinned for jose compat) |
| python-dotenv | 1.0.1 | Env vars |
| pydantic[email] | 2.10.4 | Validation |
| python-multipart | 0.0.9 | Form parsing (OAuth2/Swagger) |

---

## 4. Architecture Overview

```
expense-budget-fastapi-supabase/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Package marker (empty — correct)
│   │   ├── main.py              # FastAPI app factory + lifespan + CORS + static
│   │   ├── database.py          # Engine, SessionLocal, Base, get_db()
│   │   ├── models.py            # SQLAlchemy ORM: User, Income, Expense, Saving, Budget
│   │   ├── schemas.py           # Pydantic schemas (Create/Out for each model)
│   │   ├── auth.py              # PBKDF2 hashing + JWT create/decode
│   │   ├── deps.py              # get_current_user() FastAPI dependency
│   │   ├── routes_auth.py       # /auth/register · /auth/login · /auth/token · /auth/me
│   │   └── routes_finance.py    # /finance/* CRUD + summary + charts
│   ├── .env.example             # Template — copy to .env
│   └── requirements.txt         # Pinned Python deps
├── frontend/
│   ├── index.html               # SPA shell (served at /)
│   ├── style.css                # Design system CSS (custom properties)
│   └── app.js                   # Vanilla JS — auth + CRUD + charts
├── postman/
│   └── Expense_Budget_API.postman_collection.json
├── supabase/
│   └── schema.sql               # Manual Supabase SQL (optional — auto-created on start)
├── run_backend_windows.bat
├── run_backend_mac_linux.sh
└── README.md
```

**Data flow:**
```
Browser → GET / → FastAPI serves index.html (StaticFiles)
Browser → POST /auth/register → creates user, returns JWT
Browser → POST /finance/salary → (Bearer JWT) → creates income row
Browser → GET /finance/summary → (Bearer JWT) → aggregates totals
```

---

## 5. Issues Found

| # | Severity | File | Issue |
|---|----------|------|-------|
| 1 | **CRITICAL** | `requirements.txt` | `psycopg[binary]==3.2.3` not installed on host; only `psycopg2` available → PostgreSQL connections fail silently |
| 2 | **CRITICAL** | `database.py` | URL rewrite always emits `postgresql+psycopg://` regardless of whether psycopg v3 is installed → ImportError at runtime with Supabase |
| 3 | **HIGH** | `main.py` | `@app.on_event("startup")` is deprecated since FastAPI 0.93; removed in 0.115 → triggers deprecation warning on every start |
| 4 | **HIGH** | `deps.py` | `tokenUrl="/auth/login"` points to JSON endpoint; Swagger UI sends form-data → "Authorize" button broken in /docs |
| 5 | **HIGH** | `requirements.txt` | `python-multipart` missing → FastAPI cannot parse OAuth2 form data (Swagger auth fails) |
| 6 | **HIGH** | `requirements.txt` | `cryptography` not pinned → python-jose 3.3.0 breaks with cryptography ≥ 43 |
| 7 | **MEDIUM** | `schemas.py` | `user_id` missing from all `*Out` schemas → API consumers cannot identify record ownership |
| 8 | **MEDIUM** | `routes_auth.py` | No OAuth2 form login endpoint (`/auth/token`) → Swagger Authorize unusable |
| 9 | **MEDIUM** | `routes_finance.py` | No pagination on list endpoints → unbounded queries for large datasets |
| 10 | **LOW** | `auth.py` | No warning when default insecure `SECRET_KEY` is used → silent security risk in production |
| 11 | **LOW** | `main.py` | `ALLOWED_ORIGINS=["*"]` hardcoded → no way to restrict CORS for production without code change |
| 12 | **LOW** | `.env.example` | Missing `ALLOWED_ORIGINS` variable → incomplete environment documentation |
| 13 | **LOW** | `models.py` | `nullable` not explicitly set on all non-nullable columns → relies on implicit defaults |
| 14 | **LOW** | All routes | No structured logging → ops teams cannot trace request failures |

---

## 6. Severity Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 4 |
| MEDIUM | 3 |
| LOW | 5 |
| **TOTAL** | **14** |

---

## 7. Recommended Fixes (all applied)

1. Add `psycopg2-binary==2.9.9` to requirements + smart driver detection in `database.py`
2. Rewrite `database.py` with psycopg v3 → v2 fallback logic
3. Replace `@app.on_event("startup")` with `@asynccontextmanager lifespan`
4. Add `/auth/token` OAuth2 form endpoint + update `tokenUrl` in `deps.py`
5. Add `python-multipart==0.0.9` to requirements
6. Pin `cryptography==42.0.8` in requirements
7. Add `user_id` to all `*Out` Pydantic schemas
8. Add pagination `limit`/`offset` to all list endpoints
9. Add startup warning when default `SECRET_KEY` is active
10. Make `ALLOWED_ORIGINS` configurable via env var
11. Update `.env.example` with all variables including `ALLOWED_ORIGINS`
12. Add explicit `nullable=False` to all required model columns
13. Add `logging` to `auth.py`, `deps.py`, `routes_auth.py`, `routes_finance.py`, `main.py`
