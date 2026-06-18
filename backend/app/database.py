"""
database.py
-----------
Database engine and session factory.

Driver resolution order:
  1. If DATABASE_URL is empty/unset  -> SQLite (budget_app.db inside backend/)
  2. If PostgreSQL URL given          -> try psycopg v3 first, fall back to psycopg2
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

# Load .env from backend/ directory (one level above this file)
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()

# Default to SQLite when no DATABASE_URL is configured
if not DATABASE_URL:
    _sqlite_path = BASE_DIR / "budget_app.db"
    DATABASE_URL = f"sqlite:///{_sqlite_path}"
    logger.info("No DATABASE_URL set — using SQLite at %s", _sqlite_path)


def _resolve_postgres_url(url: str) -> str:
    """
    Normalise a PostgreSQL URL to use the available driver.
    - Tries psycopg v3 first (postgresql+psycopg://)
    - Falls back to psycopg2      (postgresql+psycopg2://)
    - Supabase-style postgres://   is also accepted
    """
    # Strip bare scheme variants first
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    # Already has explicit driver prefix – leave as-is
    if "+" in url.split("://")[0]:
        return url

    # Try psycopg v3
    try:
        import psycopg  # noqa: F401
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        pass

    # Fall back to psycopg2
    try:
        import psycopg2  # noqa: F401
        logger.warning(
            "psycopg (v3) not found; falling back to psycopg2. "
            "Install psycopg[binary] for best Supabase compatibility."
        )
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    except ImportError:
        raise RuntimeError(
            "No PostgreSQL driver found. "
            "Install psycopg[binary] or psycopg2-binary."
        )


# Resolve the final URL
if DATABASE_URL.startswith(("postgres://", "postgresql")):
    DATABASE_URL = _resolve_postgres_url(DATABASE_URL)

connect_args: dict = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
