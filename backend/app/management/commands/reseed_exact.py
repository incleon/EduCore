import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.department import Department
from app.models.course import Course
from app.models.subject import Subject

def main():
    db = SessionLocal()
    try:
        # We want EXACTLY these 5 courses to be active.
        target_courses = {
            "B.TECH": {"name": "B.Tech", "duration": "4 years"},
            "M.TECH": {"name": "M.Tech", "duration": "2 years"},
            "B.SC": {"name": "B.Sc", "duration": "3 years"},
            "B.A": {"name": "B.A", "duration": "3 years"},
            "B.COM": {"name": "B.Com", "duration": "3 years"},
        }
        
        # 1. Restore/Create target courses, Soft delete all others
        all_courses = db.query(Course).all()
        for c in all_courses:
            if c.code in target_courses:
                c.is_deleted = False
                c.name = target_courses[c.code]["name"]
                c.duration_years = target_courses[c.code]["duration"]
            else:
                c.is_deleted = True
                
        db.flush()

        # 2. Get the course IDs
        btech = db.query(Course).filter_by(code="B.TECH").first()
        mtech = db.query(Course).filter_by(code="M.TECH").first()
        bsc = db.query(Course).filter_by(code="B.SC").first()
        ba = db.query(Course).filter_by(code="B.A").first()
        bcom = db.query(Course).filter_by(code="B.COM").first()

        # Define EXACTLY the departments we want active.
        # Everything else under these courses will be soft-deleted.
        target_depts = {
            btech.id: [
                ("BT-CS", "B.Tech Computer Science"),
                ("BT-ME", "B.Tech Mechanical Engineering"),
                ("BT-CE", "B.Tech Civil Engineering"),
                ("BT-EE", "B.Tech Electrical Engineering"),
                ("BT-EC", "B.Tech Electronics & Comm"),
                ("BT-AS", "B.Tech Applied Sciences"),
            ],
            mtech.id: [
                ("MT-AI", "M.Tech Artificial Intelligence"),
                ("MT-DS", "M.Tech Data Science"),
                ("MT-STE", "M.Tech Structural Eng"),
                ("MT-TE", "M.Tech Thermal Engineering"),
                ("MT-VD", "M.Tech VLSI Design"),
            ],
            bsc.id: [
                ("BS-PHY", "B.Sc Physics"),
                ("BS-CHE", "B.Sc Chemistry"),
                ("BS-MAT", "B.Sc Mathematics"),
                ("BS-ZOO", "B.Sc Zoology"),
                ("BS-BOT", "B.Sc Botany"),
            ],
            ba.id: [
                ("BA-ENG", "B.A English"),
                ("BA-HIS", "B.A History"),
                ("BA-POL", "B.A Political Science"),
                ("BA-ECO", "B.A Economics"),
                ("BA-SOC", "B.A Sociology"),
            ],
            bcom.id: [
                ("BC-ACC", "B.Com Accounting"),
                ("BC-FIN", "B.Com Finance"),
                ("BC-TAX", "B.Com Taxation"),
                ("BC-BM", "B.Com Business Management"),
                ("BC-ITR", "B.Com International Trade"),
            ]
        }

        # First, ensure these departments exist and are active
        active_dept_ids = []
        applied_sci_id = None
        for cid, depts in target_depts.items():
            for code, name in depts:
                dept = db.query(Department).filter_by(code=code).first()
                if not dept:
                    dept = Department(name=name, code=code, description=f"Department of {name}", course_id=cid)
                    db.add(dept)
                    db.flush()
                else:
                    dept.is_deleted = False
                    dept.course_id = cid
                    dept.name = name
                active_dept_ids.append(dept.id)

                if code == "BT-AS":
                    applied_sci_id = dept.id

        # Soft delete all OTHER departments for the 5 courses
        all_depts = db.query(Department).filter(Department.course_id.in_([btech.id, mtech.id, bsc.id, ba.id, bcom.id])).all()
        for d in all_depts:
            if d.id not in active_dept_ids:
                d.is_deleted = True

        # Ensure Applied Sciences subjects are active
        as_subjects = [
            ("AS101", "Engineering Physics", 4, 1),
            ("AS102", "Engineering Mathematics I", 4, 1),
            ("AS103", "Engineering Chemistry", 4, 1),
            ("AS104", "Basic Electrical Engineering", 3, 2),
            ("AS105", "Engineering Mathematics II", 4, 2),
        ]
        
        for code, name, credits, sem in as_subjects:
            subj = db.query(Subject).filter_by(code=code).first()
            if not subj:
                subj = Subject(name=name, code=code, credits=credits, semester=sem, department_id=applied_sci_id)
                db.add(subj)
            else:
                subj.is_deleted = False
                subj.department_id = applied_sci_id
                
        db.commit()
        print("Successfully synchronized exactly the required courses, departments, and subjects! Soft deleted duplicates.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
