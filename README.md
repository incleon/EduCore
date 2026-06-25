<p align="center">
  <img src="frontend/public/institute.png" alt="EduCore institute mark" width="110" />
</p>

<h1 align="center">EduCore CMS</h1>

<p align="center">
  A full-stack, role-based college management system for academic structure, people, learning, finance, library, reporting, and timetable workflows.
</p>

<p align="center">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=111" />
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00" />
  <img alt="MySQL" src="https://img.shields.io/badge/MySQL-8%2B-4479A1?logo=mysql&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img alt="Node" src="https://img.shields.io/badge/Node.js-20%2B-339933?logo=node.js&logoColor=white" />
</p>

---

## Table of contents

- [Overview](#overview)
- [Feature set](#feature-set)
- [Roles and access control](#roles-and-access-control)
- [Academic architecture](#academic-architecture)
- [Student credentials and sequence rules](#student-credentials-and-sequence-rules)
- [Technology stack](#technology-stack)
- [Application architecture](#application-architecture)
- [Repository structure](#repository-structure)
- [Database entities](#database-entities)
- [API map](#api-map)
- [Prerequisites](#prerequisites)
- [Local installation](#local-installation)
- [Database initialization and migration](#database-initialization-and-migration)
- [Move the local database to a server](#move-the-local-database-to-a-server)
- [Running the application](#running-the-application)
- [System data, demo seeding, and cleanup](#system-data-demo-seeding-and-cleanup)
- [Environment variables](#environment-variables)
- [Quality checks](#quality-checks)
- [Docker deployment](#docker-deployment)
- [Production deployment](#production-deployment)
- [Security notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Additional documentation](#additional-documentation)

## Executive Overview

EduCore CMS is a comprehensive, enterprise-grade Educational Resource Planning (ERP) and College Management System. Powered by a high-performance FastAPI backend and a dynamic React frontend, EduCore centralizes complex academic administration, financial operations, and learning management into a single, cohesive platform. It is engineered with strict, role-based access controls to ensure institutional data integrity and security.

**Key Capabilities:**

- **Scalable Architecture:** Designed for universities, multi-program institutes, and colleges with complex organizational hierarchies.
- **Intelligent Academic Core:** Manages versioned curricula, dynamic subject classifications, and strict admission-batch locking.
- **Proactive Analytics & Dashboards:** Actionable, role-specific command centers equipped with smart alerts and visual metrics to drive informed decision-making.
- **Comprehensive Workflow Automation:** Automates student enrollment, fee tracking, faculty assignments, attendance, and library circulation.
- **Enterprise Security & Persistence:** Leverages robust MySQL/MariaDB persistence, Alembic versioned schema migrations, and JWT-based authorization.
- **Flexible Deployment:** Supports native environments, Docker Compose containerization, and scaled production deployments.

## Feature set

### Identity, authentication, and authorization

- HTTP-only JWT cookie authentication.
- CAPTCHA-protected login.
- Logout and password-change workflows.
- Permission-based backend authorization and frontend navigation.
- Bootstrap administrator configuration through environment variables.
- Role-aware dashboard and profile responses.
- Audit middleware for request activity.
- In-app notifications with mark-all-read support.

### Students

- Student admission with generated institutional identity.
- Durable student IDs scoped by admission year, course, and branch.
- Personal and institutional email information.
- Department, course, branch, curriculum version, semester, and section mapping.
- Date of birth, admission date, guardian, parent, blood-group, and status information.
- Active, graduated, suspended, and dropped enrollment states.
- Complete read-only profile view containing all non-sensitive admission details.
- Curriculum-driven subject resolution and elective selection.
- Search, hierarchy filters, editing, permanent deletion, CSV export, and pagination.

### Faculty and HOD

- Faculty account and profile creation.
- Generated faculty IDs and employee IDs.
- Department and branch specialization.
- Designation, qualification, joining date, experience, specialization, and biography.
- HOD assignment to a department with role synchronization.
- Faculty-to-curriculum-subject assignment by academic year and optional section.
- Full faculty profile view.

### Academic hierarchy

- Departments as top-level academic owners.
- Courses/programs owned by departments.
- Optional branches or specializations within courses.
- Stable curriculum identities with versioned regulations.
- Admission-batch ranges and active/published curriculum versions.
- Semester credit boundaries.
- Course, branch, semester, curriculum-version, and academic-year-specific sections.
- Hierarchy filters and dependent dropdowns that clear invalid child selections.

### Subjects and curriculum

- One reusable global subject catalogue.
- Subject ownership by department.
- Controlled subject classifications:
  - `COMMON`
  - `SPECIALIZATION`
  - `ELECTIVE`
  - `OPEN_ELECTIVE`
  - `LAB`
  - `PROJECT`
  - `INTERNSHIP`
- Curriculum-subject mapping without copying common subjects between branches.
- Branch-restricted specialization subjects.
- Elective groups with minimum and maximum selection limits.
- Student elective selections.
- Automatic subject resolution from a student's locked curriculum version.

### Attendance and marks

- Daily attendance by student and subject.
- Present, absent, late, and excused states.
- Optional section and faculty-assignment context.
- Bulk attendance marking.
- Student attendance statistics.
- Midterm, final, quiz, assignment, practical, and internal marks.
- Maximum-mark validation and semester-level results.
- Department, course, branch, student, and subject filtering.

### Assignments

- Faculty assignments scoped to an approved teaching allocation and section.
- Automatic pending-submission creation for students in the target section.
- Student text/link submission with submission timestamps.
- Faculty accept/reject review with feedback.
- Teacher-owned assignment editing and deletion.
- Dedicated `manage_assignments` permission for faculty and administrators.

### Fees and payments

- Tuition, examination, library, laboratory, hostel, transport, and other fee types.
- Pending, paid, partial, overdue, and waived states.
- Due dates, payment dates, receipt numbers, payment methods, and remarks.
- Partial and full payment recording.
- Strategy-based fee handling for standard, late-penalty, and scholarship cases.
- Pending-fee reporting and role-specific access.

### Library

- Book catalogue with title, author, ISBN, publisher, edition, category, copies, shelf location, and description.
- Available, issued, reserved, lost, and damaged book states.
- Student book issue and return workflows.
- Due dates, overdue/lost states, fines, and remarks.
- Inventory search and availability tracking.

### Timetables

- Timetable versions scoped by course, department, optional branch, semester, and optional section.
- Weekly day/slot grid.
- Subject and faculty placement.
- Draft, submitted, and approved workflow support.
- Submission and approval ownership.
- Section-scoped timetable uniqueness.

### Interface, Analytics, and Reporting

- **Responsive React SPA:** Modern, high-performance single-page application using Vite.
- **Role-Based Command Centers:** Interactive, Bento-box style dashboards tailored for Administrators, HODs, Faculty, Students, Accountants, and Librarians.
- **Proactive Smart Alerts:** System-generated alerts for low attendance, pending fee ratios, at-risk students, and inventory thresholds to drive proactive administrative action.
- **Advanced Visualizations:** Integrated Recharts for enrollment funnels, financial breakdowns, and faculty workload distributions.
- **Permission-Aware Navigation:** Secure, dynamically rendered sidebars and protected routes based on granular JWT entitlements.
- **Comprehensive Data Grids:** Advanced search, hierarchical filtering, status badges, and pagination for large-scale institutional data.
- **Data Export & Reporting:** PDF and CSV generation capabilities for audits and compliance reporting.

## Enterprise Roles and Access Control

EduCore implements a granular, zero-trust authorization model. Permissions are strictly enforced at the API level via FastAPI dependencies, ensuring data security regardless of frontend UI state.

| Role | Focus Area | Key Dashboard Metrics & Capabilities |
|---|---|---|
| **Administrator** | Strategic Oversight | Institutional enrollment trends, financial health, staff-to-student ratios, and system-wide audit feeds. Full read/write access. |
| **Head of Department** | Departmental Performance | Workload distribution, at-risk subject flagging, faculty management, and curriculum oversight for their specific department. |
| **Faculty** | Academic Delivery | "Week-at-a-glance" schedules, at-risk student radar, grading queues, attendance tracking, and assignment management. |
| **Student** | Academic Success | Real-time schedules, urgent deadline tracking, daily attendance, fee status, and personalized curriculum progression. |
| **Accountant** | Financial Health | High-risk fee defaulter tracking, revenue stream breakdowns, and complete payment reconciliation workflows. |
| **Librarian** | Resource Circulation | Inventory velocity, low-stock alerts, overdue action triggers, and complete catalogue management. |

## Academic architecture

```text
Department
└── Course / Program
    └── Optional Branch / Specialization
        └── Curriculum
            └── Curriculum Version (batch locked)
                └── Semester
                    ├── Curriculum Subjects
                    │   ├── Common subjects
                    │   ├── Branch subjects
                    │   └── Elective groups
                    └── Sections
```

The canonical ownership link is `courses.department_id`. The former inverse department-to-course database link was removed by migration `0005_hierarchy_sequences`.

### Curriculum locking

A student stores their selected curriculum version. Applicable versions are resolved using course, optional branch, and admission-year range. Publishing a later curriculum does not silently move existing students to new regulations.

### Subject resolution

`GET /api/academic/students/{student_id}/subjects` resolves:

1. Common mappings for the student's semester.
2. Mappings restricted to the student's branch.
3. Elective/open-elective mappings explicitly selected by the student.
4. Applicable lab, project, and internship mappings.

## Student credentials and sequence rules

Student IDs use:

```text
YY + COURSE_CODE + BRANCH_CODE + sequence
```

Example for a 2026 B.Tech Computer Science student:

```text
Student ID:          26BTCS001
Enrollment number:  ENR-26BTCS001
Institutional email: yash.26btcs001@cms.edu
```

Rules:

- The prefix uses the final two digits of the admission year.
- Course and branch codes are uppercased and stripped of punctuation.
- The numeric sequence is padded to at least three digits.
- Each admission-year/course/branch combination owns an independent counter.
- A database sequence row is locked while allocating a number.
- Deleting a student does not decrement the counter or reuse an issued ID.
- After `26BTCS010`, the next matching registration is `26BTCS011`.
- The sequence can grow beyond `999`.

## Technology stack

### Backend

| Area | Technology |
|---|---|
| Web framework | FastAPI 0.115.6 |
| ASGI server | Uvicorn 0.34 |
| ORM | SQLAlchemy 2.0.36 |
| Migrations | Alembic 1.14.1 |
| Database driver | PyMySQL 1.1 |
| Validation/settings | Pydantic 2.10 and pydantic-settings |
| Authentication | python-jose, Passlib, bcrypt |
| Email | fastapi-mail |
| CAPTCHA | captcha |
| Files | python-multipart and aiofiles |
| Reports | fpdf2 and built-in CSV support |
| Tests | pytest and HTTPX |

### Frontend

| Area | Technology |
|---|---|
| UI | React |
| Build system | Vite |
| Routing | React Router DOM |
| Charts | Recharts |
| Icons | Lucide React |
| Code quality | ESLint with React Hooks and React Refresh plugins |
| Production hosting | Nginx container or FastAPI static SPA fallback |

### Infrastructure

- MySQL 8.4 in Docker Compose.
- MariaDB 10.6+ is also supported by the application configuration.
- Dockerfiles for backend and frontend.
- Nginx configuration for the frontend container.
- Named volumes for MySQL data and uploaded files.

## Application architecture

The backend follows layered separation:

```text
HTTP request
    ↓
Router / permission dependency
    ↓
Pydantic request schema
    ↓
Service layer and business validation
    ↓
Repository abstraction
    ↓
SQLAlchemy model / MySQL
```

Notable patterns used in the codebase:

- Application factory and lifespan startup.
- Dependency injection for sessions and authenticated users.
- Repository pattern for reusable data access.
- Service layer for business rules.
- Strategy pattern for fee calculation behavior.
- Observer/event dispatcher for operational events.
- Factory-style dashboard resolution.
- Middleware-based audit capture.
- Central exception handlers.
- SQLAlchemy relationships, composition, aggregation, and association models.

The frontend uses:

```text
AuthContext
└── Protected AppShell
    ├── Lazy-loaded pages
    ├── Resource configuration
    ├── Generic resource table
    ├── Generic create/edit form modal
    ├── Hierarchy-aware option filtering
    └── Central API client
```

## Repository structure

```text
CMS/
├── backend/
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/               Versioned schema migrations
│   ├── app/
│   │   ├── core/                   Settings, security, permissions, events, logging
│   │   ├── database/               Session, base models, bootstrap/demo seeding
│   │   ├── management/commands/    Historical and operational utilities
│   │   ├── middleware/             Audit middleware
│   │   ├── models/                 SQLAlchemy entities
│   │   ├── repositories/           Generic and concrete data access
│   │   ├── routers/                Authentication and REST APIs
│   │   ├── schemas/                Pydantic request/response contracts
│   │   ├── services/               Business rules and application services
│   │   ├── templates/email/        Student welcome email
│   │   └── utils/                  PDF, CSV, and report factories
│   ├── tests/                      Backend tests
│   ├── uploads/                    Runtime uploads
│   ├── .env.example                Environment template
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── public/                     Static institute asset
│   ├── src/
│   │   ├── components/layout/      App shell and navigation
│   │   ├── components/ui/          Forms, dialogs, cards, profile details
│   │   ├── config/                 Resource columns and form definitions
│   │   ├── lib/                    API client
│   │   ├── pages/                  Login, dashboard, resources, profile, timetable
│   │   ├── state/                  Authentication context
│   │   └── styles/                 Responsive design system
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── ACADEMIC_ARCHITECTURE.md
├── DB_SETUP.md
├── PROJECT_EXECUTION.md
├── docker-compose.yml
└── README.md
```

## Database entities

| Domain | Tables/models |
|---|---|
| Identity | `users`, `roles`, `permissions`, `user_roles`, `role_permissions` |
| Academic ownership | `departments`, `courses`, `branches` |
| Curriculum | `subject_types`, `curricula`, `curriculum_versions`, `academic_semesters` |
| Learning structure | `subjects`, `curriculum_subjects`, `elective_groups`, `student_electives`, `sections`, `faculty_assignments` |
| People | `students`, `student_sequences`, `teachers`, `subject_teachers` |
| Learning records | `attendances`, `marks` |
| Finance | `fees` |
| Library | `library_books`, `book_issues` |
| Timetable | `timetable_versions`, `timetable_slots`, legacy document support |
| Platform | `notifications`, `audit_logs` |

Most entities inherit timestamps and compatibility deletion fields from the shared base model. Current user-facing deletion paths permanently remove business records so hidden rows cannot continue blocking unique values.

## API map

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` when `DEBUG=True`.

| Prefix | Responsibilities |
|---|---|
| `/auth` | Login, logout, current user, complete own profile, password change |
| `/captcha` | Image, SVG, and tokenized CAPTCHA challenges |
| `/api/users` | Administrative user management |
| `/api/students` | Student listing, full detail, admission, updates, deletion |
| `/api/teachers` | Faculty listing, full detail, creation, updates, deletion |
| `/api/departments` | Department CRUD and HOD assignment |
| `/api/courses` | Course/program CRUD and hierarchy filtering |
| `/api/subjects` | Subject catalogue, teacher mapping, subject students |
| `/api/academic` | Branches, curricula, versions, semesters, sections, electives, mappings, faculty assignments, student subject resolution |
| `/api/attendance` | Listing, single/bulk marking, updates, statistics |
| `/api/marks` | Assessment records and student-semester marks |
| `/api/assignments` | Teacher-owned assignments, student submissions, and faculty review |
| `/api/fees` | Fee records, pending fees, payment processing |
| `/api/library` | Books, issues, returns, active loans |
| `/api/timetables` | Timetable grid/version retrieval, saving, submission, approval |
| `/api/dashboard` | Role-aware dashboard data |
| `/api/notifications` | User notifications and read state |
| `/uploads` | Backend-owned uploaded files |

List endpoints use page/page-size pagination where applicable. Hierarchy-aware resources accept relevant parameters such as `department_id`, `course_id`, `branch_id`, `student_id`, and `subject_id`.

## Prerequisites

- Python 3.10+
- Node.js 20+
- npm
- MySQL 8+ or MariaDB 10.6+
- Git
- Optional: Docker Desktop with Compose

## Local installation

### 1. Obtain the repository

```powershell
git clone https://github.com/incleon/EduCore.git
cd CMS
```

### 2. Backend environment

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` before initializing the database.

### 3. Frontend dependencies

```powershell
cd frontend
npm install
```

## Database initialization and migration

Create a MySQL database and account:

```sql
CREATE DATABASE cms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cms_user'@'%' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON cms_db.* TO 'cms_user'@'%';
FLUSH PRIVILEGES;
```

Use `'localhost'` instead of `'%'` for a local-only MySQL account.

### Brand-new empty database

Run inside `backend/`:

```powershell
python -m alembic upgrade head
python -m app.database.seed --system
```

Alembic creates the schema in revision order and records `f437010c7643` in `alembic_version`. The second command reconciles roles, permissions, subject classifications, and the bootstrap administrator. Do not use `alembic stamp head` on an empty database: stamping records a revision without creating its tables.

### Existing EduCore database

Do not stamp an existing database:

```powershell
python -m alembic upgrade head
python -m app.cli init-db
```

Migration history includes:

- `0001_initial_schema`: legacy baseline.
- `0002_academic_structure`: normalized academic and curriculum entities.
- `0003_section_scoped_timetables`: independent section timetable scope.
- `0004_null_safe_academic_scopes`: null-safe optional branch/section uniqueness.
- `2c8000b87f5f`: migration-chain compatibility revision.
- `0005_hierarchy_sequences`: canonical Department → Course link and durable student counters.
- `f437010c7643`: assignments and student submissions.

See [DB_SETUP.md](DB_SETUP.md) before changing an existing installation.

## Move the local database to a server

The application already uses MySQL through SQLAlchemy, so moving from local MySQL to a VM, Docker host, or managed MySQL service does not require changing models or business rules. Preserve both the data and the `alembic_version` table, then point `DATABASE_URL` at the new server.

### Choose one migration path

| Goal | Correct path |
|---|---|
| Move the current schema **and all current data** | Logical dump and restore (steps below) |
| Create an empty production database with the same schema/rules | Run `alembic upgrade head`, then `python -m app.database.seed --system` |
| Upgrade an older deployed EduCore database | Back it up, set its `DATABASE_URL`, then run `alembic upgrade head` |

Do not initialize the remote schema before restoring a full dump. The dump already contains tables, constraints, indexes, data, and Alembic state, and pre-creating those tables causes “table already exists” errors.

### 1. Provision the destination

Use MySQL 8.0/8.4 (or a compatible managed MySQL service), create a private database/user, enable automated backups, and allow TCP `3306` only from the backend server. Example, run as a database administrator on the destination:

```sql
CREATE DATABASE cms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cms_app'@'10.%' IDENTIFIED BY 'REPLACE_WITH_A_LONG_RANDOM_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP,
      REFERENCES, CREATE TEMPORARY TABLES, LOCK TABLES
ON cms_db.* TO 'cms_app'@'10.%';
FLUSH PRIVILEGES;
```

Replace `10.%` with the exact backend host/network allowed by your provider. Avoid `'%'` when a narrower host rule is possible. For a managed database, create the database/user through its console if direct administrative SQL is restricted.

### 2. Preflight the local database

Stop writes during the final dump (maintenance mode or stop the backend), then confirm the source is healthy and at migration head:

```powershell
cd backend
python -m alembic current
python -m alembic heads
python -m pytest -q
```

Both Alembic commands must report `f437010c7643 (head)`. Record source row counts before export:

```sql
SELECT 'users' AS table_name, COUNT(*) AS rows_count FROM users
UNION ALL SELECT 'students', COUNT(*) FROM students
UNION ALL SELECT 'teachers', COUNT(*) FROM teachers
UNION ALL SELECT 'departments', COUNT(*) FROM departments
UNION ALL SELECT 'courses', COUNT(*) FROM courses
UNION ALL SELECT 'sections', COUNT(*) FROM sections;
```

### 3. Export the local database

Run from a terminal that has MySQL client tools installed. Let the client prompt for the password; do not put it in shell history.

```powershell
mysqldump --host=127.0.0.1 --port=3306 --user=cms_user --password `
  --single-transaction --quick --routines --triggers --events `
  --default-character-set=utf8mb4 --set-gtid-purged=OFF --no-tablespaces `
  cms_db > cms_db_backup.sql
```

`--single-transaction` gives a consistent InnoDB snapshot. Keep the backend stopped until the final cutover if you cannot tolerate changes made after the dump. Store `cms_db_backup.sql` securely: it contains user and institutional data.

Optional integrity hash:

```powershell
Get-FileHash .\cms_db_backup.sql -Algorithm SHA256
```

### 4. Restore to the remote server

For direct MySQL access:

```powershell
mysql --host=YOUR_DB_HOST --port=3306 --user=cms_app --password `
  --default-character-set=utf8mb4 cms_db < cms_db_backup.sql
```

If the provider requires TLS, add its documented options, commonly `--ssl-mode=VERIFY_IDENTITY --ssl-ca=PATH_TO_CA.pem`. If it offers an import job or private proxy, use that supported route instead of opening the database publicly.

### 5. Verify schema and data before cutover

Temporarily set the backend shell to the remote URL. URL-encode special characters in the username/password (`@` → `%40`, `:` → `%3A`, `/` → `%2F`, `%` → `%25`).

```powershell
$env:DATABASE_URL='mysql+pymysql://cms_app:ENCODED_PASSWORD@YOUR_DB_HOST:3306/cms_db'
python -m alembic current
python -m alembic upgrade head
python -m app.database.seed --system
```

`alembic current` should already show the source revision because the dump includes `alembic_version`; `upgrade head` safely applies only revisions added after the dump was taken. Run the row-count query from step 2 against the destination and compare every count. Then run the opt-in live workflow test against a temporary backend connected to the destination:

```powershell
$env:RUN_LIVE_CMS_TESTS='1'
$env:CMS_BASE_URL='http://127.0.0.1:8000'
python -m pytest tests/test_live_workflows.py -q
```

The smoke test uses uniquely named records, covers all major CRUD/workflow modules, and removes its test graph afterward.

### 6. Configure the deployed backend

Store production values in the platform secret manager, not Git. Minimum settings:

```dotenv
DEBUG=False
DATABASE_URL=mysql+pymysql://cms_app:ENCODED_PASSWORD@YOUR_DB_HOST:3306/cms_db
SECRET_KEY=REPLACE_WITH_AT_LEAST_32_RANDOM_BYTES
COOKIE_SECURE=True
CORS_ORIGINS=https://cms.example.edu
ADMIN_PASSWORD=REPLACE_BEFORE_THE_FIRST_BOOT
```

Provider-specific TLS parameters may be appended to `DATABASE_URL`, for example `?ssl_ca=/run/secrets/mysql-ca.pem`. Use the exact query parameters documented by the provider/PyMySQL and mount the CA certificate read-only.

Always run migrations as a release step **before** starting the new application version:

```powershell
cd backend
python -m alembic upgrade head
python -m app.database.seed --system
python run.py
```

For multiple backend instances, run Alembic once in a dedicated release/migration job—not concurrently in every replica.

### 7. Cut over and roll back safely

1. Take one final local dump after writes are stopped.
2. Restore and verify it on the destination.
3. Change only the deployed backend's `DATABASE_URL`.
4. Start one backend instance and verify login, dashboard, students, departments, sections, assignments, uploads, and email.
5. Start the remaining instances and monitor application/database logs.
6. Keep the local database read-only and retain the verified dump until the rollback window closes.

If cutover fails, stop the deployed backend, restore its previous `DATABASE_URL`, and restart it against the untouched local database. Do not allow writes to both databases during the rollback window; this project does not include bidirectional replication or conflict resolution.

Database migration does not move uploaded files. Copy `backend/uploads/` to persistent server/object storage separately and preserve file paths referenced by database rows.

## Running the application

### Backend development server

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python run.py
```

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs` when `DEBUG=True`
- ReDoc: `http://127.0.0.1:8000/redoc` when `DEBUG=True`

### Frontend development server

Open a second terminal:

```powershell
cd frontend
npm run dev
```

- Frontend: `http://localhost:5173`
- Vite proxies API/authentication requests to the backend.

### Single-server production preview

```powershell
cd frontend
npm run build

cd ../backend
python run.py
```

When `frontend/dist` exists, FastAPI mounts the compiled assets and returns `index.html` for SPA routes.

## System data, demo seeding, and cleanup

### Automatic startup initialization

Normal startup creates/reconciles only:

- Roles.
- Permissions.
- Role-permission mappings.
- Seven fixed subject types.
- A bootstrap administrator only when no administrator exists.

Startup does not create dummy departments, courses, faculty, students, or transactions.

### Explicit demo seed

```powershell
cd backend
python -m app.database.seed
```

The seed builds a coherent demo graph with ten records for each applicable academic and operational entity:

- Departments, courses, branches.
- Curricula, versions, semesters, sections.
- Subjects, curriculum mappings, elective groups/selections.
- Faculty, students, and faculty assignments.
- Attendance, marks, and fees.
- Library books and issues.
- Timetable versions and slots.

Audit logs and notifications remain runtime-generated. The ten students belong to the current-year B.Tech (`BT`) Computer Science (`CS`) scope and receive IDs `YYBTCS001` through `YYBTCS010`.

Supporting HOD, accountant, and librarian identities are included. Dummy user password hashes match the current administrator hash; therefore their login password is the administrator password at seed time.

### System-only reconciliation

```powershell
python -m app.database.seed --system
```

### Admin-preserving cleanup

```powershell
python -m app.database.seed --clean
```

This command is destructive. It permanently deletes:

- Academic and operational records.
- Student sequence rows.
- Audit logs and notifications.
- Every non-admin user.

It preserves:

- The current administrator row and unchanged password hash.
- The administrator's role assignment.
- Roles, permissions, and role-permission mappings.
- Subject types.
- Alembic revision state.

Back up valuable databases before running cleanup.

## Environment variables

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Purpose | Development default/example |
|---|---|---|
| `APP_NAME` | Display/API application name | `Enterprise College Management System` |
| `APP_VERSION` | Application version exposed by FastAPI | `1.0.0` |
| `DEBUG` | Enables Swagger/ReDoc and development behavior | `True` |
| `DATABASE_URL` | SQLAlchemy MySQL connection | `mysql+pymysql://cms_user:...@127.0.0.1:3306/cms_db` |
| `SECRET_KEY` | JWT signing secret | Must be changed |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Login token lifetime | `60` |
| `COOKIE_SECURE` | Restricts auth cookie to HTTPS | `False` locally, `True` in production |
| `ADMIN_EMAIL` | Bootstrap admin email | `admin@cms.edu` |
| `ADMIN_USERNAME` | Bootstrap admin username | `admin` |
| `ADMIN_PASSWORD` | Bootstrap admin password | `admin123` locally only |
| `HOST` | Backend bind address | `0.0.0.0` |
| `PORT` | Backend port | `8000` |
| `LOG_LEVEL` | Application log level | `INFO` |
| `LOG_FILE` | Log destination | `logs/cms.log` |
| `UPLOAD_DIR` | Upload storage | `uploads` |
| `MAX_UPLOAD_SIZE` | Maximum upload bytes | `5242880` |
| `DEFAULT_PAGE_SIZE` | Default API page size | `10` |
| `MAX_PAGE_SIZE` | Maximum API page size | `100` |
| `CORS_ORIGINS` | Comma-separated browser origins | Local Vite URLs |
| `MAIL_USERNAME` | SMTP username | Project mailbox/example |
| `MAIL_PASSWORD` | SMTP app/service password | Must be configured |
| `MAIL_FROM` | Sender address | Usually SMTP username |
| `MAIL_SERVER` | SMTP hostname | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_STARTTLS` | STARTTLS toggle | `True` |
| `MAIL_SSL_TLS` | Direct TLS toggle | `False` |
| `MAIL_VALIDATE_CERTS` | TLS certificate validation | `True` |

MySQL helper variables (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_ROOT_USER`, `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, and `MYSQL_PASSWORD`) are also present for provisioning commands and container configuration.

Passwords containing `@`, `:`, `/`, `#`, or `%` must be URL-encoded inside `DATABASE_URL`.

## Quality checks

### Backend

```powershell
cd backend
python -m compileall -q app
pytest -q
python -m alembic current
```

The migration check should report `f437010c7643 (head)` or a later revision.

To exercise the complete running application against the configured database (the test creates uniquely named records and cleans them up):

```powershell
$env:RUN_LIVE_CMS_TESTS='1'
$env:CMS_BASE_URL='http://127.0.0.1:8000'
pytest tests/test_live_workflows.py -q
```

### Frontend

```powershell
cd frontend
npm run lint
npm run build
```

The production bundle is written to `frontend/dist/`.

## Docker deployment

```powershell
docker compose up --build
```

Services:

| Service | Address | Notes |
|---|---|---|
| Frontend | `http://localhost:8080` | Nginx-hosted React build |
| Backend | `http://localhost:8000` | FastAPI API |
| MySQL | `localhost:3306` | Persistent `mysql_data` volume |

Docker volumes:

- `mysql_data`: database persistence.
- `uploads`: backend upload persistence.

The Compose file contains development placeholder passwords. Change them before using it outside a local environment.

To use a managed/remote database, remove or disable the `db` service, remove the backend's hard-coded Compose `DATABASE_URL` override, and supply the production `DATABASE_URL` through a secret. The backend no longer needs `depends_on: db`; it only needs network access to the database host. Do not publish a managed database through the Compose host.

Useful commands:

```powershell
# Start or rebuild
docker compose up --build

# Run in background
docker compose up -d --build

# View logs
docker compose logs -f backend

# Stop containers without deleting volumes
docker compose down
```

## Production deployment

Recommended sequence:

```powershell
cd frontend
npm ci
npm run lint
npm run build

cd ../backend
pip install -r requirements.txt
python -m alembic upgrade head
$env:DEBUG='False'
python run.py
```

Production requirements:

- Use a strong `SECRET_KEY`.
- Set a strong bootstrap administrator password before first startup.
- Set `COOKIE_SECURE=True` and serve through HTTPS.
- Restrict `CORS_ORIGINS` to trusted frontend domains.
- Configure a managed MySQL/MariaDB database with backups.
- Configure SMTP credentials through secret storage.
- Persist the uploads directory.
- Run migrations before starting upgraded application instances.
- Serve `frontend/dist` through Nginx/CDN or allow FastAPI to serve the SPA.
- Disable development documentation by setting `DEBUG=False`.

## Security notes

- Authentication tokens are stored in HTTP-only cookies.
- Production cookies should be secure and transported only over HTTPS.
- CAPTCHA reduces automated login attempts.
- Passwords are hashed with bcrypt; hashes are never returned through profile APIs.
- Authorization is permission-based and enforced server-side.
- Existing admin credentials are not overwritten by startup reconciliation.
- The demo seed copies the admin password hash; use it only in controlled development environments.
- Never commit `.env`, SMTP credentials, database dumps, access tokens, or production secrets.
- Rotate every development/default credential before shared deployment.
- The cleanup command is destructive and should follow a verified backup.

## Troubleshooting

### Database connection fails

- Confirm MySQL is running and accepting TCP connections.
- Check `DATABASE_URL`, database name, username, password, and port.
- URL-encode special characters in the password.
- Confirm the MySQL user has privileges on `cms_db`.

### Tables already exist during setup

- Use the fresh-database sequence only for a truly empty database.
- Use `alembic upgrade head` for an existing installation.
- Do not replay the legacy baseline over tables created by SQLAlchemy.

### Alembic revision is behind

```powershell
cd backend
python -m alembic upgrade head
python -m app.cli init-db
```

### A deleted code/email previously said “already exists”

Current deletion paths permanently remove business rows. Upgrade to the latest migration and use the admin-preserving cleanup command once to remove historical ghost rows when appropriate.

### Frontend cannot reach the API

- Confirm the backend is listening on port `8000`.
- Confirm Vite proxy settings or production `CORS_ORIGINS`.
- When using cookies across origins, ensure credentials and HTTPS settings match.

### Email is not sent

- Configure `MAIL_USERNAME`, `MAIL_PASSWORD`, and `MAIL_FROM`.
- For Gmail, use an app password rather than the normal account password.
- Verify port `587`, STARTTLS, and certificate settings.

### Swagger UI is missing

`/docs` and `/redoc` are disabled when `DEBUG=False`.

### Demo seed or cleanup warning

- Run commands from `backend/` with the virtual environment active.
- Apply migrations before seeding.
- Back up data before `--clean`.
- Startup itself does not insert demo data.

## Additional documentation

- [Database setup](DB_SETUP.md)
- [Project execution guide](PROJECT_EXECUTION.md)
- [Academic architecture](ACADEMIC_ARCHITECTURE.md)

---

<p align="center">
  Built as a modular academic administration platform with explicit data ownership, durable credential generation, and role-aware workflows.
</p>
