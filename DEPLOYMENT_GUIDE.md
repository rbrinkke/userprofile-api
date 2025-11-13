# 🚀 User Profile API - Complete Deployment Guide

**Status**: ✅ Database configured | ✅ Stored Procedures installed | ⚠️ Code fixes needed

## Current Deployment Status

### ✅ Completed
1. **Database Schema** - All tables, enums, and constraints exist in `activitydb.activity`
2. **Stored Procedures** - All 23 procedures successfully deployed
3. **Environment Configuration** - `.env` file correctly configured with Docker hostnames
4. **JWT Secret Synchronization** - Matched with auth-api

### ⚠️ Known Issues Found & Fixed

#### Issue 1: Pydantic v2 Compatibility
**Problem**: `regex` parameter removed in Pydantic v2
```python
# OLD (broken):
new_username: str = Field(..., regex=r"^[a-zA-Z0-9_]{3,30}$")

# FIXED:
new_username: str = Field(..., pattern=r"^[a-zA-Z0-9_]{3,30}$")
```
**Status**: ✅ Fixed in `app/schemas/profile.py`

#### Issue 2: Slowapi Rate Limiter
**Problem**: Rate limiter decorators on routes require `Request` parameter
**Impact**: Prevents application startup
**Solution Required**: Remove individual route limiters, use app-level limiter

---

## 📋 Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] PostgreSQL running (`activity-postgres-db`)
- [ ] Redis running (`auth-redis`)
- [ ] Docker network `activity-network` exists
- [ ] Auth-API running (for JWT token issuance)

### Database Verification
```bash
# Check database connectivity
docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT 1;"

# Verify schema exists
docker exec activity-postgres-db psql -U postgres -d activitydb -c "\dn"

# Count stored procedures (should be 23)
docker exec activity-postgres-db psql -U postgres -d activitydb -c "
SELECT COUNT(*) FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'activity'
AND proname IN ('sp_get_user_profile', 'sp_update_user_profile',
                'sp_update_username', 'sp_set_main_photo',
                'sp_add_profile_photo', 'sp_remove_profile_photo',
                'sp_set_user_interests', 'sp_add_user_interest',
                'sp_remove_user_interest', 'sp_get_user_settings',
                'sp_update_user_settings', 'sp_update_subscription',
                'sp_set_captain_status', 'sp_increment_verification_count',
                'sp_increment_no_show_count', 'sp_update_activity_counts',
                'sp_search_users', 'sp_update_last_seen',
                'sp_ban_user', 'sp_unban_user',
                'sp_moderate_main_photo', 'sp_get_pending_photo_moderations',
                'sp_delete_user_account');"
```

### Configuration Verification
```bash
# Verify JWT secret matches auth-api
docker exec auth-api env | grep JWT_SECRET_KEY
cat .env | grep JWT_SECRET_KEY
# These MUST be identical!

# Check database URL
cat .env | grep DATABASE_URL
# Should be: postgresql://postgres:postgres_secure_password_change_in_prod@activity-postgres-db:5432/activitydb

# Check Redis URL
cat .env | grep REDIS_URL
# Should be: redis://auth-redis:6379/0
```

---

## 🔧 Deployment Steps

### Step 1: Fix Remaining Code Issues

**Remove duplicate limiter instances from routes**:
The main app already has a global limiter. Individual route limiters cause conflicts.

Files to check:
- `app/routes/profile.py`
- `app/routes/photos.py`
- `app/routes/interests.py`
- `app/routes/settings.py`
- `app/routes/subscription.py`
- `app/routes/captain.py`
- `app/routes/verification.py`
- `app/routes/search.py`
- `app/routes/heartbeat.py`
- `app/routes/moderation.py`

**Action**: Remove limiter imports and decorators, use app-level limiter from `app.main`

### Step 2: Build Docker Image
```bash
cd /mnt/d/activity/userprofile-api

# Build without cache to ensure all changes are included
docker compose build --no-cache userprofile-api

# Verify build succeeded
docker images | grep userprofile-api
```

### Step 3: Start Container
```bash
# Start in detached mode
docker compose up -d userprofile-api

# Check if container is running
docker ps | grep userprofile-api

# Monitor logs for startup
docker compose logs -f userprofile-api
```

### Step 4: Health Check
```bash
# Wait 10 seconds for startup
sleep 10

# Check health endpoint
curl http://localhost:8008/health

# Expected response:
# {
#   "status": "healthy",
#   "environment": "development",
#   "version": "1.0.0",
#   "checks": {
#     "api": "ok",
#     "database": "ok",
#     "cache": "ok"
#   }
# }
```

### Step 5: Test API Endpoints

#### Get JWT Token from Auth API
```bash
# Register user (if needed)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# Login to get JWT token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

#### Test User Profile Endpoint
```bash
# Get own profile
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8008/api/v1/users/me

