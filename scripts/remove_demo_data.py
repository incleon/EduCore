import os
import sys

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.department import Department
from app.models.subject import Subject, SubjectTeacher
from app.models.student import Student
from app.models.teacher import Teacher

def main():
    db = SessionLocal()
    try:
        print("Removing demo data...")
        
        # 1. Gather all users that were created for demo teachers and students
        # We can find them by checking emails for "@demo.edu"
        demo_users = db.query(User).filter(User.email.like('%@demo.edu')).all()
        user_ids_to_delete = [u.id for u in demo_users]
        
        print(f"Found {len(user_ids_to_delete)} demo users to delete.")
        
        # 2. Gather demo courses
        demo_courses = ["B.ARCH", "B.SC.HONS", "B.A.HONS", "M.SC", "PH.D"]
        courses = db.query(Course).filter(Course.code.in_(demo_courses)).all()
        course_ids = [c.id for c in courses]
        
        if course_ids:
            # 3. Gather departments belonging to those courses
            depts = db.query(Department).filter(Department.course_id.in_(course_ids)).all()
            dept_ids = [d.id for d in depts]
            
            if dept_ids:
                print(f"Found {len(dept_ids)} demo departments.")
                
                # Delete SubjectTeachers (association table) linked to the demo teachers
                # Find the teachers first
                demo_teachers = db.query(Teacher).filter(Teacher.department_id.in_(dept_ids)).all()
                teacher_ids = [t.id for t in demo_teachers]
                if teacher_ids:
                    db.query(SubjectTeacher).filter(SubjectTeacher.teacher_id.in_(teacher_ids)).delete(synchronize_session=False)
                    print(f"Deleted subject-teacher associations for {len(teacher_ids)} teachers.")
                
                # Delete Subjects
                deleted_subjects = db.query(Subject).filter(Subject.department_id.in_(dept_ids)).delete(synchronize_session=False)
                print(f"Deleted {deleted_subjects} subjects.")
                
                # Delete Students
                deleted_students = db.query(Student).filter(Student.department_id.in_(dept_ids)).delete(synchronize_session=False)
                print(f"Deleted {deleted_students} students.")
                
                # Delete Teachers
                deleted_teachers = db.query(Teacher).filter(Teacher.department_id.in_(dept_ids)).delete(synchronize_session=False)
                print(f"Deleted {deleted_teachers} teachers.")
                
                # Delete Departments
                deleted_depts = db.query(Department).filter(Department.course_id.in_(course_ids)).delete(synchronize_session=False)
                print(f"Deleted {deleted_depts} departments.")
                
            # Delete Courses
            deleted_courses = db.query(Course).filter(Course.code.in_(demo_courses)).delete(synchronize_session=False)
            print(f"Deleted {deleted_courses} courses.")

        # Delete Users
        if user_ids_to_delete:
            db.query(UserRole).filter(UserRole.user_id.in_(user_ids_to_delete)).delete(synchronize_session=False)
            deleted_users = db.query(User).filter(User.id.in_(user_ids_to_delete)).delete(synchronize_session=False)
            print(f"Deleted {deleted_users} users and their roles.")
            
        db.commit()
        print("Demo data successfully removed.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
