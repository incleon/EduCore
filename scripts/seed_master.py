import sys
import os
import random
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.department import Department
from app.models.course import Course
from app.models.subject import Subject
from app.models.user import User, Role, UserRole
from app.models.student import Student, EnrollmentStatus
from app.models.teacher import Teacher
from app.core.security import PasswordHasher

def get_or_create_course(db, code, name, description, duration):
    course = db.query(Course).filter_by(code=code).first()
    if not course:
        course = Course(name=name, code=code, description=description, duration_years=duration)
        db.add(course)
        db.flush()
        print(f"[+] Created Course: {name} ({code})")
    else:
        print(f"[*] Course {name} ({code}) already exists.")
    return course

def get_or_create_department(db, code, name, course_id):
    dept = db.query(Department).filter((Department.code == code) | (Department.name == name)).first()
    if not dept:
        dept = Department(name=name, code=code, description=f"Department of {name}", course_id=course_id)
        db.add(dept)
        db.flush()
        print(f"  [+] Created Department: {name} ({code})")
    else:
        print(f"  [*] Department {name} ({code}) already exists.")
    return dept

def get_or_create_subject(db, code, name, credits, sem, dept_id):
    subj = db.query(Subject).filter_by(code=code).first()
    if not subj:
        subj = Subject(name=name, code=code, credits=credits, semester=sem, department_id=dept_id)
        db.add(subj)
        db.flush()
        print(f"    [+] Created Subject: {name} ({code}) under Dept ID {dept_id}")
    else:
        print(f"    [*] Subject {name} ({code}) already exists.")
    return subj

def seed_courses_and_departments(db):
    print("--- Seeding 5 Courses and their 5 Real Departments ---")
    
    # We prefix department names with Course Name to absolutely guarantee they are uniquely seeded
    # and not skipped due to global name uniqueness constraints.

    # 1. B.Tech
    btech = get_or_create_course(db, "B.TECH", "B.Tech", "Bachelor of Technology", "4 years")
    print("\nSeeding Departments for B.Tech...")
    get_or_create_department(db, "BT-CS", "B.Tech Computer Science", btech.id)
    get_or_create_department(db, "BT-ME", "B.Tech Mechanical Engineering", btech.id)
    get_or_create_department(db, "BT-CE", "B.Tech Civil Engineering", btech.id)
    get_or_create_department(db, "BT-EE", "B.Tech Electrical Engineering", btech.id)
    get_or_create_department(db, "BT-EC", "B.Tech Electronics & Comm", btech.id)
    
    # Additional Applied Sciences department for 1st year B.Tech
    applied_sci = get_or_create_department(db, "BT-AS", "B.Tech Applied Sciences", btech.id)
    
    # Seeding entities (subjects) for Applied Sciences that are taught in 1st year
    print("\nSeeding 1st Year Applied Sciences Subjects (taught to all B.Tech branches)...")
    get_or_create_subject(db, "AS101", "Engineering Physics", 4, 1, applied_sci.id)
    get_or_create_subject(db, "AS102", "Engineering Mathematics I", 4, 1, applied_sci.id)
    get_or_create_subject(db, "AS103", "Engineering Chemistry", 4, 1, applied_sci.id)
    get_or_create_subject(db, "AS104", "Basic Electrical Engineering", 3, 2, applied_sci.id)
    get_or_create_subject(db, "AS105", "Engineering Mathematics II", 4, 2, applied_sci.id)

    # 2. M.Tech
    mtech = get_or_create_course(db, "M.TECH", "M.Tech", "Master of Technology", "2 years")
    print("\nSeeding Departments for M.Tech...")
    get_or_create_department(db, "MT-AI", "M.Tech Artificial Intelligence", mtech.id)
    get_or_create_department(db, "MT-DS", "M.Tech Data Science", mtech.id)
    get_or_create_department(db, "MT-STE", "M.Tech Structural Eng", mtech.id)
    get_or_create_department(db, "MT-TE", "M.Tech Thermal Engineering", mtech.id)
    get_or_create_department(db, "MT-VD", "M.Tech VLSI Design", mtech.id)

    # 3. B.Sc
    bsc = get_or_create_course(db, "B.SC", "B.Sc", "Bachelor of Science", "3 years")
    print("\nSeeding Departments for B.Sc...")
    get_or_create_department(db, "BS-PHY", "B.Sc Physics", bsc.id)
    get_or_create_department(db, "BS-CHE", "B.Sc Chemistry", bsc.id)
    get_or_create_department(db, "BS-MAT", "B.Sc Mathematics", bsc.id)
    get_or_create_department(db, "BS-ZOO", "B.Sc Zoology", bsc.id)
    get_or_create_department(db, "BS-BOT", "B.Sc Botany", bsc.id)

    # 4. B.A
    ba = get_or_create_course(db, "B.A", "B.A", "Bachelor of Arts", "3 years")
    print("\nSeeding Departments for B.A...")
    get_or_create_department(db, "BA-ENG", "B.A English", ba.id)
    get_or_create_department(db, "BA-HIS", "B.A History", ba.id)
    get_or_create_department(db, "BA-POL", "B.A Political Science", ba.id)
    get_or_create_department(db, "BA-ECO", "B.A Economics", ba.id)
    get_or_create_department(db, "BA-SOC", "B.A Sociology", ba.id)

    # 5. B.Com
    bcom = get_or_create_course(db, "B.COM", "B.Com", "Bachelor of Commerce", "3 years")
    print("\nSeeding Departments for B.Com...")
    get_or_create_department(db, "BC-ACC", "B.Com Accounting", bcom.id)
    get_or_create_department(db, "BC-FIN", "B.Com Finance", bcom.id)
    get_or_create_department(db, "BC-TAX", "B.Com Taxation", bcom.id)
    get_or_create_department(db, "BC-BM", "B.Com Business Management", bcom.id)
    get_or_create_department(db, "BC-ITR", "B.Com International Trade", bcom.id)

