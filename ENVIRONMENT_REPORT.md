# ENVIRONMENT REPORT

**Project:** Budget Bloom
**Date:** 2026-06-18

---

## 1. Environment Files Found

| File | Status |
|------|--------|
| `backend/.env.example` | Found — updated |
| `backend/.env` | **NOT FOUND** — must be created by developer |

> The `.env` file is intentionally gitignored. Developers must copy `.env.example → .env`.

---

## 2. Required Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./budget_app.db` | PostgreSQL/Supabase connection string. Empty = SQLite fallback |
| `SECRET_KEY` | **YES** (prod) | `CHANGE_ME_TO_A_LONG_RANDOM_SECRET` | JWT signing secret. Must be changed before deployment |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm. Supported: HS256, HS384, HS512 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` (24h) | Token lifetime in minutes |
| `ALLOWED_ORIGINS` | No | `*` | CORS allowed origins. Use comma-separated list for production |

---

## 3. Issues Found

### Issue 1 — HIGH: No `.env` file present

**Problem:** `backend/.env` does not exist. The app falls back to:
- `DATABASE_URL = ""` → SQLite (acceptable for local dev)
- `SECRET_KEY = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"` → **insecure for production**

**Fix Applied:** Added startup warning in `auth.py` when default `SECRET_KEY` is detected:
```
WARNING: SECRET_KEY is using the insecure default. Set SECRET_KEY in backend/.env before deploying.
```

**Action Required:** Run:
```bat
copy backend\.env.example backend\.env
```
Then edit `backend\.env` and set a real `SECRET_KEY`.

### Issue 2 — MEDIUM: `ALLOWED_ORIGINS` not documented in original `.env.example`

**Problem:** The original `.env.example` had no `ALLOWED_ORIGINS` variable, but the
app defaulted to `allow_origins=["*"]` hardcoded — no way to restrict without code change.

**Fix Applied:** Added `ALLOWED_ORIGINS` to:
- `backend/.env.example` (with documentation)
- `backend/app/main.py` (reads from env, defaults to `*`)

### Issue 3 — LOW: `SECRET_KEY` default value too weak

**Problem:** The default placeholder `"CHANGE_ME_TO_A_LONG_RANDOM_SECRET"` is only 37 chars
and predictable — if deployed without changing it, JWTs can be forged.

**Fix Applied:** Added startup log warning. Recommended generation command added to `.env.example`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 4. Updated `.env.example`

```env
# DATABASE — leave empty for SQLite (local dev)
DATABASE_URL=

# JWT Secret — CHANGE THIS in production
SECRET_KEY=change-this-to-a-long-random-secret-key

# JWT config
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS — restrict to your domain in production
ALLOWED_ORIGINS=*
```

---

## 5. Local Setup Commands

```bat
# Windows
copy backend\.env.example backend\.env
notepad backend\.env
```

```bash
# Mac/Linux
cp backend/.env.example backend/.env
nano backend/.env
```

---

## 6. Database URL Examples

```env
# SQLite (local dev — no setup needed)
DATABASE_URL=

# Supabase Direct (port 5432)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOURREF.supabase.co:5432/postgres

# Supabase Pooler (port 6543)
DATABASE_URL=postgresql://postgres.YOURREF:YOUR_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

# Local PostgreSQL
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/budget_bloom
```
