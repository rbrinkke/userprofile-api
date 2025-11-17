# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**User Profile API** is a FastAPI microservice managing complete user lifecycle including profiles, photos, interests, settings, subscriptions, verification, and moderation. Part of the Activity App microservices architecture.

**Port**: 8008 (external) → 8000 (internal container)

## Technology Stack

- **Framework**: FastAPI 0.109.0 with uvicorn
- **Database**: PostgreSQL 15 (`activitydb.activity` schema) - **STORED PROCEDURES ONLY**
- **Cache**: Redis (DB 0: cache, DB 1: rate limiting)
- **Authentication**: JWT tokens (shared secret with auth-api)
- **Logging**: Structlog with correlation IDs
- **Monitoring**: Prometheus metrics at `/metrics`
- **Container**: Docker Compose with `activity-network`

## Quick Commands

### Starting the Service

```bash
# Docker Compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f userprofile-api

# Rebuild after code changes (CRITICAL)
docker-compose build userprofile-api --no-cache && docker-compose restart userprofile-api

# Manual (local development)
export $(cat .env | xargs)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Health & Monitoring

```bash
# Health check (includes database + Redis status)
curl http://localhost:8008/health

# Prometheus metrics
curl http://localhost:8008/metrics

# API documentation (development only)
open http://localhost:8008/docs
open http://localhost:8008/redoc
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it activity-postgres-db psql -U postgres -d activitydb

# Check user profiles table
\dt activity.user_profiles

# List stored procedures
\df activity.sp_*

# Run stored procedure manually
SELECT * FROM activity.sp_get_user_profile('<user-uuid>', '<requesting-user-uuid>');

# Initialize schema (first time only)
psql -U postgres -d activitydb -f sqlschema.sql
psql -U postgres -d activitydb -f database/stored_procedures.sql
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_profile_service.py -v

# Run single test
pytest tests/test_profile_service.py::test_get_user_profile -v
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### Testing UI

A standalone web-based testing interface is available for manual API testing:

```bash
# Start testing UI (requires userprofile-api to be running)
cd testing_ui
./start.sh

# Access testing interface
open http://localhost:8099/test/userprofile

# View testing UI logs
docker logs -f auth-testing-ui

# Stop testing UI
cd testing_ui && docker compose down
```

The testing UI provides visual testing for all 28 endpoints with features like:
- Auto-fill tokens/IDs from previous responses
- Local storage for session persistence
- Formatted JSON responses with timestamps
- Support for S2S authentication headers
- Real-time validation feedback

See `testing_ui/README.md` for complete documentation.

## Architecture Principles

### 1. Stored Procedure First (CRITICAL)

**ALL database operations MUST go through stored procedures in the `activity` schema.**

Why:
- Database team owns schema evolution
- Supports CQRS architecture (Command Query Responsibility Segregation)
- Easier to audit and optimize
- Can change implementation without changing API

Pattern:
```python
# In service layer (app/services/)
result = await db.fetch_one(
    "SELECT * FROM activity.sp_get_user_profile($1, $2)",
    user_id,
    requesting_user_id
)
```

**NEVER** write raw SQL queries like `SELECT * FROM activity.user_profiles WHERE...`

### 2. Service Layer Pattern

**Three-layer architecture:**

1. **Routes** (`app/routes/`) - Thin HTTP layer
   - Request validation (Pydantic schemas)
   - Authorization checks (JWT dependencies)
   - Rate limiting decorators
   - Response formatting

2. **Services** (`app/services/`) - Business logic
   - Call stored procedures via `db.*` methods
   - Handle cache invalidation
   - Orchestrate multiple operations
   - Transform database results to response models

3. **Core** (`app/core/`) - Shared utilities
   - `database.py` - Connection pool management (asyncpg)
   - `cache.py` - Redis operations
   - `security.py` - JWT validation
   - `logging_config.py` - Structured logging
   - `exceptions.py` - Custom exception classes

Example flow:
```
User Request
  → Route handler (authorization, validation)
    → Service method (business logic)
      → Stored procedure (database operation)
        → Database
      → Cache invalidation
    → Response model
  → JSON response
```

