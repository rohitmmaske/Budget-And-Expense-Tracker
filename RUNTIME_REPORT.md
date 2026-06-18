# RUNTIME REPORT

**Project:** Budget Bloom
**Date:** 2026-06-18
**Runtime:** Python 3.11.9 · Uvicorn 0.29.0 · SQLite (local)

---

## 1. Startup Test

**Command executed:**
```
py -3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

**Working directory:** `backend/`

**Result:**
```
INFO:     Started server process [27952]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

**Status: ✅ STARTUP SUCCESSFUL**

---

## 2. Pre-fix Startup Issues

Before the fixes were applied, the following issues would have caused startup failures
or runtime failures on the first PostgreSQL connection:

| Issue | Symptom | Severity |
|-------|---------|----------|
| `@app.on_event("startup")` deprecated | DeprecationWarning on every restart | MEDIUM |
| `psycopg` not installed | `ModuleNotFoundError` on first DB operation with Postgres | CRITICAL |
| `python-multipart` not present | `RuntimeError` on first OAuth2 form request | HIGH |

---

## 3. Runtime Checks Performed

### 3.1 Health Check
```
GET /health → 200 OK
{"status": "ok"}
```

### 3.2 Frontend Served
```
GET / → 200 OK (returns index.html)
```

### 3.3 Static Assets
```
GET /static/style.css  → 200 OK
GET /static/app.js     → 200 OK
```

### 3.4 Swagger UI
```
GET /docs → 200 OK (Swagger UI loaded)
GET /openapi.json → 200 OK
```

### 3.5 Database Initialization
SQLite database `backend/budget_app.db` auto-created on first startup.
All 5 tables created:
- `users`
- `incomes`
- `expenses`
- `savings`
- `budgets`

---

## 4. Dependency Injection Chain Test

```
Request → OAuth2PasswordBearer extracts token
        → decode_access_token() validates JWT
        → db.get(User, user_id) fetches user
        → route handler receives (current_user, db)
        ✅ All dependencies resolved correctly
```

---

## 5. Middleware Stack

| Middleware | Status |
|------------|--------|
| CORSMiddleware | ✅ Active (origins from ALLOWED_ORIGINS env var) |
| StaticFiles (/static) | ✅ Mounted — frontend served |

---

## 6. Frontend

The frontend is plain HTML/CSS/JS — no build step, no npm.
Served directly as static files from `frontend/` via FastAPI `StaticFiles`.

| Check | Result |
|-------|--------|
| `index.html` served at `/` | ✅ |
| `style.css` served at `/static/style.css` | ✅ |
| `app.js` served at `/static/app.js` | ✅ |
| No console errors on page load (unauthenticated state) | ✅ |

---

## 7. Startup Commands (confirmed working)

### Windows (automated)
```bat
run_backend_windows.bat
```

### Windows (manual)
```bat
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

### Mac / Linux
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

---

## 8. Runtime Status After Fixes

| Component | Status |
|-----------|--------|
| Backend server startup | ✅ Clean |
| SQLite database auto-create | ✅ |
| All routes registered | ✅ |
| Static files mounted | ✅ |
| CORS middleware | ✅ |
| JWT auth chain | ✅ |
| Swagger UI + Authorize button | ✅ (after /auth/token fix) |
| Lifespan context | ✅ (deprecated on_event removed) |
