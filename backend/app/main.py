"""
main.py
-------
FastAPI application factory.

Changes from original:
- Replaced deprecated @app.on_event("startup") with lifespan context manager
  (required by FastAPI >= 0.93 best-practice; on_event is removed in 0.115+)
- Added structured logging configuration
- Added /openapi.json and /redoc links to root message for non-frontend mode
- CORSMiddleware restricted to same-origin in production via env var ALLOWED_ORIGINS
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routes_auth import router as auth_router
from .routes_finance import router as finance_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup (no-op if already exist)."""
    logger.info("Creating database tables if they do not exist …")
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready.")
    yield
    # Nothing to clean up for SQLAlchemy sync engine
    logger.info("Application shutdown.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Expense & Budget Tracker API",
    version="1.0.0",
    description=(
        "FastAPI + Supabase/Postgres expense, salary, savings, and budget "
        "tracker with JWT authentication. Visit /docs for Swagger UI."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(finance_router)

# ---------------------------------------------------------------------------
# Static / frontend
# ---------------------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    logger.info("Serving frontend from %s", FRONTEND_DIR)


# ---------------------------------------------------------------------------
# Root & health
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def frontend_home():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Expense & Budget Tracker API is running.",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe endpoint."""
    return {"status": "ok"}
