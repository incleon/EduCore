# EduCore execution plan

This guide takes a new machine from a cloned repository to a running EduCore
CMS. It supports Windows, macOS, and Linux.

Database creation, migration, backup, and recovery rules live in the canonical
[DB_SETUP.md](DB_SETUP.md). That guide must be followed whenever the database
state changes.

## Choose an installation method

| Method | Best for | Required software |
|---|---|---|
| [Docker Compose](#option-a-docker-compose-recommended) | Fastest and most reproducible setup | Git, Docker Desktop or Docker Engine with Compose |
| [Native development](#option-b-native-development) | Backend/frontend development and debugging | Git, Python 3.10+, Node.js 20+, MySQL 8+ or MariaDB 10.6+ |

Do not combine the database initialization commands from the two methods.

## 1. Get the project

```text
git clone https://github.com/incleon/EduCore.git
cd EduCore
```

If the repository was downloaded as an archive, extract it and open a terminal
in the directory containing `backend/`, `frontend/`, and `docker-compose.yml`.

## Option A: Docker Compose (recommended)

Docker provides the same MySQL, Python, Node, backend, and frontend environment
on all supported operating systems.

### A1. Create the environment file

Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

macOS/Linux:

```bash
cp backend/.env.example backend/.env
```

For local evaluation, the example values match the development Compose file.
Before shared or production use, change the database passwords, `SECRET_KEY`,
and administrator password in both the environment and Compose configuration.

### A2. Build and start

```text
docker compose up -d --build
docker compose logs -f backend
```

Wait until the backend reports a successful startup, then press `Ctrl+C` to stop
following logs. This does not stop the containers.

### A3. Record the first database baseline

Run this once for a newly created `mysql_data` volume:

```text
docker compose exec backend python -m alembic stamp head
docker compose exec backend python -m alembic current
```

The reason for this first-run step is documented in
[DB_SETUP.md](DB_SETUP.md#initialize-a-new-database).

### A4. Add demonstration data (optional)

```text
docker compose exec backend python -m app.database.seed
```

This command replaces business data and is only appropriate for development or
demonstration databases.

### A5. Open the application

| Service | Address |
|---|---|
| Web application | `http://localhost:8080` |
| Backend API | `http://localhost:8000` |
| API documentation when enabled | `http://localhost:8000/docs` |
| MySQL from the host | `127.0.0.1:3306` |

Use the administrator email and password configured in `backend/.env`.

### A6. Everyday Docker commands

```text
# View service state
docker compose ps

# Follow backend logs
docker compose logs -f backend

# Restart without rebuilding
docker compose restart

# Rebuild after dependency or Dockerfile changes
docker compose up -d --build

# Stop while preserving data
docker compose down
```

Do not add `-v` to `docker compose down` unless the local database may be
permanently deleted.

## Option B: Native development

### B1. Create the backend environment

Windows PowerShell:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Keep this terminal open. All backend commands below assume the virtual
environment is active and the current directory is `backend/`.

### B2. Configure and initialize MySQL

Follow these sections in order:

1. [Create the database and application user](DB_SETUP.md#create-the-database-and-application-user)
2. [Configure `backend/.env`](DB_SETUP.md#configure-backendenv)
3. [Initialize a new database](DB_SETUP.md#initialize-a-new-database)

For an existing installation, use
[Upgrade an existing database](DB_SETUP.md#upgrade-an-existing-database)
instead of the new-database procedure.

### B3. Start the backend

```text
python run.py
```

Backend addresses:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs` when `DEBUG=True`
- ReDoc: `http://127.0.0.1:8000/redoc` when `DEBUG=True`

Leave this terminal running.

### B4. Install and start the frontend

Open a second terminal in the repository root.

Windows PowerShell:

```powershell
cd frontend
npm ci
npm run dev
```

macOS/Linux:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. The Vite development server proxies API,
authentication, CAPTCHA, and upload requests to port `8000`.

If `npm ci` reports that the lock file is out of sync, use `npm install` once to
refresh dependencies, then commit the intentional lock-file update.

## Optional demonstration dataset

The backend starts with system metadata and an administrator, not disposable
business data. To populate every major module for development:

```text
cd backend
python -m app.database.seed
```

The seed is destructive to existing business data. Its behavior, cleanup
command, and safety notes are documented in
[DB_SETUP.md](DB_SETUP.md#system-data-and-demonstration-data).

## Validate the installation

### Backend checks

From `backend/` with the virtual environment active:

```text
python -m compileall -q app
python -m pytest -q
python -m alembic current
python -m alembic heads
```

`current` and `heads` must report the same revision.

### Frontend checks

From `frontend/`:

```text
npm run lint
npm run build
```

### Manual smoke test

1. Open the login page.
2. Sign in with the configured administrator.
3. Confirm the dashboard loads.
4. Open students, faculty, departments, courses, branches, attendance, marks,
   finance, library, assignments, and timetable.
5. Confirm browser developer tools show no failed API requests.

## Resume work on another day

Native installation:

```text
# Terminal 1
cd backend
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python run.py

# Terminal 2
cd frontend
npm run dev
```

Docker installation:

```text
docker compose up -d
```

## Pull and run a newer version

### Native installation

```text
git pull

cd backend
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m app.database.seed --system

cd ../frontend
npm ci
```

Restart the backend and frontend after the update.

### Docker installation

```text
git pull
docker compose stop backend
docker compose build
docker compose run --rm backend python -m alembic upgrade head
docker compose up -d
docker compose exec backend python -m app.database.seed --system
```

Back up a valuable database before upgrading. See
[DB_SETUP.md](DB_SETUP.md#backup-and-restore).

## Production build

Production deployment requires HTTPS, persistent uploads, a backed-up database,
restricted network access, and secrets stored outside Git. See
[DEPLOYMENT.md](DEPLOYMENT.md) for the complete deployment topology.

For a local production-style build:

```text
cd frontend
npm ci
npm run lint
npm run build

cd ../backend
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m app.database.seed --system
```

Set production values before startup:

```dotenv
DEBUG=False
COOKIE_SECURE=True
CORS_ORIGINS=https://cms.example.edu
DATABASE_URL=mysql+pymysql://USER:ENCODED_PASSWORD@DB_HOST:3306/cms_db
SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
```

Then run:

```text
python run.py
```

When `frontend/dist/` exists, FastAPI can serve the compiled single-page
application. Nginx or a CDN may serve it separately in a full deployment.

## Common failures

### Backend cannot connect to the database

Use the checklist in
[DB_SETUP.md](DB_SETUP.md#cannot-connect-to-mysql).

### Frontend cannot reach the backend

- Confirm the backend is listening on `127.0.0.1:8000`.
- Confirm the frontend is running on `localhost:5173`.
- Check `frontend/vite.config.js` proxy targets.
- Check `CORS_ORIGINS` for non-proxied deployments.

### Login fails

- Confirm the values in the environment used during the first database
  initialization.
- Remember that changing `ADMIN_PASSWORD` later does not reset an existing
  administrator.
- Confirm `/captcha/new` succeeds.

### Port already in use

- Stop the conflicting process or change the configured port.
- Docker commonly conflicts with a native MySQL already using port `3306`.
- Native and Docker backends cannot both bind port `8000`.

### Reset a forgotten local administrator

Do not delete production users or edit password hashes manually. Restore from a
known backup or use an approved account-recovery procedure.
