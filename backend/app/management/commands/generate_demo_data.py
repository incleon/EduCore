import os
import sys

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.user import User, Role, UserRole
from app.models.course import Course
from app.models.department import Department
from app.models.subject import Subject, SubjectTeacher
from app.models.student import Student
from app.models.teacher import Teacher
from app.core.security import PasswordHasher
import random

def main():
    db = SessionLocal()
    try:
        # Ensure we have roles loaded
        role_map = {r.name: r.id for r in db.query(Role).all()}
        if not role_map:
            print("Database not seeded with roles. Please run the main app seeder first.")
            return

        demo_password = PasswordHasher.hash_password("admin123")
        print("Starting seeding process...")

        # Create 5 Courses
        courses_data = [
            ("Bachelor of Architecture", "B.ARCH", "5 years"),
            ("Bachelor of Science", "B.SC.HONS", "3 years"),
            ("Bachelor of Arts", "B.A.HONS", "3 years"),
            ("Master of Science", "M.SC", "2 years"),
            ("Doctor of Philosophy", "PH.D", "3 years")
        ]

        created_courses = []
        for name, code, duration in courses_data:
            c = db.query(Course).filter_by(code=code).first()
            if not c:
                c = Course(name=name, code=code, duration_years=duration)
                db.add(c)
                db.commit()
            created_courses.append(c)

        print(f"Ensured {len(created_courses)} custom courses.")

        # For each course, create 5 departments
        dept_names = [
            "Information Technology", "Chemical Engineering", "Civil Engineering", 
            "Aerospace", "Biotechnology", "Data Science", "Cyber Security", 
            "Architecture", "Urban Planning", "Interior Design", "Psychology", 
            "Sociology", "Literature", "History", "Economics"
        ]

        all_depts = []
        dept_counter = 1
        for course in created_courses:
            for i in range(5):
                d_name = f"{random.choice(dept_names)} {course.code.replace('.', '')} {i+1}"
                d_code = f"D-{course.code.replace('.', '')}-{i+1}"
                d = db.query(Department).filter_by(code=d_code).first()
                if not d:
                    d = Department(name=d_name, code=d_code, course_id=course.id)
                    db.add(d)
                    db.commit()
                all_depts.append(d)
                dept_counter += 1

        print(f"Ensured {len(all_depts)} departments.")

        # Track totals for summary
        total_teachers = 0
        total_subjects = 0
        total_students = 0

        # Create teachers, subjects, students
        # Use large offsets for counters to prevent unique constraint clashes with existing seed data
        teacher_counter = 500
        student_counter = 5000
        subject_counter = 1000

        for dept in all_depts:
            # 5 Teachers per department
            dept_teachers = []
            for i in range(5):
                emp_id = f"T-DEMO-{teacher_counter:04d}"
                t = db.query(Teacher).filter_by(employee_id=emp_id).first()
                if not t:
                    email = f"teacher{teacher_counter}@demo.edu"
                    # Check if user email exists
                    if not db.query(User).filter_by(email=email).first():
                        u = User(
                            email=email, 
                            username=f"tdemo{teacher_counter}", 
                            hashed_password=demo_password, 
                            full_name=f"Prof. Demo {teacher_counter}"
                        )
                        db.add(u)
                        db.flush()
                        db.add(UserRole(user_id=u.id, role_id=role_map["teacher"]))
                        
                        t = Teacher(user_id=u.id, department_id=dept.id, employee_id=emp_id, designation="Professor")
                        db.add(t)
                        db.commit()
                        total_teachers += 1
                
                if t:
                    dept_teachers.append(t)
                teacher_counter += 1
                
            # For each department, semester wise subjects and students (semesters 1 to 4)
            for sem in [1, 2, 3, 4]:
                # 5 Subjects per semester
                for i in range(5):
                    s_code = f"SUBJ-{subject_counter:04d}"
                    s = db.query(Subject).filter_by(code=s_code).first()
                    if not s:
                        s = Subject(name=f"Advanced Topic {subject_counter}", code=s_code, credits=3, semester=sem, department_id=dept.id)
                        
                        # Assign to a random teacher in this dept
                        if dept_teachers:
                            assigned_teacher = random.choice(dept_teachers)
                            s.teacher_id = assigned_teacher.id
                            db.add(s)
                            db.flush()
                            
                            st = SubjectTeacher(subject_id=s.id, teacher_id=assigned_teacher.id, section="A")
                            db.add(st)
                        else:
                            db.add(s)
                            
                        db.commit()
                        total_subjects += 1
                    subject_counter += 1
                    
                # 5 Students per semester
                for i in range(5):
                    enr_no = f"ENR-DEMO-{student_counter:05d}"
                    stu = db.query(Student).filter_by(enrollment_number=enr_no).first()
                    if not stu:
                        email = f"student{student_counter}@demo.edu"
                        if not db.query(User).filter_by(email=email).first():
                            u = User(
                                email=email, 
                                username=f"sdemo{student_counter}", 
                                hashed_password=demo_password, 
                                full_name=f"Student Demo {student_counter}"
                            )
                            db.add(u)
                            db.flush()
                            db.add(UserRole(user_id=u.id, role_id=role_map["student"]))
                            
                            stu = Student(user_id=u.id, department_id=dept.id, enrollment_number=enr_no, semester=sem, section="A")
                            db.add(stu)
                            db.commit()
                            total_students += 1
                    student_counter += 1

        print("--- SEEDING COMPLETE ---")
        print(f"Courses Created: {len(created_courses)}")
        print(f"Departments Created: {len(all_depts)}")
        print(f"Teachers Created: {total_teachers}")
        print(f"Subjects Created: {total_subjects}")
        print(f"Students Created: {total_students}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
