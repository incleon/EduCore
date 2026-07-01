"""
FastAPI Application Factory — Main Entry Point
=================================================

OOP Concepts Demonstrated:
--------------------------
1. FACTORY PATTERN: create_app() is an application factory
2. COMPOSITION: App composes routers, middleware, exception handlers
3. DEPENDENCY INJECTION: FastAPI's built-in DI system
4. ASSOCIATION: Routers are associated with the app

This is where everything comes together:
- Database initialization
- Middleware registration
- Route registration
- Exception handler registration
- Static file serving
- Template engine setup
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.exception_handlers import register_exception_handlers
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.exception_handlers import register_exception_handlers
from app.database.session import init_db, SessionLocal
from app.database.seed import seed_system_data
from app.middleware.audit_middleware import AuditMiddleware

# Import routers
from app.routers.auth import router as auth_router
from app.routers.api_routes import (
    users_router, students_router, teachers_router,
    courses_router, departments_router, subjects_router,
    attendance_router, marks_router, library_router,
    timetables_router
)
from app.routers.finance import router as finance_router, legacy_router as legacy_finance_router
from app.routers.captcha import router as captcha_router
from app.routers.dashboard import router as dashboard_router
from app.routers.notifications import router as notifications_router
from app.routers.academic import router as academic_router
from app.routers.assignments import assignments_router

# ── Setup logging before anything else ───────────────────────
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan — runs on startup and shutdown.

    Startup: Initialize database, run seed data
    Shutdown: Cleanup resources
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create necessary directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    # Initialize database tables

    # Initialize database tables
    init_db()

    # Reconcile required authorization metadata only. Demo data is explicit.
    db = SessionLocal()
    try:
        seed_system_data(db)
    finally:
        db.close()

    logger.info("Application started successfully!")
    logger.info(f"API docs: http://localhost:{settings.PORT}/docs")
    logger.info(f"Web app: http://localhost:{settings.PORT}/login")

    yield  # Application runs here

    logger.info("Application shutting down...")


def create_app() -> FastAPI:
    """
    APPLICATION FACTORY PATTERN.

    Why factory pattern?
    - Configurable: different configs for dev/test/prod
    - Testable: create test instances with different settings
    - Clean: all setup logic centralized
    """

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise College Management System with RBAC",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS Middleware ──────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Audit Middleware ─────────────────────────────────────
    app.add_middleware(AuditMiddleware)

    # ── Exception Handlers ───────────────────────────────────
    register_exception_handlers(app)

    # Uploaded files remain backend-owned. The React build is mounted below
    # only when a production bundle exists.
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    # ── Register API Routers ─────────────────────────────────
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(students_router)
    app.include_router(teachers_router)
    app.include_router(courses_router)
    app.include_router(departments_router)
    app.include_router(subjects_router)
    app.include_router(attendance_router)
    app.include_router(marks_router)
    app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
    app.include_router(legacy_finance_router)
    app.include_router(library_router)
    app.include_router(timetables_router)
    app.include_router(dashboard_router)
    app.include_router(notifications_router)
    app.include_router(academic_router)
    app.include_router(assignments_router)

    app.include_router(captcha_router)

    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

        @app.get("/{path:path}", include_in_schema=False)
        def serve_spa(path: str):
            requested = frontend_dist / path
            if path and requested.is_file():
                return FileResponse(requested)
            return FileResponse(frontend_dist / "index.html")

    return app


# ── Create the app instance ─────────────────────────────────
app = create_app()
