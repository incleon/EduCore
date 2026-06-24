# Project execution guide

## Prerequisites

- Python 3.10 or newer
- Node.js 20 or newer
- MySQL 8+ or MariaDB 10.6+

## First-time local setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `DATABASE_URL`, `SECRET_KEY`, and the bootstrap administrator values in `.env`. Then initialize a brand-new empty database:

```powershell
python -m app.cli init-db --no-seed
python -m alembic stamp head
python -m app.cli init-db
python run.py
```

For an existing installation, do not stamp the database. Apply every migration, including the canonical-hierarchy and student-sequence migration:

```powershell
python -m alembic upgrade head
python -m app.cli init-db
python run.py
```

`init-db` and normal application startup reconcile system metadata only. Demo data is never inserted automatically.

### Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies backend, authentication, CAPTCHA, and upload requests.

## Demo and cleanup workflow

Run commands from `backend/` with the virtual environment active.

```powershell
# Add the deterministic ten-record demo dataset
python -m app.database.seed

# Reconcile roles, permissions, subject types, and bootstrap admin only
python -m app.database.seed --system

# Destructive: remove business records and all non-admin users
python -m app.database.seed --clean
```

The cleanup command preserves:

- The current administrator row and password hash.
- The administrator role assignment.
- Roles, permissions, role-permission mappings, and subject types.
- Alembic migration state.

It permanently removes academic and operational records, audit/notification data, student-number counters, and every non-admin user. Take a database backup before running it against valuable data.

The demo command creates current-year IDs such as `26BTCS001` through `26BTCS010`. The exact year prefix follows the year in which the seeder runs. All dummy accounts use the administrator’s current password hash.

## Quality checks

```powershell
cd backend
python -m compileall -q app
pytest -q
python -m alembic current

cd ../frontend
npm run lint
npm run build
```

The Alembic result should report `0005_hierarchy_sequences (head)` or a later revision.

## Production build

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

When `frontend/dist` exists, FastAPI can serve the compiled application. A separate CDN or Nginx deployment is also supported.

Recommended production settings:

```dotenv
DEBUG=False
CORS_ORIGINS=https://your-campus-domain.example
SECRET_KEY=<long-random-secret>
COOKIE_SECURE=True
DATABASE_URL=<managed-mysql-connection-url>
ADMIN_EMAIL=<initial-admin-address>
ADMIN_USERNAME=<initial-admin-username>
ADMIN_PASSWORD=<strong-initial-password>
```

Change bootstrap credentials before the first production start. Once an administrator exists, changing `ADMIN_PASSWORD` does not reset that account.

## Docker Compose

```powershell
docker compose up --build
```

- Frontend: `http://localhost:8080`
- Backend API: `http://localhost:8000`
- MySQL: local port `3306`

Apply migrations inside the backend container whenever an existing deployment is upgraded.
