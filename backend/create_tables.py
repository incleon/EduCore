import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.database.session import engine
from app.database.base import Base
from app.main import app

print("Creating missing tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
