import sqlite3

def add_columns():
    try:
        conn = sqlite3.connect('cms.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN father_name VARCHAR(255)")
            print("Added father_name column.")
        except Exception as e:
            print(f"Notice (father_name): {e}")

        try:
            cursor.execute("ALTER TABLE students ADD COLUMN mother_name VARCHAR(255)")
            print("Added mother_name column.")
        except Exception as e:
            print(f"Notice (mother_name): {e}")

        conn.commit()
        print("Database schema successfully updated.")
    except Exception as e:
        print(f"Database connection error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_columns()
