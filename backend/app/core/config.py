"""
Application Configuration
==========================

OOP Concepts Demonstrated:
--------------------------
1. INHERITANCE: Settings inherits from Pydantic BaseSettings
2. ENCAPSULATION: Configuration values are encapsulated in a single class
3. CLASS METHODS: model_config is a class-level configuration
4. SINGLETON PATTERN: 'settings' is a module-level singleton instance

Why this approach?
- Type-safe configuration (Pydantic validates types automatically)
- Environment variable loading (from .env file)
- Single source of truth for all config values
- Easy to test (just create a new Settings instance with overrides)

SOLID Principles:
- SRP: This class only handles configuration
- OCP: New config values can be added without modifying existing code
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class demonstrates INHERITANCE (extends BaseSettings) and
    ENCAPSULATION (all config values are encapsulated here).

    Pydantic BaseSettings automatically reads from:
    1. Environment variables
    2. .env file
    3. Default values defined here
    """

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = Field(
        default="Enterprise College Management System",
        description="Application display name"
    )
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode toggle")

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="mysql+pymysql://cms_user:secure_password@127.0.0.1:3306/cms_db",
        description="Database connection string"
    )

    # ── JWT Authentication ───────────────────────────────────
    SECRET_KEY: str = Field(
        default="change-this-in-production",
        description="JWT signing secret key"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="JWT token expiration in minutes"
    )
    COOKIE_SECURE: bool = Field(
        default=False,
        description="Send authentication cookies only over HTTPS",
    )
    ADMIN_EMAIL: str = Field(default="admin@cms.edu", description="Bootstrap administrator email")
    ADMIN_USERNAME: str = Field(default="admin", description="Bootstrap administrator username")
    ADMIN_PASSWORD: str = Field(default="admin123", description="Bootstrap administrator password")

    # ── Server ───────────────────────────────────────────────
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # ── Logging ──────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="logs/cms.log", description="Log file path")

    # ── File Upload ──────────────────────────────────────────
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")
    MAX_UPLOAD_SIZE: int = Field(
        default=5_242_880,  # 5MB
        description="Maximum upload file size in bytes"
    )

    # ── Pagination ───────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = Field(default=10, description="Default page size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum page size")

    # ── Frontend ─────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated browser origins allowed to call the API",
    )

    # ── Email ────────────────────────────────────────────────
    MAIL_USERNAME: str = Field(default="info.educorecms@gmail.com", description="SMTP Username")
    MAIL_PASSWORD: str = Field(default="", description="SMTP App Password or service password")
    MAIL_FROM: Optional[str] = Field(default=None, description="SMTP From address")
    MAIL_SERVER: str = Field(default="smtp.gmail.com", description="SMTP server")
    MAIL_PORT: int = Field(default=587, description="SMTP port")
    MAIL_STARTTLS: bool = Field(default=True, description="Enable STARTTLS")
    MAIL_SSL_TLS: bool = Field(default=False, description="Enable SSL/TLS")
    MAIL_VALIDATE_CERTS: bool = Field(default=True, description="Validate SMTP certificates")
    MAIL_DEBUG: int = Field(default=0, description="SMTP debug level")
    MAIL_TIMEOUT: int = Field(default=30, description="SMTP connection timeout in seconds")

    # ── Class-level configuration ────────────────────────────
    model_config = {
        "env_file": str(BACKEND_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

    # ── CLASS METHOD: Alternative constructor ────────────────
    @classmethod
    def for_testing(cls) -> "Settings":
        """
        CLASS METHOD demonstrating an alternative constructor pattern.

        Why class method instead of static method?
        - Class methods receive the class itself (cls) as first argument
        - They can create instances of the class
        - They support inheritance (subclass will create subclass instance)

        Usage: test_settings = Settings.for_testing()
        """
        return cls(
            DATABASE_URL="mysql+pymysql://cms_user:secure_password@127.0.0.1:3306/test_cms_db",
            DEBUG=True,
            SECRET_KEY="test-secret-key",
            LOG_LEVEL="DEBUG",
        )

    # ── MAGIC METHOD: String representation ──────────────────
    def __repr__(self) -> str:
        """
        MAGIC METHOD (__repr__) for developer-friendly representation.

        Why use __repr__?
        - Called by repr() and in debugger
        - Should be unambiguous and ideally recreatable
        - Helps during debugging to see configuration state
        """
        return (
            f"Settings(APP_NAME='{self.APP_NAME}', "
            f"DEBUG={self.DEBUG}, "
            f"DATABASE_URL='{self.DATABASE_URL}')"
        )

    def __str__(self) -> str:
        """
        MAGIC METHOD (__str__) for user-friendly representation.

        Why different from __repr__?
        - __str__ is for end-users (print, logging)
        - __repr__ is for developers (debugging)
        """
        return f"{self.APP_NAME} v{self.APP_VERSION}"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# ── SINGLETON PATTERN ────────────────────────────────────────
# Module-level instance — Python's idiomatic singleton.
# The module is loaded once and cached by Python's import system,
# so 'settings' is created exactly once and reused everywhere.
settings = Settings()
