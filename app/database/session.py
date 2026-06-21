"""
Database Session Management
==============================

OOP Concepts Demonstrated:
--------------------------
1. SINGLETON PATTERN: engine is created once and reused
2. FACTORY PATTERN: SessionLocal is a session factory
3. ENCAPSULATION: Database connection details are encapsulated here

Why a separate session module?
- Single Responsibility Principle (SRP)
- All database connection logic in one place
- Easy to swap databases (change DATABASE_URL only)
- Session lifecycle managed centrally
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ── SINGLETON PATTERN ────────────────────────────────────────
# The engine is created once when this module is first imported.
# Python's module system ensures it's only created once (singleton).

import os

# Resolve SQLite relative path (./cms.db) to an absolute path so data isn't lost
# if the server is started from a different working directory.
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./"):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_name = db_url.replace("sqlite:///./", "")
    db_url = f"sqlite:///{os.path.join(base_dir, db_name)}"

# SQLite-specific: check_same_thread=False allows multi-threaded access
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before use
)

# Enable foreign key enforcement for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ── FACTORY PATTERN ──────────────────────────────────────────
# SessionLocal is a FACTORY — each call creates a new Session instance.
# It configures how sessions behave (autocommit, autoflush, bind).
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def init_db() -> None:
    """
    Initialize the database — create all tables.

    This is called once at application startup.
    In production, use Alembic migrations instead.
    """
    from app.database.base import Base
    # Import all models so they're registered with Base.metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {settings.DATABASE_URL}")