### 3. Dependency Injection

FastAPI's `Depends()` is used extensively:

```python
from app.core.security import get_current_user, require_admin

@router.get("/me")
async def get_my_profile(
    current_user: TokenPayload = Depends(get_current_user),  # JWT validation
):
    # current_user.user_id, current_user.subscription_level, etc.
    ...

@router.post("/admin/users/{user_id}/ban")
async def ban_user(
    user_id: UUID,
    admin: TokenPayload = Depends(require_admin),  # Requires admin role
):
    ...
```

Available dependencies:
- `get_current_user` - Requires valid JWT, returns `TokenPayload`
- `get_optional_user` - Optional JWT (returns None if missing)
- `require_premium` - Requires Premium subscription
- `require_admin` - Requires admin role
- `require_moderator` - Requires moderator or admin role
- `validate_service_api_key` - Service-to-service authentication

### 4. Caching Strategy

**Three cache types with different TTLs:**

- `user_profile:{user_id}` - 5 minutes (300s)
- `user_settings:{user_id}` - 30 minutes (1800s)
- `user_interests:{user_id}` - 1 hour (3600s)

**Cache invalidation** on all updates:

```python
# In service methods
async def update_profile(self, user_id: UUID, updates: dict):
    # Update via stored procedure
    await db.execute("SELECT activity.sp_update_user_profile($1, $2)", user_id, updates)

    # Invalidate ALL user caches
    await cache.invalidate_all_user_caches(user_id)
```

### 5. Structured Logging with Correlation IDs

All requests get a correlation ID for distributed tracing:

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

logger.info("profile_updated",
           user_id=str(user_id),
           fields_updated=list(updates.keys()))

logger.warning("subscription_required",
              user_id=str(user_id),
              current_level=subscription_level,
              required_level="premium")

logger.error("database_error",
            operation="update_profile",
            error=str(e))
```

**Correlation ID** is automatically injected via `CorrelationMiddleware` and appears in all logs for request tracing across services.

### 6. Security & Privacy

**Asymmetric Blocking:**
```python
# Both directions return 404 (no user enumeration)
# Blocker sees: User not found
# Blocked sees: User not found
```

**Ghost Mode (Premium feature):**
- No profile view records created
- Token payload includes `ghost_mode: true`
- Check via `current_user.ghost_mode`

**Generic Error Messages:**
```python
# Right: Prevents information leakage
raise ResourceNotFoundError(resource="User")  # "User not found"

# Wrong: Reveals system internals
raise Exception("User email not verified")  # Information disclosure
```

**Rate Limiting (slowapi):**
```python
from slowapi import Limiter
from app.main import limiter

@router.patch("/me/username")
@limiter.limit("3/hour")  # Aggressive for sensitive operations
async def change_username(...):
    ...

@router.patch("/me")
@limiter.limit("20/minute")  # Standard for updates
async def update_profile(...):
    ...
```

## Critical Development Patterns

### Docker: Always Rebuild After Code Changes

**CRITICAL**: `docker-compose restart` uses the OLD image. You MUST rebuild:

```bash
# Wrong (uses old cached image)
docker-compose restart userprofile-api

# Right (rebuilds with new code)
docker-compose build userprofile-api && docker-compose restart userprofile-api

# Force rebuild without cache (if changes still not appearing)
docker-compose build --no-cache userprofile-api && docker-compose restart userprofile-api
```

Rebuild required after:
- Python code changes
- `requirements.txt` updates
- Environment variable changes in `.env`
- `Dockerfile` modifications

### Shared JWT Secret (CRITICAL)

**ALL services MUST use the same `JWT_SECRET_KEY`:**

```bash
# In .env (MUST match auth-api's JWT_SECRET_KEY)
JWT_SECRET_KEY=dev-secret-key-change-in-production

# Generate secure key for production:
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Services sharing this secret:
- auth-api (issues tokens)
- userprofile-api (validates tokens)
- chat-api (validates tokens)
- activity-api (validates tokens)
- All other microservices

### Service-to-Service Authentication

For endpoints called by other services (not users):