# Update profile
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Updated",
    "last_name": "Name",
    "profile_description": "Test description"
  }' \
  http://localhost:8008/api/v1/users/me
```

#### Test Interest Management
```bash
# Add interest
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tag": "hiking",
    "weight": 1.0
  }' \
  http://localhost:8008/api/v1/users/me/interests

# Get interests
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8008/api/v1/users/me/interests
```

---

## 🐛 Troubleshooting

### Container Won't Start

**Check logs**:
```bash
docker compose logs userprofile-api
```

**Common issues**:
1. **Database connection failed**
   - Verify PostgreSQL is running: `docker ps | grep postgres`
   - Check DATABASE_URL in `.env`

2. **Redis connection failed**
   - Verify Redis is running: `docker ps | grep redis`
   - Check REDIS_URL in `.env`

3. **Import errors**
   - Rebuild without cache: `docker compose build --no-cache userprofile-api`

### JWT Validation Fails

**Symptoms**: `401 Unauthorized` on all endpoints

**Check**:
```bash
# Compare JWT secrets
docker exec auth-api env | grep JWT_SECRET_KEY
cat .env | grep JWT_SECRET_KEY
```

**Fix**: Update `.env` with exact JWT_SECRET_KEY from auth-api, then rebuild.

### Stored Procedure Not Found

**Symptom**: Database errors mentioning missing function

**Verify**:
```bash
docker exec activity-postgres-db psql -U postgres -d activitydb -c "\df activity.sp_*" | grep sp_get_user_profile
```

**Fix**: Redeploy stored procedures:
```bash
docker exec -i activity-postgres-db psql -U postgres -d activitydb < database/stored_procedures.sql
```

### Rate Limiting Errors

**Symptom**: `Exception: No "request" or "websocket" argument on function`

**Cause**: Individual route limiters conflict with app-level limiter

**Fix**: Remove `@limiter.limit()` decorators from route files

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Container is running: `docker ps | grep userprofile-api`
- [ ] Health endpoint responds: `curl http://localhost:8008/health`
- [ ] Database connection works (check health response)
- [ ] Redis connection works (check health response)
- [ ] Can get own profile with JWT token
- [ ] Can update profile
- [ ] Can manage interests
- [ ] Can manage settings
- [ ] Logs show no errors: `docker compose logs userprofile-api | grep ERROR`
- [ ] Prometheus metrics available: `curl http://localhost:8008/metrics`

---

## 📊 Monitoring

### View Logs
```bash
# All logs
docker compose logs -f userprofile-api

# Error logs only
docker compose logs userprofile-api | grep ERROR

# Last 100 lines
docker compose logs --tail 100 userprofile-api
```

### Check Metrics
```bash
# Prometheus metrics
curl http://localhost:8008/metrics

# Filter for HTTP metrics
curl http://localhost:8008/metrics | grep http_requests
```

### Database Monitoring
```bash
# Check active connections
docker exec activity-postgres-db psql -U postgres -d activitydb -c "
SELECT count(*) FROM pg_stat_activity
WHERE datname = 'activitydb' AND application_name LIKE 'asyncpg%';"

# Check stored procedure usage
docker exec activity-postgres-db psql -U postgres -d activitydb -c "
SELECT schemaname, funcname, calls
FROM pg_stat_user_functions
WHERE schemaname = 'activity'
ORDER BY calls DESC
LIMIT 10;"
```

---

## 🔐 Production Deployment Checklist

Before deploying to production:

- [ ] Change `ENVIRONMENT=production` in `.env`
- [ ] Set `DEBUG=false`
- [ ] Generate strong JWT_SECRET_KEY (64+ chars)
- [ ] Change all service API keys
- [ ] Update DATABASE_URL to managed PostgreSQL
- [ ] Update REDIS_URL to managed Redis
- [ ] Configure proper CORS_ORIGINS
- [ ] Set LOG_LEVEL=INFO or WARNING
- [ ] Set LOG_FORMAT=json
- [ ] Configure Sentry DSN for error tracking
- [ ] Setup SSL/TLS termination
- [ ] Configure health check monitoring
- [ ] Setup automated backups
- [ ] Test failover scenarios

---

## 📞 Support

**Issues Found**:
1. ✅ Pydantic v2 `regex` → `pattern` - FIXED
2. ✅ JWT secret mismatch - FIXED
3. ⚠️ Slowapi limiter conflicts - NEEDS FIX
4. ✅ All 23 stored procedures deployed - VERIFIED

**Next Steps**:
1. Fix slowapi limiter decorators in routes
2. Rebuild and test
3. Verify all 28 endpoints work correctly
4. Load testing with multiple concurrent requests
