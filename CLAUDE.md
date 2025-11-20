# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**User Profile API** is a FastAPI-based microservice managing complete user lifecycle operations including profiles, photos, interests, settings, subscriptions, verification, and moderation. Part of the Activity Platform monorepo using PostgreSQL (stored procedures pattern), Redis caching, and centralized observability.

**Port**: 8008 (external) → 8000 (container)

## Critical Architecture Patterns

### Stored Procedure Architecture

**ALL database operations** use PostgreSQL stored procedures in the `activity` schema. Never write raw SQL queries in Python code.

**Pattern**:
1. Database team owns all stored procedures in `database/stored_procedures.sql` (23 procedures, 1008 lines)
2. Python services call procedures via `db.fetch_one()` or `db.fetch_all()`
3. Services transform database results into Pydantic schemas

**Example**:
```python
# In service layer (app/services/profile_service.py)
async def get_user_profile(self, user_id: UUID, requesting_user_id: UUID):
    result = await db.fetch_one(
        "SELECT * FROM activity.sp_get_user_profile($1, $2)",
        user_id,
        requesting_user_id
    )
    return UserProfileResponse(**result) if result else None
```

**Available Stored Procedures** (prefix: `activity.sp_`):
- Profile: `get_user_profile`, `update_user_profile`, `update_username`, `delete_user_account`
- Photos: `set_main_photo`, `add_profile_photo`, `remove_profile_photo`, `moderate_main_photo`, `get_pending_photo_moderations`
- Interests: `set_user_interests`, `add_user_interest`, `remove_user_interest`
- Settings: `get_user_settings`, `update_user_settings`
- Subscription: `update_subscription`, `set_captain_status`
- Verification: `increment_verification_count`, `increment_no_show_count`, `update_activity_counts`
- Search: `search_users`
- Moderation: `ban_user`, `unban_user`, `moderate_main_photo`
- Activity: `update_last_seen`

### Service Layer Architecture

**Structure**: Routes → Services → Database (stored procedures)

Each domain has its own service class:
- `ProfileService` - Profile CRUD operations
- `PhotoService` - Photo management, moderation integration
- `InterestService` - Interest tags management
- `SettingsService` - User settings (privacy, notifications, preferences)
- `SubscriptionService` - Subscription tiers, Captain program
- `VerificationService` - Trust scores, verification tracking
- `SearchService` - User search with filters
- `ModerationService` - Admin moderation operations

**Service Pattern**:
```python
class ProfileService:
    """Profile management service."""

    async def get_user_profile(self, user_id: UUID, requesting_user_id: UUID):
        """Get profile using stored procedure."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_get_user_profile($1, $2)",
            user_id,
            requesting_user_id
        )
        return transform_result(result)
```

### JWT Authentication Pattern

**Critical**: All endpoints (except health check) require JWT authentication from auth-api.

**JWT_SECRET_KEY MUST match auth-api exactly** - Token validation fails if secrets differ.

```python
# app/core/security.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """
    Decode JWT and extract user information.
    Raises 401 if token invalid or expired.
    """
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    return TokenPayload(
        user_id=UUID(payload["sub"]),
        ghost_mode=payload.get("ghost_mode", False)
    )
```

**Service-to-Service Authentication**:
- Internal service calls use API keys (e.g., `MODERATION_API_KEY`, `PAYMENT_API_KEY`)
- Validation via `validate_service_api_key()` dependency

### External Service Integration

**Image API Integration** (`app/services/photo_service.py`):
```python
# Upload photo to image-api
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{settings.IMAGE_API_URL}/api/v1/upload",
        headers={"Authorization": f"Bearer {jwt_token}"},
        files={"file": image_file}
    )
```

**Moderation API Integration** (photo approval workflow):
- When user sets main photo → Calls moderation-api for content review
- Stores moderation status in database
- Admin endpoints for photo approval/rejection

## Common Development Tasks

### Starting the Service

**Prerequisites**: Infrastructure must be running first (PostgreSQL, Redis).