```python
from app.core.security import validate_service_api_key

@router.post("/users/{user_id}/activity-counters")
async def update_activity_counters(
    user_id: UUID,
    counters: ActivityCountersUpdate,
    service: str = Depends(validate_service_api_key),  # Requires X-Service-API-Key header
):
    # service = "activities-api" or "participation-api"
    ...
```

API keys defined in `.env`:
- `ACTIVITIES_API_KEY` - Activities service
- `PARTICIPATION_API_KEY` - Participation service
- `MODERATION_API_KEY` - Moderation service
- `PAYMENT_API_KEY` - Payment processor

### Adding New Stored Procedures

**Process:**

1. Create SQL in `database/stored_procedures.sql`:
```sql
CREATE OR REPLACE FUNCTION activity.sp_new_operation(
    p_user_id UUID,
    p_param VARCHAR
)
RETURNS TABLE (...) AS $$
BEGIN
    -- Implementation
END;
$$ LANGUAGE plpgsql;
```

2. Apply to database:
```bash
docker exec -i activity-postgres-db psql -U postgres -d activitydb < database/stored_procedures.sql
```

3. Create Python wrapper in service:
```python
async def new_operation(self, user_id: UUID, param: str) -> Result:
    result = await db.fetch_one(
        "SELECT * FROM activity.sp_new_operation($1, $2)",
        user_id,
        param
    )
    return Result(**result) if result else None
```

4. Add route handler in `app/routes/`:
```python
@router.post("/new-operation")
async def new_operation_endpoint(
    request: NewOperationRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    result = await service.new_operation(current_user.user_id, request.param)
    return NewOperationResponse.from_db(result)
```

### Adding New API Endpoints

**Step-by-step process:**

1. **Define schemas** in `app/schemas/`:
```python
# app/schemas/new_feature.py
from pydantic import BaseModel
from uuid import UUID

class NewFeatureRequest(BaseModel):
    field1: str
    field2: int

class NewFeatureResponse(BaseModel):
    success: bool
    data: dict
```

2. **Create service method** in `app/services/`:
```python
# app/services/new_feature_service.py
class NewFeatureService:
    async def do_something(self, user_id: UUID, request: NewFeatureRequest):
        # Call stored procedure
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_new_feature($1, $2)",
            user_id,
            request.field1
        )
        return result

new_feature_service = NewFeatureService()
```

3. **Create route handler** in `app/routes/`:
```python
# app/routes/new_feature.py
from fastapi import APIRouter, Depends
from app.core.security import get_current_user, TokenPayload
from app.schemas.new_feature import NewFeatureRequest, NewFeatureResponse
from app.services.new_feature_service import new_feature_service

router = APIRouter()

@router.post("/new-feature", response_model=NewFeatureResponse)
async def new_feature_endpoint(
    request: NewFeatureRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    result = await new_feature_service.do_something(current_user.user_id, request)
    return NewFeatureResponse(success=True, data=result)
```

4. **Register router** in `app/main.py`:
```python
from app.routes import new_feature

app.include_router(new_feature.router, prefix=settings.API_V1_PREFIX, tags=["New Feature"])
```

### Exception Handling

**Use custom exceptions from `app/core/exceptions.py`:**

```python
from app.core.exceptions import (
    ResourceNotFoundError,           # 404
    ResourceDuplicateError,          # 409
    ValidationError,                 # 422
    AuthTokenExpiredError,           # 401
    AuthInsufficientPermissionsError,# 403
    SubscriptionPremiumRequiredError,# 403
)

# Example usage
if not profile:
    raise ResourceNotFoundError(resource="User")

if duplicate_username:
    raise ResourceDuplicateError(resource="Username", value=username)

if not current_user.is_premium:
    raise SubscriptionPremiumRequiredError(current_level=current_user.subscription_level)
```

Exceptions are handled by `app/middleware/error_handler.py` and return standardized JSON responses.

## External Service Integration

### Image API Integration

```python
import httpx
from app.config import settings

async def validate_photo_url(photo_url: str) -> bool:
    """Verify photo URL belongs to our CDN."""
    # Check URL domain matches IMAGE_API_CDN_DOMAIN
    return settings.IMAGE_API_CDN_DOMAIN in photo_url

async def notify_image_api(user_id: UUID, photo_id: str):
    """Notify image-api of profile photo changes."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{settings.IMAGE_API_URL}/api/v1/photos/{photo_id}/profile-updated",
            json={"user_id": str(user_id)},
            timeout=5.0
        )
```

