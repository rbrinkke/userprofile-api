"""
Main FastAPI application for User Profile API.
Handles startup/shutdown, middleware configuration, and route registration.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.core.cache import cache
from app.core.database import db
from app.core.exceptions import APIException
from app.core.logging_config import setup_logging, get_logger
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.error_handler import (
    api_exception_handler,
    generic_exception_handler,
    rate_limit_exceeded_handler,
)

# Initialize structured logging
setup_logging()
logger = get_logger(__name__)


# ============================================================================
# Application Lifecycle
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_starting",
        environment=settings.ENVIRONMENT,
        project=settings.PROJECT_NAME,
        version=settings.API_VERSION,
    )

    try:
        # Connect to database
        await db.connect()
        logger.info("database_initialized")

        # Connect to Redis cache
        await cache.connect()
        logger.info("cache_initialized")

        logger.info("application_ready")

    except Exception as e:
        logger.error("application_startup_failed", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("application_shutting_down")

    try:
        await db.disconnect()
        await cache.disconnect()
        logger.info("application_stopped")

    except Exception as e:
        logger.error("application_shutdown_failed", error=str(e))


# ============================================================================
# FastAPI Application Instance
# ============================================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="User Profile API - Complete user lifecycle management with profiles, photos, interests, settings, and verification",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-ID"],
)

# Correlation ID middleware
app.add_middleware(CorrelationMiddleware)

# ============================================================================
# Rate Limiting
# ============================================================================


def get_client_ip(request) -> str:
    """
    Get real client IP address, handling proxies and load balancers.

    Checks X-Forwarded-For header first (for proxied requests),
    falls back to direct client IP.
    """
    # Check X-Forwarded-For header (set by proxies/load balancers)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # First IP is the original client
        return forwarded.split(",")[0].strip()

    # Fallback to direct connection IP
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(
    key_func=get_client_ip,
    storage_uri=f"{settings.REDIS_URL}/{settings.REDIS_RATE_LIMIT_DB}",
    enabled=settings.RATE_LIMIT_ENABLED,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ============================================================================
# Exception Handlers
# ============================================================================

app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ============================================================================
# Metrics & Monitoring
# ============================================================================

if settings.ENABLE_METRICS:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    logger.info("prometheus_metrics_enabled")

# ============================================================================
# Health Check Endpoint
# ============================================================================


@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Checks:
    - API status
    - Database connectivity
    - Redis cache connectivity

    Returns:
        200 OK if all systems operational
        503 Service Unavailable if any system is down
    """
    checks = {
        "api": "ok",
        "database": "ok" if await db.health_check() else "error",
        "cache": "ok" if await cache.health_check() else "error",
    }

    all_ok = all(status == "ok" for status in checks.values())
    status_code = 200 if all_ok else 503

    return {
        "status": "healthy" if all_ok else "degraded",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION,
        "checks": checks,
    }


# ============================================================================
# Route Registration
# ============================================================================

# Import routers (will be created next)
from app.routes import (
    profile,
    photos,
    interests,
    settings as settings_router,
    subscription,
    captain,
    verification,
    search,
    heartbeat,
    moderation,
)

# Register routers with API version prefix
app.include_router(profile.router, prefix=settings.API_V1_PREFIX, tags=["Profile Management"])
app.include_router(photos.router, prefix=settings.API_V1_PREFIX, tags=["Photo Management"])
app.include_router(interests.router, prefix=settings.API_V1_PREFIX, tags=["Interest Tags"])
app.include_router(settings_router.router, prefix=settings.API_V1_PREFIX, tags=["User Settings"])
app.include_router(subscription.router, prefix=settings.API_V1_PREFIX, tags=["Subscription Management"])
app.include_router(captain.router, prefix=settings.API_V1_PREFIX, tags=["Captain Program"])
app.include_router(verification.router, prefix=settings.API_V1_PREFIX, tags=["Trust & Verification"])
app.include_router(search.router, prefix=settings.API_V1_PREFIX, tags=["User Search"])
app.include_router(heartbeat.router, prefix=settings.API_V1_PREFIX, tags=["Activity Tracking"])
app.include_router(moderation.router, prefix=settings.API_V1_PREFIX, tags=["Admin Moderation"])

# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_PREFIX}/docs" if settings.is_development else "disabled",
    }


logger.info(
    "application_configured",
    cors_origins=settings.CORS_ORIGINS,
    rate_limiting=settings.RATE_LIMIT_ENABLED,
    caching=settings.CACHE_ENABLED,
)
