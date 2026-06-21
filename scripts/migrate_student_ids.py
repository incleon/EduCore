import sqlite3
import datetime
from collections import defaultdict

def get_branch_code(dept_code):
    return dept_code[:2].upper() if dept_code else "XX"

def migrate():
    conn = sqlite3.connect("cms.db")
    cursor = conn.cursor()

    # We skip creating the column and index because they already exist from the previous run.

    # Fetch all students
    cursor.execute('''
        SELECT s.id, s.admission_date, d.code
        FROM students s
        LEFT JOIN departments d ON s.department_id = d.id
        ORDER BY s.id ASC
    ''')
    students = cursor.fetchall()

    sequence_tracker = defaultdict(lambda: 1)
    updates = []

    for std_id, admission_date, dept_code in students:
        if admission_date:
            try:
                year = datetime.datetime.strptime(admission_date, "%Y-%m-%d").year
            except:
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

    cursor.executemany("UPDATE students SET student_id = ? WHERE id = ?", updates)
    print(f"Re-generated IDs for {len(updates)} students using Department.code!")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