### Email API Integration

```python
async def send_profile_verification_email(user_id: UUID, email: str):
    """Send email via email-api."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{settings.EMAIL_API_URL}/api/v1/emails/send",
            json={
                "to": email,
                "template": "profile_verification",
                "context": {"user_id": str(user_id)}
            },
            timeout=10.0
        )
```

## Configuration Management

### Environment Variables

**Critical settings in `.env`:**

```bash
# Database (matches docker-compose.yml)
DATABASE_URL=postgresql://postgres:postgres_secure_password_change_in_prod@activity-postgres-db:5432/activitydb

# Redis (shared instance)
REDIS_URL=redis://auth-redis:6379/0

# JWT (MUST match auth-api)
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Service API Keys
ACTIVITIES_API_KEY=dev-activities-key
PARTICIPATION_API_KEY=dev-participation-key
MODERATION_API_KEY=dev-moderation-key
PAYMENT_API_KEY=dev-payment-key

# External Services
IMAGE_API_URL=http://image-api:8002
EMAIL_API_URL=http://email-api:8000
AUTH_API_URL=http://auth-api:8000

# Features
RATE_LIMIT_ENABLED=true
CACHE_ENABLED=true
ENABLE_METRICS=true
```

**Access via `app/config.py`:**

```python
from app.config import settings

# Use settings throughout application
jwt_secret = settings.JWT_SECRET_KEY
is_dev = settings.is_development
cache_ttl = settings.CACHE_TTL_USER_PROFILE
```

### Configuration Validation

The configuration uses Pydantic BaseSettings with validators:

```python
# Automatic validation on startup
# - CORS_ORIGINS parsed from JSON string
# - LOG_LEVEL validated against valid levels
# - ENVIRONMENT validated (development/staging/production)
# - Required fields checked (DATABASE_URL, JWT_SECRET_KEY, etc.)
```

If configuration is invalid, the application will fail fast on startup with clear error messages.

## API Endpoints (28 total)

### Profile Management (5)
- `GET /api/v1/users/me` - Own profile
- `GET /api/v1/users/{user_id}` - Public profile (with blocking check)
- `PATCH /api/v1/users/me` - Update profile
- `PATCH /api/v1/users/me/username` - Change username (rate limited: 3/hour)
- `DELETE /api/v1/users/me` - Delete account (rate limited: 1/hour)

### Photo Management (3)
- `POST /api/v1/users/me/photos/main` - Set main photo (requires moderation)
- `POST /api/v1/users/me/photos` - Add extra photo (max 5)
- `DELETE /api/v1/users/me/photos` - Remove photo

### Interest Tags (4)
- `GET /api/v1/users/me/interests` - Get interests
- `PUT /api/v1/users/me/interests` - Replace all (max 20 tags)
- `POST /api/v1/users/me/interests` - Add interest
- `DELETE /api/v1/users/me/interests/{tag}` - Remove interest

### User Settings (2)
- `GET /api/v1/users/me/settings` - Get settings
- `PATCH /api/v1/users/me/settings` - Update settings

### Subscription (2)
- `GET /api/v1/users/me/subscription` - Get subscription
- `POST /api/v1/users/me/subscription` - Update (payment-api only)

### Captain Program (2)
- `POST /api/v1/users/{user_id}/captain` - Grant (admin only)
- `DELETE /api/v1/users/{user_id}/captain` - Revoke (admin only)

### Verification (3)
- `GET /api/v1/users/me/verification` - Trust metrics
- `POST /api/v1/users/{user_id}/verify` - Increment (service only)
- `POST /api/v1/users/{user_id}/no-show` - Increment (service only)

### Activity Counters (1)
- `POST /api/v1/users/{user_id}/activity-counters` - Update (service only)

### Search (1)
- `GET /api/v1/users/search` - Search users (fuzzy username/name)

