import os
import sys
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.fee import Fee, FeeType, FeeStatus
from app.models.student import Student

def generate_fees():
    db = SessionLocal()
    try:
        students = db.query(Student).all()
        if not students:
            print("No students found. Run the main seeder first.")
            return

        fees_added = 0
        for student in students:
            # Check if student already has fees
            existing_fee = db.query(Fee).filter(Fee.student_id == student.id).first()
            if existing_fee:
                continue

            # Add Tuition Fee (Pending)
            tuition = Fee(
                student_id=student.id,
                fee_type=FeeType.TUITION,
                amount=50000.0,
                paid_amount=0.0,
                due_date=date.today() + timedelta(days=30),
                status=FeeStatus.PENDING,
                semester=student.semester
            )
            
            # Add Library Fee (Partial)
            library = Fee(
                student_id=student.id,
                fee_type=FeeType.LIBRARY,
                amount=2000.0,
                paid_amount=1000.0,
                due_date=date.today() - timedelta(days=5),
                status=FeeStatus.PARTIAL,
                semester=student.semester
            )

            # Add Hostel Fee (Paid)
            hostel = Fee(
                student_id=student.id,
                fee_type=FeeType.HOSTEL,
                amount=15000.0,
                paid_amount=15000.0,
                due_date=date.today() - timedelta(days=60),
                paid_date=date.today() - timedelta(days=65),
                status=FeeStatus.PAID,
                semester=student.semester,
                receipt_number=f"RCP-{student.id}-HSTL"
            )

            db.add_all([tuition, library, hostel])
            fees_added += 3

        db.commit()
        print(f"Successfully generated {fees_added} fee records for {len(students)} students.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_fees()
