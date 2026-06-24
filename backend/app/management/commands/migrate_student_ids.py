from sqlalchemy import text
from app.database.session import engine
import datetime
from collections import defaultdict


def get_branch_code(dept_code):
    return dept_code[:2].upper() if dept_code else "XX"


def migrate():
    with engine.connect() as conn:
        result = conn.execute(text(
            """
            SELECT s.id, s.admission_date, d.code
            FROM students s
            LEFT JOIN departments d ON s.department_id = d.id
            ORDER BY s.id ASC
            """
        ))
        students = result.fetchall()

        sequence_tracker = defaultdict(lambda: 1)
        updates = []

        for std_id, admission_date, dept_code in students:
            if admission_date:
                try:
                    year = datetime.datetime.strptime(admission_date, "%Y-%m-%d").year
                except Exception:
                    year = datetime.datetime.now().year
            else:
                year = datetime.datetime.now().year

            yy = str(year)[-2:]
            bb = get_branch_code(dept_code)
            prefix = f"{yy}{bb}"

            seq = sequence_tracker[prefix]
            sequence_tracker[prefix] += 1

            new_id = f"{prefix}{seq:03d}"
            updates.append((new_id, std_id))

        # Bulk update
        for new_id, std_id in updates:
            conn.execute(text("UPDATE students SET student_id = :sid WHERE id = :id"), {"sid": new_id, "id": std_id})

        print(f"Re-generated IDs for {len(updates)} students using Department.code!")
        conn.commit()


if __name__ == "__main__":
    migrate()