### Heartbeat (1)
- `POST /api/v1/users/me/heartbeat` - Update last_seen_at

### Moderation (4)
- `GET /api/v1/admin/users/photo-moderation` - Pending photos (admin)
- `POST /api/v1/admin/users/{user_id}/photo-moderation` - Moderate (admin)
- `POST /api/v1/admin/users/{user_id}/ban` - Ban user (admin)
- `DELETE /api/v1/admin/users/{user_id}/ban` - Unban user (admin)

## Troubleshooting

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker ps | grep activity-postgres-db

# Test connection
docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT 1;"

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL
# Should be: postgresql://postgres:password@activity-postgres-db:5432/activitydb
```

### Redis Connection Errors

```bash
# Check Redis is running
docker ps | grep auth-redis

# Test connection
docker exec auth-redis redis-cli ping
# Expected: PONG

# Check REDIS_URL in .env
cat .env | grep REDIS_URL
```

### JWT Validation Failures

```bash
# Verify JWT_SECRET_KEY matches auth-api
cat .env | grep JWT_SECRET_KEY
cat ../auth-api/.env | grep JWT_SECRET_KEY
# MUST be identical

# Test with valid token from auth-api
curl -H "Authorization: Bearer <token>" http://localhost:8008/api/v1/users/me
```

### Code Changes Not Appearing

```bash
# ALWAYS rebuild after code changes
docker-compose build userprofile-api --no-cache
docker-compose restart userprofile-api

# Verify new code is running
docker-compose logs userprofile-api | head -20
```

### Stored Procedure Not Found

```bash
# List stored procedures
docker exec -it activity-postgres-db psql -U postgres -d activitydb -c "\df activity.sp_*"

# Re-apply stored procedures
docker exec -i activity-postgres-db psql -U postgres -d activitydb < database/stored_procedures.sql
```

### Rate Limiting Issues

```bash
# Check Redis rate limit database
docker exec auth-redis redis-cli -n 1 KEYS "*"

# Clear rate limits for testing
docker exec auth-redis redis-cli -n 1 FLUSHDB

# Check if rate limiting is enabled
cat .env | grep RATE_LIMIT_ENABLED
```

### Cache Issues

```bash
# Check Redis cache database
docker exec auth-redis redis-cli -n 0 KEYS "user_*"

# Clear cache for testing
docker exec auth-redis redis-cli -n 0 FLUSHDB

# Verify cache is enabled
cat .env | grep CACHE_ENABLED
```

## Production Deployment

See `PRODUCTION_DEPLOYMENT.md` for comprehensive checklist.

**Critical changes for production:**

```bash
# .env
ENVIRONMENT=production
DEBUG=false

# Change ALL secrets
JWT_SECRET_KEY=<64+ character random string>
ACTIVITIES_API_KEY=<secure random string>
PARTICIPATION_API_KEY=<secure random string>
MODERATION_API_KEY=<secure random string>
PAYMENT_API_KEY=<secure random string>

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Database (use managed PostgreSQL)
DATABASE_URL=postgresql://user:password@production-db-host:5432/activitydb

# Redis (use managed Redis)
REDIS_URL=redis://production-redis-host:6379/0

# CORS
CORS_ORIGINS=["https://app.example.com"]

# Features
RATE_LIMIT_ENABLED=true
CACHE_ENABLED=true
ENABLE_METRICS=true
```

## File Organization Best Practices

- **Tests**: Place in `tests/` directory, matching structure of `app/`
- **Documentation**: User-facing docs in root, Claude-specific in `claudedocs/`
- **Scripts**: Utility scripts in `scripts/` (if any)
- **Never** create `test_*.py` files next to source code
- **Never** create random utility scripts in project root

## Additional Documentation

- `README.md` - Project overview and quick start
- `QUICKSTART.md` - Detailed getting started guide
- `PRODUCTION_DEPLOYMENT.md` - Production deployment checklist
- `SECURITY_AUDIT.md` - Security audit report
- `MIGRATION_TO_CENTRAL_DB.md` - Database migration documentation
- `database/stored_procedures.sql` - All 23 stored procedures with documentation
- `testing_ui/README.md` - Testing UI complete documentation
