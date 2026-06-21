import sqlite3
import datetime

def migrate():
    conn = sqlite3.connect("cms.db")
    cursor = conn.cursor()

    # 1. Add column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE teachers ADD COLUMN faculty_id VARCHAR(20)")
        print("Added faculty_id column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column faculty_id already exists.")
        else:
            raise e

    # 2. Add index if it doesn't exist
    try:
        cursor.execute("CREATE UNIQUE INDEX ix_teachers_faculty_id ON teachers(faculty_id)")
        print("Added unique index.")
    except sqlite3.OperationalError as e:
        pass

    # 3. Generate IDs for existing teachers
    cursor.execute('''
        SELECT id, joining_date FROM teachers ORDER BY id ASC
    ''')
    teachers = cursor.fetchall()

    updates = []
    
    # We will just track sequence counts by year
    sequence_tracker = {}
    
    for t_id, joining_date in teachers:
        if joining_date:
            try:
                year = datetime.datetime.strptime(joining_date, "%Y-%m-%d").year
            except:
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
        cursor.executemany("UPDATE teachers SET faculty_id = ? WHERE id = ?", updates)
        print(f"Generated IDs for {len(updates)} teachers!")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
