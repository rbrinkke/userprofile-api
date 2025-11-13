"""
Global error handling middleware.
Catches unhandled exceptions and returns standardized error responses.
"""
import traceback
import uuid
from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.exceptions import APIException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Handle custom API exceptions.

    Args:
        request: FastAPI request
        exc: API exception

    Returns:
        JSON response with error details
    """
    logger.warning(
        "api_exception",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handle rate limit exceeded errors.

    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception

    Returns:
        JSON response with rate limit error
    """
    logger.warning(
        "rate_limit_exceeded",
        endpoint=request.url.path,
        limit=str(exc.detail),
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "retry_after": 60,  # seconds
                    "limit": str(exc.detail),
                    "endpoint": request.url.path,
                },
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: FastAPI request
        exc: Unhandled exception

    Returns:
        JSON response with generic error
    """
    request_id = str(uuid.uuid4())

    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        traceback=traceback.format_exc(),
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "details": {
                    "request_id": request_id,
                },
            }
        },
    )
