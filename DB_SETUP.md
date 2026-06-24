# Database setup

EduCore uses MySQL or MariaDB through SQLAlchemy and Alembic.

## 1. Create the database and account

Sign in to MySQL as an administrator:

```sql
CREATE DATABASE cms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cms_user'@'%' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON cms_db.* TO 'cms_user'@'%';
FLUSH PRIVILEGES;
```

For a local-only account, replace `'%'` with `'localhost'`.

## 2. Configure the backend

```powershell
Copy-Item backend/.env.example backend/.env
```

Set at least:

```dotenv
DATABASE_URL=mysql+pymysql://cms_user:your-password@127.0.0.1:3306/cms_db
SECRET_KEY=generate-a-long-random-production-secret
DEBUG=True
ADMIN_EMAIL=admin@cms.edu
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

URL-encode passwords containing `@`, `:`, `/`, `#`, or `%` inside `DATABASE_URL`. Never retain the example administrator password outside local development.

## 3. Initialize a brand-new database

Activate the backend environment and enter `backend/`:

```powershell
python -m app.cli init-db --no-seed
python -m alembic stamp head
python -m app.cli init-db
```

This creates the current schema, records it at the current Alembic head, and inserts required system metadata. The legacy baseline must not be replayed against an empty schema created by SQLAlchemy.

## 4. Upgrade an existing database

```powershell
cd backend
python -m alembic upgrade head
python -m app.cli init-db
```

Revision `0005_hierarchy_sequences` performs two important upgrades:

- Makes `Course.department_id` the canonical Department → Course relationship and removes the obsolete inverse department link.
- Adds `student_sequences`, which tracks the last issued number for each admission-year/course/branch scope.

The migration is restart-safe for MySQL’s non-transactional DDL behavior.

## Startup behavior

Backend startup does not seed dummy courses, departments, people, or transactions. It only reconciles:

- Roles and permissions.
- Role-permission mappings.
- Fixed subject types.
- A bootstrap administrator when no administrator exists.

An existing administrator’s username, email, and password hash are never overwritten.

## Demo seeding

To create the complete demo dataset explicitly:

```powershell
cd backend
python -m app.database.seed
```

The command is designed to be repeatable and uses stable codes to avoid duplicate demo records. It seeds ten records for each applicable academic and operational entity. Audit logs and notifications remain runtime-generated.

Student IDs follow:

```text
YY + course code + branch code + sequence
26BTCS001
```

Institutional email follows:

```text
firstname.26btcs001@cms.edu
```

The ten seeded B.Tech Computer Science students occupy sequences `001`–`010`; the next matching registration receives `011`.

## Admin-preserving cleanup

To permanently clean the database while keeping the current administrator and system metadata:

```powershell
cd backend
python -m app.database.seed --clean
```

This is destructive. It physically deletes business records and non-admin users, clears student sequences, and frees unique names, codes, usernames, emails, and ISBNs for reuse. Back up important data first.

## Verification

```powershell
python -m alembic current
python -m compileall -q app
pytest -q
```

With the backend running:

- `/docs` should load when `DEBUG=True`.
- `GET /captcha/new` should return a CAPTCHA challenge.
- The configured administrator should be able to sign in.
- A clean database should contain no business records or non-admin users.

## Docker database

`docker compose up --build` provisions MySQL and supplies the backend connection to the `db` service. Replace all placeholder passwords before using the Compose configuration outside local development.

Never commit `backend/.env`, database dumps, or production credentials.