def seed_teachers(db):
    first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Shaurya", "Atharva", "Kabir", "Rishi", "Saanvi", "Aanya", "Aadhya", "Aaradhya", "Ananya", "Pari", "Diya", "Nandini", "Ishita", "Meera", "Neha", "Riya", "Kavya", "Swati", "Pooja", "Sneha", "Amit", "Rahul", "Vikram", "Suresh", "Ramesh", "Anil", "Sunil", "Rajesh", "Prakash", "Sanjay", "Vijay", "Ajay", "Ashok", "Sanjeev", "Manoj", "Ravi", "Kiran", "Deepak", "Tarun", "Naveen", "Praveen", "Ashish", "Gaurav", "Saurabh", "Manish", "Priya", "Priyanka", "Anjali", "Rachna", "Shruti", "Sweta", "Sonal", "Shikha"]
    last_names = ["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Desai", "Joshi", "Chauhan", "Rajput", "Rao", "Das", "Mukherjee", "Banerjee", "Bose", "Nair", "Menon", "Pillai", "Reddy", "Iyer", "Yadav", "Tiwari", "Mishra", "Pandey", "Shukla", "Dubey", "Srivastava", "Tripathi", "Thakur", "Jain", "Agarwal", "Garg", "Bansal", "Mehta", "Shah", "Kapadia", "Patil", "Deshmukh", "Kadam", "Chavan", "Bhatt", "Bhattacharya", "Chowdhury", "Dutta", "Ghosh", "Khatri", "Kaur"]
    
    combinations = [f"{f} {l}" for f in first_names for l in last_names]
    random.shuffle(combinations)
    
    role = db.query(Role).filter_by(name="teacher").first()
    if not role:
        print("Teacher role not found. Please seed basic roles first.")
        return

    departments = db.query(Department).all()
    print(f"Adding 10 teachers to each of {len(departments)} departments...")
    
    password = PasswordHasher.hash_password("password123")
    
    name_idx = 0
    
    for dept in departments:
        for i in range(10):
            if name_idx >= len(combinations):
                name_idx = 0
            
            full_name = combinations[name_idx]
            name_idx += 1
            
            base_username = full_name.lower().replace(" ", ".")
            username = f"{base_username}.{dept.code.lower()}.{i}"
            email = f"{username}@cms.edu"
            
            user = db.query(User).filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    username=username,
                    hashed_password=password,
                    full_name=f"Prof. {full_name}"
                )
                db.add(user)
                db.flush()
                
                user_role = UserRole(user_id=user.id, role_id=role.id)
                db.add(user_role)
                db.flush()
                
                emp_id = f"EMP-{dept.code}-{random.randint(1000, 9999)}-{i}"
                fac_id = f"FAC-{dept.code}-{random.randint(1000, 9999)}-{i}"
                
                teacher = Teacher(
                    user_id=user.id,
                    department_id=dept.id,
                    employee_id=emp_id,
                    faculty_id=fac_id,
                    designation=random.choice(["Assistant Professor", "Associate Professor", "Professor", "Lecturer"]),
                    specialization=f"Specialization in {dept.name}",
                    qualification=random.choice(["Ph.D.", "M.Tech", "M.Sc", "M.A", "MBA"]),
                    joining_date=datetime.date(random.randint(2010, 2023), random.randint(1, 12), random.randint(1, 28)),
                    experience_years=random.randint(1, 20)
                )
                db.add(teacher)
        db.commit()
    print("Successfully added 10 teachers to each department!")


