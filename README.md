# 🎓 EduCore CMS
**Enterprise-Grade College Management System**

EduCore is a robust, modular, and highly scalable College Management System built with **FastAPI**, **SQLAlchemy**, and **Jinja2**. It digitizes and centralizes academic, administrative, and financial workflows into a single, intuitive platform.

---

## ✨ Core Modules & Features

### 🔐 1. Advanced Role-Based Access Control (RBAC) & Dashboards
EduCore uses a highly granular permission system rather than simple role checks, with dynamic, role-specific dashboards built using the **Factory Pattern**.
- **Roles:** Admin, HOD, Teacher, Student, Accountant, Librarian.
- **Dynamic Dashboards:** The system evaluates the user's highest role hierarchically and serves specialized, metric-rich dashboards tailored to their responsibilities.
- **HOD Sandboxing:** HODs are strictly sandboxed to their own department. They manage only their department's students, teachers, subjects, and timetables without global visibility.

### 🏛️ 2. Enterprise Architecture & OOP Principles
The codebase is structured for enterprise scalability using advanced Object-Oriented Programming (OOP) concepts and Design Patterns:
- **Service Layer & Repository Pattern:** Decouples business logic from database operations, ensuring modularity and easier testing.
- **Factory Pattern:** Dynamically provisions role-specific UI components and dashboards.
- **Observer Pattern:** Implements an asynchronous event dispatcher for system events (e.g., triggering email notifications upon student admission or fee payment).
- **Strategy Pattern:** Dynamically applies different fee calculation algorithms (Standard, Late Penalty, Scholarship).

### 📧 3. Automated Email Integration
- **Institutional Identity:** Automatically generates structured institutional emails (`firstname.studentid@cms.edu`) and secure random passwords for new students and faculty.
- **Event-Driven Notifications:** Asynchronously dispatches onboarding emails and fee payment receipts to personal email addresses without blocking the main application thread.

### 📚 4. Academics & Timetable Management
- **Hierarchical Structure:** Courses ➔ Departments ➔ Subjects.
- **Interactive Timetables:** Grid-based, visually structured weekly schedules with drafted vs. approved version control.
- **PDF Exports:** Generate responsive, landscape PDF downloads for student and teacher schedules.

### 🏫 5. Comprehensive Library & Financial Systems
- **Library Dashboard:** Live statistics of inventory, active issues, and overdue returns. Modals for rapid, single-page book management and issuance.
- **Fee Management:** Flexible fee structures, partial/full payment tracking, and automated receipt generation.

---

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| **Backend Framework** | FastAPI (Python) |
| **Templating Engine** | Jinja2 |
| **Database ORM** | SQLAlchemy |
| **Database System** | SQLite (Production ready via PostgreSQL/MySQL Migration scripts) |
| **Frontend Styling** | Vanilla CSS, Bootstrap 5, Bootstrap Icons |
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

### 3. Environment Configuration
Create a `.env` file in the root directory (use `.env.example` as a template) and configure your database and email SMTP settings.

### 4. Database Initialization
Seed the database with initial academic structures, roles, permissions, and 100+ realistic faculty records:
```bash
python app/database/seed.py
```

### 5. Running the Server
Start the FastAPI server via Uvicorn:
```bash
python run.py
```
The application will be accessible at: `http://localhost:8000`

---

## 📁 Repository Structure
To keep the root folder clean, administrative and utility files have been organized into subdirectories.
- `app/`: The core FastAPI application (models, routers, templates, services, database, core architecture).
- `scripts/`: Development utility scripts (Data generation, DB migrations, file organizers).
- `docs/`: Historical documentation and deployment plans.
- `logs/`: Application audit logs.
- `uploads/`: Media and file upload directory.

---

*Powered by EduCore — Streamlining academic administration through enterprise-grade software design.*
