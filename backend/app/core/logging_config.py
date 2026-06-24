"""
Logging Configuration
======================

OOP Concepts Demonstrated:
--------------------------
1. SINGLETON PATTERN: Logger instances are singletons (Python's logging module)
2. FACTORY PATTERN: get_logger() is a factory function that creates/returns loggers
3. ENCAPSULATION: Log format and handlers are encapsulated in setup function

Why structured logging?
- Production systems need traceable, searchable logs
- Consistent format across all modules
- File + console output for different environments
- Log levels filter noise in production
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.config import settings


def setup_logging() -> None:
    """
    Configure application-wide logging.

    Creates both console and file handlers with rotation.
    File rotation prevents log files from growing indefinitely
    (important in production environments).
    """
    # Ensure log directory exists
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # ── Log Format ───────────────────────────────────────
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Root Logger ──────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicate logs on reload
    root_logger.handlers.clear()

    # ── Console Handler ──────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root_logger.addHandler(console_handler)

    # ── File Handler (with rotation) ─────────────────────
    file_handler = RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=10_485_760,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """
    FACTORY FUNCTION for creating named loggers.

    Why a factory function?
    - Ensures consistent logger naming convention
    - Single point to add custom logic (e.g., extra fields)
    - Each module gets its own logger for granular control

    Usage:
        logger = get_logger(__name__)
        logger.info("Student created", extra={"student_id": 123})
    """
    return logging.getLogger(f"cms.{name}")
