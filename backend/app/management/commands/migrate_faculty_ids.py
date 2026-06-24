from sqlalchemy import text
from app.database.session import engine
import datetime

def migrate():
    with engine.connect() as conn:
        # 1. Add column if it doesn't exist
        try:
            conn.execute(text("ALTER TABLE teachers ADD COLUMN faculty_id VARCHAR(20)"))
            print("Added faculty_id column.")
        except Exception:
            print("Column faculty_id may already exist or cannot be added.")

        # 2. Add unique index
        try:
            conn.execute(text("CREATE UNIQUE INDEX ix_teachers_faculty_id ON teachers(faculty_id)"))
            print("Added unique index.")
        except Exception:
            pass

        # 3. Generate IDs for existing teachers
        result = conn.execute(text("SELECT id, joining_date FROM teachers ORDER BY id ASC"))
        teachers = result.fetchall()

        updates = []
        sequence_tracker = {}

        for t_id, joining_date in teachers:
            if joining_date:
                try:
                    year = datetime.datetime.strptime(joining_date, "%Y-%m-%d").year
                except Exception:
                    year = datetime.datetime.now().year
            else:
                year = datetime.datetime.now().year

            yy = str(year)[-2:]
            prefix = f"FC{yy}"

            if prefix not in sequence_tracker:
                sequence_tracker[prefix] = 1

            seq = sequence_tracker[prefix]
            sequence_tracker[prefix] += 1

            new_id = f"{prefix}{seq:06d}"
            updates.append((new_id, t_id))

        if updates:
            conn.execute(text("""
                UPDATE teachers SET faculty_id = :faculty_id WHERE id = :id
            """), [dict(faculty_id=u[0], id=u[1]) for u in updates])
            print(f"Generated IDs for {len(updates)} teachers!")

        conn.commit()


if __name__ == "__main__":
    migrate()
