"""Initialize schema and seed the MySQL database using the application's models.

Run from project root (using your virtualenv):

    python scripts\init_and_seed_db.py

This will call `Base.metadata.create_all()` and then run the existing seed logic.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root in path
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
# Make project root importable
import sys
sys.path.insert(0, str(ROOT))

# Import application DB helpers
from app.database.session import init_db, SessionLocal
from app.database.seed import seed_database
from app.core.logging_config import setup_logging

setup_logging()

print("Initializing database schema...")
init_db()

print("Seeding database with demo data (if not already seeded)...")
# Use a session to run seed_database
db = SessionLocal()
try:
    seed_database(db)
finally:
    db.close()

print("Done. Schema created and seed completed.")
