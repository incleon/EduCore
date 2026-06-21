import sqlite3

def main():
    try:
        conn = sqlite3.connect('cms.db')
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE students ADD COLUMN personal_email VARCHAR(255)")
        conn.commit()
        print("Successfully added personal_email column to students table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column already exists.")
        else:
            print(f"OperationalError: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
