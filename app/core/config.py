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
        default="sqlite:///./cms.db",
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

    # ── Email ────────────────────────────────────────────────
    MAIL_USERNAME: str = Field(default="info.educorecms@gmail.com", description="SMTP Username")
    MAIL_PASSWORD: str = Field(default="", description="SMTP App Password")

    # ── Class-level configuration ────────────────────────────
    model_config = {
        "env_file": ".env",
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
            DATABASE_URL="sqlite:///./test_cms.db",
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


# ── SINGLETON PATTERN ────────────────────────────────────────
# Module-level instance — Python's idiomatic singleton.
# The module is loaded once and cached by Python's import system,
# so 'settings' is created exactly once and reused everywhere.
settings = Settings()