```bash
# 1. Start infrastructure (from monorepo root)
./scripts/start-infra.sh

# 2. Verify infrastructure
docker ps | grep -E "activity-postgres-db|auth-redis"

# 3. Start userprofile-api
cd userprofile-api
docker compose up -d

# Or run locally without Docker
export $(cat .env | xargs)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Changes Workflow

**CRITICAL**: Docker restart does NOT pick up code changes. Always rebuild:

```bash
# After any code changes
docker compose build userprofile-api --no-cache
docker compose restart userprofile-api

# Verify new code is running
docker logs userprofile-api --tail 50
```

### Database Operations

**Schema Initialization**:
```bash
# Initialize schema (run once)
docker exec -i activity-postgres-db psql -U postgres -d activitydb < sqlschema.sql

# Deploy stored procedures
docker exec -i activity-postgres-db psql -U postgres -d activitydb < database/stored_procedures.sql
```

**Connecting to Database**:
```bash
# Interactive psql session
docker exec -it activity-postgres-db psql -U postgres -d activitydb

# Check schema objects
\dn                          # List schemas
\dt activity.*               # List tables in activity schema
\df activity.sp_*            # List stored procedures

# Test stored procedure
SELECT * FROM activity.sp_get_user_profile(
    'user-uuid-here'::uuid,
    'requesting-user-uuid'::uuid
);
```

**Modifying Stored Procedures**:
1. Edit `database/stored_procedures.sql`
2. Deploy changes: `docker exec -i activity-postgres-db psql -U postgres -d activitydb < database/stored_procedures.sql`
3. Test via Python service or direct psql call

### Testing

**No test suite yet** - Tests directory exists but empty.

**Manual Testing**:
```bash
# Generate test JWT token (15 min expiry)
python3 -c "
import jwt
from datetime import datetime, timedelta
from uuid import uuid4

secret = 'your_very_long_secret_key_at_least_32_characters'
payload = {
    'sub': str(uuid4()),
    'exp': datetime.utcnow() + timedelta(minutes=15),
    'ghost_mode': False
}
print(jwt.encode(payload, secret, algorithm='HS256'))
"

# Use token in requests
export TOKEN="<generated-token>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8008/api/v1/users/me
```

**API Documentation**:
- Swagger UI: http://localhost:8008/docs (development only)
- ReDoc: http://localhost:8008/redoc (development only)

### Monitoring & Debugging

**Health Check**:
```bash
curl http://localhost:8008/health
# Returns: database, cache, API status
```

**Logs**:
```bash
# Follow logs
docker logs -f userprofile-api

# Search for errors
docker logs userprofile-api 2>&1 | grep -i error

# Structured logging enabled (JSON format)
docker logs userprofile-api 2>&1 | jq .
```

**Metrics** (Prometheus):
```bash
# Scrape endpoint
curl http://localhost:8008/metrics
```

## Configuration Management

### Environment Variables

**Critical Settings** (must match across services):
- `JWT_SECRET_KEY` - MUST match auth-api exactly (token validation fails otherwise)
- `DATABASE_URL` - Points to centralized `activity-postgres-db`
- `REDIS_URL` - Shared Redis instance (note: uses `auth-redis` container name)

**Service URLs**:
- `IMAGE_API_URL` - http://image-api:8002
- `EMAIL_API_URL` - http://email-api:8000
- `AUTH_API_URL` - http://auth-api:8000

**Feature Flags**:
- `RATE_LIMIT_ENABLED` - Enable slowapi rate limiting (default: true)
- `CACHE_ENABLED` - Enable Redis caching (default: true)
- `ENABLE_METRICS` - Enable Prometheus metrics (default: true)

**Cache TTL Configuration** (seconds):
- `CACHE_TTL_USER_PROFILE` - 300 (5 minutes)
- `CACHE_TTL_USER_SETTINGS` - 1800 (30 minutes)
- `CACHE_TTL_USER_INTERESTS` - 3600 (1 hour)

### CORS Configuration

**Development**: Fully open (allow_origins=["*"])
**Production**: Restricted to `CORS_ORIGINS` list

## Route Organization

**Route Registration Order Matters**:
```python
# main.py - search MUST come before profile to avoid /search matching /{user_id}
app.include_router(search.router)       # /api/v1/users/search
app.include_router(profile.router)      # /api/v1/users/{user_id}
```

**Endpoint Groups**:
- `/api/v1/users/me` - Current user's profile operations
- `/api/v1/users/{user_id}` - Public profile viewing
- `/api/v1/users/search` - User search with filters
- `/api/v1/photos` - Photo management
- `/api/v1/interests` - Interest tags
- `/api/v1/settings` - Privacy & notification settings
- `/api/v1/subscription` - Subscription & Captain status
- `/api/v1/verification` - Trust score tracking
- `/api/v1/heartbeat` - Last seen updates
- `/api/v1/moderation` - Admin operations (photo approval, bans)
- `/api/v1/captain` - Captain program operations

## Troubleshooting

### JWT Validation Failures

**Symptom**: 401 Unauthorized errors
**Cause**: JWT_SECRET_KEY mismatch between auth-api and userprofile-api

```bash
# Check secrets match
cat /mnt/d/activity/auth-api/.env | grep JWT_SECRET_KEY
cat /mnt/d/activity/userprofile-api/.env | grep JWT_SECRET_KEY
# MUST be identical
```

### Database Connection Errors

**Symptom**: "could not connect to server"
**Solution**:
```bash
# Verify PostgreSQL is running
docker ps | grep activity-postgres-db

