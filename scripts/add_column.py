from sqlalchemy import text
from app.database.session import engine

def main():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN personal_email VARCHAR(255)"))
            conn.commit()
            print("Successfully added personal_email column to students table.")
        except Exception as e:
            if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                print("Column already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
