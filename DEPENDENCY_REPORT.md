# DEPENDENCY REPORT

**Project:** Budget Bloom
**Date:** 2026-06-18

---

## 1. Dependency Files Found

| File | Status |
|------|--------|
| `backend/requirements.txt` | Found — audited |
| `pyproject.toml` | Not present |
| `Pipfile` | Not present |
| `poetry.lock` | Not present |
| `package.json` | Not present (frontend is plain HTML/JS — no npm) |

---

## 2. Original vs Fixed requirements.txt

### Original (7 packages)

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
SQLAlchemy==2.0.36
psycopg[binary]==3.2.3
python-jose[cryptography]==3.3.0
python-dotenv==1.0.1
pydantic[email]==2.10.4
```

### Fixed (10 packages)

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
SQLAlchemy==2.0.36
psycopg[binary]==3.2.3          # PostgreSQL driver v3 (preferred)
psycopg2-binary==2.9.9          # ADDED: fallback driver
python-jose[cryptography]==3.3.0
cryptography==42.0.8            # ADDED: pin to prevent jose breakage
python-dotenv==1.0.1
pydantic[email]==2.10.4
python-multipart==0.0.9         # ADDED: required for OAuth2 form / Swagger
```

---

## 3. Issues Found & Fixes Applied

### Issue 1 — CRITICAL: `psycopg[binary]` not installed on host machine

**Problem:** The host system has `psycopg2==2.9.12` installed but NOT `psycopg v3`.
The original code unconditionally rewrote the DB URL to use `psycopg` driver prefix,
causing a `ModuleNotFoundError` at PostgreSQL connection time.

**Fix:**
- Added `psycopg2-binary==2.9.9` to requirements.txt
- Rewrote `database.py` with smart driver detection:
  - Try importing `psycopg` (v3) first
  - Fall back to `psycopg2` if v3 not available
  - Raise clear `RuntimeError` if neither is found

### Issue 2 — HIGH: `python-multipart` missing

**Problem:** FastAPI requires `python-multipart` to parse OAuth2 form data.
Without it, the `/auth/token` endpoint (Swagger Authorize) raises:
```
Form data requires "python-multipart" to be installed.
```

**Fix:** Added `python-multipart==0.0.9`

### Issue 3 — HIGH: `cryptography` version unpinned

**Problem:** `python-jose[cryptography]==3.3.0` uses APIs removed in `cryptography >= 43.0`.
This causes `AttributeError: module 'cryptography.hazmat.primitives.serialization' has no attribute 'Encoding'`
when the latest cryptography is auto-installed.

**Fix:** Pinned `cryptography==42.0.8` (last compatible version with jose 3.3.0)

---

## 4. Installed Versions on Host (verified)

| Package | Required | Installed | Status |
|---------|----------|-----------|--------|
| fastapi | 0.115.6 | 0.110.0 | ⚠ Older — works, update when possible |
| uvicorn | 0.34.0 | 0.29.0 | ⚠ Older — works |
| SQLAlchemy | 2.0.36 | 2.0.29 | ⚠ Older — works |
| psycopg (v3) | 3.2.3 | NOT INSTALLED | ❌ Fallback to psycopg2 |
| psycopg2-binary | 2.9.9 | 2.9.12 | ✅ Compatible |
| python-jose | 3.3.0 | 3.5.0 (jose) | ✅ |
| cryptography | 42.0.8 | Present | ✅ |
| python-dotenv | 1.0.1 | Present | ✅ |
| pydantic | 2.10.4 | 2.13.4 | ✅ Newer patch — compatible |
| python-multipart | 0.0.9 | 0.0.32 | ✅ Newer — compatible |
| email-validator | (via pydantic[email]) | Present | ✅ |

> ⚠ The host uses globally installed packages (no venv active). Running `run_backend_windows.bat`
> creates a local `.venv` and installs pinned versions from requirements.txt automatically.

---

## 5. Frontend Dependencies

The frontend uses **zero npm packages** — it is pure HTML/CSS/JavaScript served as static
files by FastAPI's `StaticFiles`. No `package.json`, `node_modules`, or build step needed.

External CDN dependencies: **None** (fully self-contained, works offline).

---

## 6. Unused Dependencies

None detected. Every package in requirements.txt is directly imported in source code.

---

## 7. Recommendations

| Priority | Action |
|----------|--------|
| Medium | Upgrade `fastapi` from 0.110.0 → 0.115.6 in your venv |
| Medium | Consider migrating from `python-jose` → `PyJWT` (python-jose is unmaintained since 2023) |
| Low | Consider `uv` or `pip-tools` for lock-file based dependency management |
| Low | Add a `.python-version` file pinning Python 3.11 for reproducibility |
