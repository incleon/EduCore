"""
Audit Middleware — Request/Response Logging
=============================================

Logs every incoming request for monitoring and debugging.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging_config import get_logger

logger = get_logger("middleware.audit")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs request details and response times.

    OOP Concept: INHERITANCE (extends BaseHTTPMiddleware)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Log request
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"| Client: {request.client.host if request.client else 'unknown'}"
        )

        response = await call_next(request)

        # Calculate duration
        duration = round((time.time() - start_time) * 1000, 2)

        logger.info(
            f"← {request.method} {request.url.path} "
            f"| Status: {response.status_code} | Duration: {duration}ms"
        )

        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        return response
