"""List tables in the configured database using SQLAlchemy Inspector."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database.session import engine
from sqlalchemy import inspect

inspector = inspect(engine)

print("Tables:")
for t in inspector.get_table_names():
    print(f"- {t}")

print("\nViews:")
for v in inspector.get_view_names():
    print(f"- {v}")
