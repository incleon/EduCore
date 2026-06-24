from sqlalchemy import text
from app.core.config import settings
from app.database.session import engine

def add_columns():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN father_name VARCHAR(255)"))
            print("Added father_name column.")
        except Exception as e:
            print(f"Notice (father_name): {e}")

        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN mother_name VARCHAR(255)"))
            print("Added mother_name column.")
        except Exception as e:
            print(f"Notice (mother_name): {e}")

        conn.commit()
        print("Database schema successfully updated.")


if __name__ == "__main__":
    add_columns()
