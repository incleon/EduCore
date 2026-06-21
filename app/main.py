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
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.exception_handlers import register_exception_handlers
from app.database.session import init_db, SessionLocal
from app.database.seed import seed_database
from app.middleware.audit_middleware import AuditMiddleware

# Import routers
from app.routers.auth import router as auth_router
from app.routers.api_routes import (
    users_router, students_router, teachers_router,
    courses_router, departments_router, subjects_router,
    attendance_router, marks_router, fees_router, library_router,
    timetables_router
)
from app.routers.pages import router as pages_router


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
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Initialize database tables
    init_db()

    # Seed with demo data
    db = SessionLocal()
    try:
        seed_database(db)
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
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Audit Middleware ─────────────────────────────────────
    app.add_middleware(AuditMiddleware)

    # ── Exception Handlers ───────────────────────────────────
    register_exception_handlers(app)

    # ── Mount Static Files ───────────────────────────────────
    os.makedirs("app/static/css", exist_ok=True)
    os.makedirs("app/static/js", exist_ok=True)
    os.makedirs("app/static/images", exist_ok=True)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
    app.include_router(fees_router)
    app.include_router(library_router)
    app.include_router(timetables_router)

    # ── Register Page Routers (Jinja2 templates) ─────────────
    app.include_router(pages_router)

    return app


# ── Create the app instance ─────────────────────────────────
app = create_app()
