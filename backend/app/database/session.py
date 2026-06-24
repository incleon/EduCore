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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ── SINGLETON PATTERN ────────────────────────────────────────
# The engine is created once when this module is first imported.
# Python's module system ensures it's only created once (singleton).

# Use application's DATABASE_URL (MySQL by default).
db_url = settings.DATABASE_URL

# MySQL uses standard connection args
connect_args = {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before use
    pool_size=10,         # Number of connections to keep in the pool
    max_overflow=20,      # Maximum overflow connections above pool_size
    pool_recycle=3600,    # Recycle connections after 1 hour (MySQL default)
    pool_timeout=30,      # Timeout waiting for a connection
)

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
