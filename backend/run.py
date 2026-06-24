"""
Enterprise College Management System — Entry Point
====================================================

This script starts the FastAPI application using Uvicorn.

OOP Concepts Demonstrated:
- Module-level script execution (__name__ == "__main__")
- Importing and using objects from other modules
"""

import uvicorn
from app.core.config import settings


def main():
    """Start the CMS application server."""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
