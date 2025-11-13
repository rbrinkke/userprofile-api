"""
Correlation ID middleware for request tracing.
Adds correlation IDs to all requests and responses for distributed tracing.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import structlog

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to all requests.

    - Reads X-Trace-ID from request headers (if provided by client/gateway)
    - Generates new UUID if not provided
    - Binds correlation_id to structlog context (appears in all logs)
    - Adds X-Trace-ID to response headers
    """

    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Trace-ID") or request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Bind to structlog context (all logs in this request will include it)
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        # Process request
        response: Response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Trace-ID"] = correlation_id

        # Clear context after request
        structlog.contextvars.clear_contextvars()

        return response
