# 🎓 EduCore CMS
**Enterprise-Grade College Management System**

EduCore is a robust, modular, and highly scalable College Management System built with **FastAPI**, **SQLAlchemy**, and **Jinja2**. It digitizes and centralizes academic, administrative, and financial workflows into a single, intuitive platform.

---

## ✨ Core Modules & Features

### 🔐 1. Advanced Role-Based Access Control (RBAC)
EduCore uses a highly granular permission system rather than simple role checks.
- **Roles:** Admin, HOD, Teacher, Student, System Admin
- **Dynamic Permissions:** Every action (e.g., `manage_fees`, `view_attendance`) is checked securely via middleware.
- **Hierarchical Access:** HODs can only manage their specific department's data; Teachers only see their assigned subjects; Students only view their personal records.

### 📚 2. Academics Management
- **Hierarchical Structure:** Courses ➔ Departments ➔ Subjects.
- **Subject Allocation:** Assign specific subjects to teachers dynamically.
- **Semester Tracking:** All academic data is tightly bound to semester schedules.

### 📅 3. Interactive Timetable System
- **Grid-Based UI:** Completely interactive, visually structured weekly schedule.
- **Free Periods:** Seamlessly configure non-instructional blocks.
- **Approval Workflow:** HODs draft timetables and submit them. Admins must explicitly approve them before they go live.
- **Version Control:** Edits to approved timetables track draft vs approved states.
- **PDF Export:** Responsive, landscape PDF downloads for students and teachers.

### 🏫 4. Enterprise Library Dashboard
- **Real-Time Metrics:** Live statistics of total inventory, available copies, and active/overdue issues.
- **Dual-Pane Interface:** Split views for Book Catalog and Active Book Issues.
- **Integrated Modals:** Add new books, issue books to student IDs, and process returns (with late fee calculations) all within a single page without reloading.
- **Student View:** Students only see the public catalog and books strictly issued to them.

### 💰 5. Fees & Financials
- **Fee Configuration:** Define fee structures for specific courses, departments, and semesters.
- **Payment Processing:** Record partial or full payments, generate receipt numbers, and track cash/online transactions.
- **Status Tracking:** Automatically tags students as `Paid`, `Partial`, or `Pending/Overdue`.

### 📊 6. Marks & Attendance
- **Attendance:** Date-based bulk attendance marking for classes.
- **Marks:** Uploading exam scores bound to specific subjects and semesters.
- **Analytics:** Teacher dashboards showing class performance and attendance averages.

---

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| **Backend Framework** | FastAPI (Python) |
| **Templating Engine** | Jinja2 |
| **Database ORM** | SQLAlchemy |
| **Database System** | SQLite (Production ready via MySQL Migration scripts) |
| **Frontend Styling** | Bootstrap 5, Bootstrap Icons, Custom CSS |
| **Typography** | Google Fonts (DM Sans) |

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone <repository_url>
cd CMS
pip install -r requirements.txt
```

### 3. Running the Server
Start the FastAPI server via Uvicorn (configured in the run script):
```bash
python run.py
```

The application will be accessible at: `http://localhost:8000`

---

## 📁 Repository Structure
To keep the root folder clean, administrative and utility files have been organized into subdirectories.
- `app/`: The core FastAPI application (models, routers, templates, services, database).
- `scripts/`: Development utility scripts (Data generation, DB migrations, mass-string replacements).
- `docs/`: Historical documentation (Migration guides, Refactoring summaries).
- `logs/`: Application audit logs.
- `uploads/`: Media and file upload directory.

---

*Powered by EduCore — Streamlining academic administration.*
