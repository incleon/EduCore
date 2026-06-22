import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.department import Department
from app.models.course import Course

def main():
    db = SessionLocal()
    try:
        # Get a general course, or create one if it doesn't exist
        course = db.query(Course).filter_by(code="BSC").first()
        if not course:
            # Let's try to get any course first
            course = db.query(Course).first()
            if not course:
                course = Course(name="B.Sc", code="BSC", description="Bachelor of Science", duration_years="3 years")
                db.add(course)
                db.flush()

        depts = [
            ("Aeronautics", "AER"),
            ("Architecture", "ARC"),
            ("Biotechnology", "BIO"),
            ("Mathematics", "MAT"),
            ("Physics", "PHY")
        ]

        for name, code in depts:
            d = db.query(Department).filter((Department.code == code) | (Department.name == name)).first()
            if not d:
                d = Department(name=name, code=code, description=f"Department of {name}", course_id=course.id)
                db.add(d)
                print(f"Added {name} ({code})")
            else:
                print(f"{name} ({code}) already exists")

        db.commit()
        print("Successfully seeded 5 real life departments!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
