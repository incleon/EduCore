# Sidebar visibility by role

In the EduCore CMS, sidebar links and entities are dynamically rendered based on the specific **permissions** and **roles** assigned to a user. This ensures that users only see the features and tools relevant to their responsibilities.

Here is a detailed breakdown of which sidebar entities are visible to each major role in the system:

---

## 📌 Always Visible (To all logged-in users)
Because these are core features, the following links appear for **all** roles (Admin, HOD, Teacher, Student, Accountant, Librarian):
- **Overview (Dashboard)** 
- **Timetable**
- **Profile (Account Menu)**

---

## 👑 1. Administrator
The Admin role has unrestricted access and all permissions. They are the only role that sees everything.
- **People:** Students, Faculty, HOD Management
- **Academics:** Departments, Courses, Branches, Curricula, Curriculum versions, Semesters, Sections, Subjects
- **Learning:** Curriculum subjects, Elective groups, Faculty assignments, Attendance, Marks, Assignments
- **Operations:** Fees, Library

---

## 🏛️ 2. Head of Department (HOD)
HODs manage students and academics for their department but do not manage system-wide faculty or operations.
- **Special:** **HOD Panel** (Visible because `user.is_hod` is true)
- **People:** Students (`view_students`)
- **Academics:** Branches, Curricula, Curriculum versions, Semesters, Sections, Subjects (`view_academic_structure`, `view_subjects`)
- **Learning:** Curriculum subjects, Elective groups, Faculty assignments, Attendance, Marks, Assignments (`view_attendance`, `view_marks`)
- **Operations:** *None*

---

## 👨‍🏫 3. Teacher
Teachers focus on student learning, attendance, marks, and library resources.
- **People:** Students (`view_students`)
- **Academics:** Branches, Curricula, Curriculum versions, Semesters, Sections, Subjects (`view_academic_structure`, `view_subjects`)
- **Learning:** Curriculum subjects, Elective groups, Faculty assignments, Attendance, Marks, Assignments (`view_attendance`, `view_marks`)
- **Operations:** Library (`view_library`)

---

## 🎓 4. Student
Students need access to their learning materials, attendance, grades, and operational dues (fees/library).
- **People:** *None* 
- **Academics:** *Hidden from sidebar* — Student's own enrollment details (Department, Course, Branch, Curriculum version, Semester, Section) are displayed in the **Dashboard Overview** card instead.
- **Learning:** Curriculum subjects, Elective groups, Faculty assignments, Attendance, Marks, Assignments (`view_attendance`, `view_marks`)
- **Operations:** Fees, Library (`view_fees`, `view_library`)

---

## 💰 5. Accountant
Accountants handle financials and need to view student records to cross-reference fee payments.
- **People:** Students (`view_students`)
- **Academics:** Branches, Curricula, Curriculum versions, Semesters, Sections (`view_academic_structure`)
- **Learning:** Curriculum subjects, Elective groups, Faculty assignments, Assignments
- **Operations:** Fees (`view_fees`)

---

## 📚 6. Librarian
Librarians handle book inventory and issues, requiring access to student directories.
- **People:** Students (`view_students`)
- **Academics:** Branches, Curricula, Curriculum versions, Semesters, Sections (`view_academic_structure`)
- **Learning:** Curriculum subjects, Elective groups, Faculty assignments, Assignments
- **Operations:** Library (`view_library`)

---

### 🔍 How it works under the hood:
The frontend `AppShell.jsx` builds the sidebar by filtering the `resourceConfigs` array using the `can(permission)` function. For example:
- **HOD Management** checks for `manage_academic_structure` (Only Admin has this).
- **Faculty** checks for `manage_teachers` (Only Admin has this).
- **Departments & Courses** check for `view_departments` (Only Admin has this).
- Any link requiring `view_academic_structure` appears for almost everyone, as all core roles possess this read permission to understand their curriculum constraints.
