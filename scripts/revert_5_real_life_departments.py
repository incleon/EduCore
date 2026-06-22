import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.department import Department

def main():
    db = SessionLocal()
    try:
        codes_to_remove = ["AER", "ARC", "BIO", "MAT", "PHY"]
        
        for code in codes_to_remove:
            dept = db.query(Department).filter_by(code=code).first()
            if dept:
                db.delete(dept)
                print(f"Removed {dept.name} ({dept.code})")
            else:
                print(f"Department with code {code} not found")

        db.commit()
        print("Successfully reverted the 5 seeded departments!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
