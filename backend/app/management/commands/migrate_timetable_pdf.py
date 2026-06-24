from sqlalchemy import create_engine
from app.database.session import engine
from app.models.timetable import TimetableDocument

def migrate():
    print("Dropping old timetables table...")
    with engine.connect() as conn:
        try:
            conn.execute("DROP TABLE IF EXISTS timetables")
            print("Dropped timetables table successfully.")
        except Exception as e:
            print(f"Error dropping table: {e}")
            
    print("Creating new timetable_documents table...")
    TimetableDocument.metadata.create_all(engine, tables=[TimetableDocument.__table__])
    print("Successfully created timetable_documents table!")

if __name__ == "__main__":
    migrate()
