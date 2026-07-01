# EduCore database setup

This is the canonical database guide for EduCore CMS. For application
installation, startup, and everyday commands, use
[EXECUTION_PLAN.md](EXECUTION_PLAN.md).

EduCore supports MySQL 8.x and MariaDB 10.6+ through SQLAlchemy and PyMySQL.
Run all backend commands in this guide from the `backend/` directory with the
Python virtual environment active.

## Choose the correct path

| Situation | Required action |
|---|---|
| New machine using Docker | Follow [Docker first run](#docker-first-run) |
| New, empty native MySQL database | Follow [Initialize a new database](#initialize-a-new-database) |
| Existing EduCore database with `alembic_version` | Follow [Upgrade an existing database](#upgrade-an-existing-database) |
| Moving an existing database to another machine | Follow [Backup and restore](#backup-and-restore) |
| Existing tables but no `alembic_version` | Stop and inspect the schema; do not stamp or migrate blindly |

> Important: the initial Alembic revision is a baseline marker and does not
> create the original tables. Consequently, a fresh database uses
> `init-db --no-seed` followed by `alembic stamp head`. An existing database
> uses `alembic upgrade head`. These workflows are not interchangeable.

## 1. Create the database and application user

Start MySQL or MariaDB, then sign in with an administrative account:

```text
mysql -u root -p
```

Run:

```sql
CREATE DATABASE cms_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'cms_user'@'localhost'
  IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';

GRANT ALL PRIVILEGES ON cms_db.* TO 'cms_user'@'localhost';
FLUSH PRIVILEGES;
```

Use `'localhost'` for a backend running on the same machine. For a backend on
another host, replace it with that host or a restricted network pattern. Avoid
`'%'` outside isolated local development.

Confirm the account works:

```text
mysql -h 127.0.0.1 -P 3306 -u cms_user -p cms_db
```

## 2. Configure `backend/.env`

Create the local environment file from the repository root.

Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

macOS/Linux:

```bash
cp backend/.env.example backend/.env
```

Set at least:

```dotenv
DATABASE_URL=mysql+pymysql://cms_user:ENCODED_PASSWORD@127.0.0.1:3306/cms_db
SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
DEBUG=True
ADMIN_EMAIL=admin@cms.edu
ADMIN_USERNAME=admin
ADMIN_PASSWORD=REPLACE_WITH_A_STRONG_ADMIN_PASSWORD
COOKIE_SECURE=False
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Percent-encode reserved URL characters in the database username or password:

| Character | Encoding |
|---|---|
| `@` | `%40` |
| `:` | `%3A` |
| `/` | `%2F` |
| `#` | `%23` |
| `%` | `%25` |

Do not commit `.env`, SQL dumps, or production credentials.

## 3. Initialize a new database

Use this only when `cms_db` contains no EduCore tables.

```text
cd backend
python -m app.cli init-db --no-seed
python -m alembic stamp head
python -m app.database.seed --system
python -m alembic current
```

What these commands do:

1. `init-db --no-seed` creates the current schema from SQLAlchemy models.
2. `alembic stamp head` records that this newly created schema matches the
   current migration head without replaying historical migrations.
3. `seed --system` creates or reconciles roles, permissions, subject types, and
   the bootstrap administrator.
4. `alembic current` confirms that the database is tracked at the current head.

Do not run `alembic upgrade head` first on an empty database. The baseline
revision intentionally contains no table-creation operations.

## 4. Upgrade an existing database

Use this only when the database already has an `alembic_version` table.

Back up the database first, stop application writes, then run:

```text
cd backend
python -m alembic current
python -m alembic heads
python -m alembic upgrade head
python -m app.database.seed --system
python -m alembic current
```

The final `current` revision must match `heads`. Do not hard-code a revision
number in operational instructions; the head changes when migrations are added.

Never use `alembic stamp head` to “fix” an unknown existing database. Stamping
changes migration metadata without changing tables and can hide a schema
mismatch.

## 5. System data and demonstration data

Normal backend startup reconciles only permanent system metadata:

- Roles and permissions.
- Role-permission mappings.
- Fixed subject types.
- A bootstrap administrator when no administrator exists.

It does not replace an existing administrator’s password and does not
automatically insert demonstration business records.

To explicitly create the comprehensive demonstration dataset:

```text
cd backend
python -m app.database.seed
```

The comprehensive seed is intended for development and demonstrations. It
replaces business data while preserving the administrator and authorization
metadata. Do not run it against a database containing valuable institutional
data.

To reconcile system metadata only:

```text
python -m app.database.seed --system
```

To delete business data and all non-admin users while preserving the current
administrator and system metadata:

```text
python -m app.database.seed --clean
```

`--clean` is destructive. Take a verified backup first.

## 6. Docker first run

The Compose stack creates MySQL and starts the backend. On its first startup,
the backend creates the current schema and system metadata.

From the repository root:

```text
docker compose up -d --build
docker compose logs -f backend
```

After the backend reports a successful startup, open another terminal and
record the migration state:

```text
docker compose exec backend python -m alembic stamp head
docker compose exec backend python -m alembic current
```

Optional development data:

```text
docker compose exec backend python -m app.database.seed
```

For later application upgrades with the existing `mysql_data` volume:

```text
docker compose stop backend
docker compose build
docker compose run --rm backend python -m alembic upgrade head
docker compose up -d
docker compose exec backend python -m app.database.seed --system
```

Change the placeholder Compose passwords before shared or production use.
Deleting the `mysql_data` volume permanently deletes the database.

## 7. Backup and restore

### Create a backup

Stop or pause writes, then let the client prompt for the password:

```text
mysqldump -h 127.0.0.1 -P 3306 -u cms_user -p \
  --single-transaction --quick --routines --triggers --events \
  --default-character-set=utf8mb4 --no-tablespaces \
  cms_db > cms_db_backup.sql
```

PowerShell accepts the same command on one line. If split across lines, use the
PowerShell backtick instead of `\`.

The dump includes `alembic_version`; do not initialize destination tables before
restoring a full dump.

### Restore on another machine

Create an empty destination database and user, then run:

```text
mysql -h DESTINATION_HOST -P 3306 -u cms_user -p \
  --default-character-set=utf8mb4 cms_db < cms_db_backup.sql
```

After restoring:

```text
cd backend
python -m alembic current
python -m alembic upgrade head
python -m app.database.seed --system
```

Copy `backend/uploads/` separately. Database dumps do not contain uploaded files.

## 8. Verification

From `backend/`:

```text
python -m alembic current
python -m alembic heads
python -m compileall -q app
python -m pytest -q
```

Then start the backend and verify:

- `http://127.0.0.1:8000/docs` loads when `DEBUG=True`.
- `GET /captcha/new` returns a CAPTCHA challenge.
- The configured administrator can sign in.
- Students, faculty, academic, finance, library, assignment, and timetable
  pages load without API errors.

## Troubleshooting

### Cannot connect to MySQL

- Confirm the database service is running.
- Check the host, port, database name, user, and password.
- Confirm the user’s allowed host matches where the backend runs.
- Percent-encode special characters in `DATABASE_URL`.
- Check that port `3306` is not already occupied when using Docker.

### “Table already exists” during setup

You used the wrong path:

- New empty database: create the schema, then stamp it.
- Existing tracked database: upgrade it.
- Restored full dump: do not pre-create tables.

### Existing tables but no migration version

Do not guess a revision and do not stamp head. Back up the database, compare its
schema with the migration history, and establish the correct baseline before
continuing.

### Access denied

Recheck the MySQL account host and grants:

```sql
SHOW GRANTS FOR 'cms_user'@'localhost';
```

### Reset local Docker data

The following deletes the local Docker database permanently:

```text
docker compose down -v
```

Use it only when a disposable local database can be recreated.
