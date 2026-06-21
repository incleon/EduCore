from app.database.session import engine
from app.database.base import BaseModel
from app.models.timetable_grid import TimetableVersion, TimetableSlot

def migrate():
    print("Starting migration...")
    
    # Drop old timetable documents table if exists
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS timetable_documents"))
            print("Dropped timetable_documents table.")
    except Exception as e:
        print(f"Note: Could not drop old table (may not exist): {e}")

    # Create new tables
    BaseModel.metadata.create_all(bind=engine, tables=[
        TimetableVersion.__table__,
        TimetableSlot.__table__
    ])
    print("Created timetable_versions and timetable_slots tables.")

if __name__ == "__main__":
    from sqlalchemy import text
    migrate()