# Check connection from container
docker exec userprofile-api pg_isready -h activity-postgres-db -p 5432
```

### Redis Connection Errors

**Symptom**: Cache/rate limit failures
**Solution**:
```bash
# Verify Redis is running
docker ps | grep auth-redis

# Test connection
docker exec auth-redis redis-cli ping
# Expected: PONG
```

### Code Changes Not Applied

**Symptom**: Changes don't appear after restart
**Solution**: Always rebuild, never just restart
```bash
docker compose build userprofile-api --no-cache
docker compose restart userprofile-api
```

### Stored Procedure Errors

**Symptom**: Database query failures
**Debug**:
```bash
# Check procedure exists
docker exec -it activity-postgres-db psql -U postgres -d activitydb -c "\df activity.sp_get_user_profile"

# Test procedure directly
docker exec -it activity-postgres-db psql -U postgres -d activitydb
SELECT * FROM activity.sp_get_user_profile(
    '00000000-0000-0000-0000-000000000000'::uuid,
    '00000000-0000-0000-0000-000000000000'::uuid
);
```

## Development Workflow

### Adding New Endpoint

1. **Create/update stored procedure** in `database/stored_procedures.sql`
2. **Deploy procedure**: `docker exec -i activity-postgres-db psql -U postgres -d activitydb < database/stored_procedures.sql`
3. **Add Pydantic schemas** in `app/schemas/<domain>.py`
4. **Add service method** in `app/services/<domain>_service.py`
5. **Add route handler** in `app/routes/<domain>.py`
6. **Test** via Swagger UI or curl
7. **Rebuild container**: `docker compose build --no-cache && docker compose restart`

### Adding External Service Integration

1. **Add service URL** to `.env` (e.g., `NEW_SERVICE_URL`)
2. **Add to config.py** as Field
3. **Create service client** in `app/services/` using httpx.AsyncClient
4. **Add authentication** (JWT or API key)
5. **Handle errors** appropriately (service unavailable, timeouts)

## Security Considerations

- **JWT_SECRET_KEY**: Never commit actual secrets, use strong random values in production
- **API Keys**: Rotate service-to-service API keys regularly
- **Database**: Never expose stored procedure logic to frontend
- **Rate Limiting**: Enabled by default, uses Redis for distributed limiting
- **CORS**: Fully open in development, restricted in production
- **Logging**: Structured JSON logs avoid PII leakage

## Dependencies

**Core**:
- FastAPI - Web framework
- asyncpg - PostgreSQL async driver
- pydantic/pydantic-settings - Configuration & validation
- python-jose - JWT handling
- redis - Caching & rate limiting

**Middleware**:
- slowapi - Rate limiting
- prometheus-fastapi-instrumentator - Metrics
- httpx - HTTP client for service-to-service calls

**Monitoring**:
- structlog - Structured logging
- prometheus_client - Metrics exposition