def seed_students(db):
    print("--- Seeding 50 Students per Department per Year (Odd Semesters) ---")
    
    first_names = [
        "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", 
        "Shaurya", "Atharva", "Kabir", "Rishi", "Saanvi", "Aanya", "Aadhya", "Aaradhya", "Ananya", "Pari", 
        "Diya", "Nandini", "Ishita", "Meera", "Neha", "Riya", "Kavya", "Swati", "Pooja", "Sneha", 
        "Amit", "Rahul", "Vikram", "Suresh", "Ramesh", "Anil", "Sunil", "Rajesh", "Prakash", "Sanjay", 
        "Vijay", "Ajay", "Ashok", "Sanjeev", "Manoj", "Ravi", "Kiran", "Deepak", "Tarun", "Naveen", 
        "Praveen", "Ashish", "Gaurav", "Saurabh", "Manish", "Priya", "Priyanka", "Anjali", "Rachna", "Shruti", 
        "Sweta", "Sonal", "Shikha", "Arnav", "Dhruv", "Rohan", "Mohit", "Yash", "Kartik", "Ayush", 
        "Nikhil", "Gautam", "Varun", "Abhinav", "Harsh", "Pranav", "Sameer", "Nitin", "Prateek", "Rishabh",
        "Tanvi", "Nisha", "Mansi", "Ritika", "Akanksha", "Saloni", "Vanshika", "Simran", "Muskan", "Roshni",
        "Kritika", "Priyadarshini", "Sakshi", "Pallavi", "Shreya", "Nidhi", "Poonam", "Meenakshi", "Radhika", "Geeta"
    ]
    last_names = [
        "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Desai", "Joshi", "Chauhan", "Rajput", 
        "Rao", "Das", "Mukherjee", "Banerjee", "Bose", "Nair", "Menon", "Pillai", "Reddy", "Iyer", 
        "Yadav", "Tiwari", "Mishra", "Pandey", "Shukla", "Dubey", "Srivastava", "Tripathi", "Thakur", "Jain", 
        "Agarwal", "Garg", "Bansal", "Mehta", "Shah", "Kapadia", "Patil", "Deshmukh", "Kadam", "Chavan", 
        "Bhatt", "Bhattacharya", "Chowdhury", "Dutta", "Ghosh", "Khatri", "Kaur", "Ahluwalia", "Anand", "Ahuja",
        "Bhatia", "Chopra", "Dhawan", "Grover", "Kapoor", "Khanna", "Khurana", "Lamba", "Malhotra", "Narang",
        "Oberoi", "Sethi", "Suri", "Tandon", "Wadhwa", "Arora", "Bedi", "Chawla", "Dhingra", "Gandi", "Goswami",
        "Kohli", "Madan", "Nanda", "Puri", "Sarin", "Sood", "Talwar", "Walia", "Appa", "Babu", "Chary", "Dasari",
        "Gowda", "Hegde", "Jha", "Kamat", "Lal", "Mallick", "Nath", "Prasad", "Rajan", "Sahu", "Tiwary", "Varma"
    ]
    
    combinations = [f"{f} {l}" for f in first_names for l in last_names]
    random.shuffle(combinations)
    
    role = db.query(Role).filter_by(name="student").first()
    if not role:
        print("Student role not found. Please seed basic roles first.")
        return

    departments = db.query(Department).all()
    print(f"Adding 50 students per year to each of {len(departments)} departments...")
    
    password = PasswordHasher.hash_password("student123")
    
    name_idx = 0
    
    for dept in departments:
        course = db.query(Course).filter_by(id=dept.course_id).first()
        duration_years_str = course.duration_years if course and course.duration_years else "3 years"
        try:
            duration_years = int(duration_years_str.split()[0])
        except Exception:
            duration_years = 3
            
        for year in range(1, duration_years + 1):
            semester = year * 2 - 1
            
            current_year = 2026
            admission_year = current_year - year + 1
            admission_year_short = str(admission_year)[-2:]
            
            branch_code = dept.code.replace('-', '').upper()
            
            student_seq = 1
            for i in range(50):
                if name_idx >= len(combinations):
                    name_idx = 0
                
                full_name = combinations[name_idx]
                name_idx += 1
                
                student_id = f"{admission_year_short}{branch_code}{str(student_seq).zfill(3)}"
                enrollment_number = f"EN{student_id}"
                
                base_username = full_name.lower().replace(" ", ".")
                username = f"{base_username}.{student_id.lower()}"
                email = f"{username}@student.cms.edu"
                
                user = db.query(User).filter_by(email=email).first()
                if not user:
                    user = User(
                        email=email,
                        username=username,
                        hashed_password=password,
                        full_name=full_name
                    )
                    db.add(user)
                    db.flush()
                    
                    user_role = UserRole(user_id=user.id, role_id=role.id)
                    db.add(user_role)
                    db.flush()
                    
                    student = Student(
                        user_id=user.id,
                        department_id=dept.id,
                        student_id=student_id,
                        enrollment_number=enrollment_number,
                        admission_date=datetime.date(admission_year, 8, random.randint(1, 30)),
                        semester=semester,
                        section=random.choice(["A", "B", "C"]),
                        guardian_name=f"Mr. {full_name.split()[-1]}",
                        guardian_phone=f"98{random.randint(10000000, 99999999)}",
                        blood_group=random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]),
                        status=EnrollmentStatus.ACTIVE
                    )
                    db.add(student)
                    student_seq += 1
        db.commit()
    print("Successfully added students to all departments!")


def main():
    db = SessionLocal()
    try:
        seed_courses_and_departments(db)
        seed_teachers(db)
        seed_students(db)
        
        db.commit()
        print("\nAll seeding completed successfully and explicitly committed!")
    except Exception as e:
        print(f"\nError occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
