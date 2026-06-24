"""
Global Exception Handlers
===========================

OOP Concepts Demonstrated:
--------------------------
1. POLYMORPHISM: Different handlers for different exception types
2. ASSOCIATION: Handlers are associated with the FastAPI app

Why global exception handlers?
- Consistent error response format across ALL endpoints
- No try/except boilerplate in every route
- Centralized logging of errors
- Clean separation between error definition and error presentation

This module converts our domain exceptions (CMSException hierarchy)
into proper HTTP responses with consistent JSON structure.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import CMSException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    This function demonstrates ASSOCIATION — it associates handler
    functions with the app object without either owning the other.

    Args:
        app: The FastAPI application instance
    """

    @app.exception_handler(CMSException)
    async def cms_exception_handler(request: Request, exc: CMSException) -> JSONResponse:
        """
        Handle all custom CMS exceptions.

        POLYMORPHISM in action: This single handler catches ALL subclasses
        of CMSException (NotFoundException, ForbiddenException, etc.) and
        each exception carries its own status_code and detail.
        """
        logger.warning(
            f"CMS Exception: {exc.error_code} | {exc.detail} | "
            f"Path: {request.url.path} | Method: {request.method}"
        )

        # If it's an HTML request (from browser), redirect to appropriate page
        accept = request.headers.get("accept", "")
        if "text/html" in accept and exc.status_code in (401, 403):
            if exc.status_code == 401:
                return RedirectResponse(url="/login", status_code=302)
            return RedirectResponse(url="/dashboard", status_code=302)

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle standard HTTP exceptions from Starlette/FastAPI."""
        logger.warning(
            f"HTTP Exception: {exc.status_code} | {exc.detail} | "
            f"Path: {request.url.path}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "error_code": "HTTP_ERROR",
                "detail": str(exc.detail),
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors.

        Transforms Pydantic's detailed validation errors into
        our consistent error response format.
        """
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            f"Validation Error: {len(errors)} errors | Path: {request.url.path}"
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "error_code": "VALIDATION_ERROR",
                "detail": "Request validation failed",
                "status_code": 422,
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for unexpected exceptions.

        In production, this prevents stack traces from leaking to clients.
        Always logs the full exception for debugging.
        """
        logger.exception(
            f"Unhandled Exception: {type(exc).__name__} | {str(exc)} | "
            f"Path: {request.url.path}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "detail": "An unexpected error occurred. Please try again later.",
                "status_code": 500,
            },
        )
