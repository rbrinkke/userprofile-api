# User Profile API - Quick Start Guide

## 🚀 Launch the Complete API in 60 Seconds

### Prerequisites
- Docker and Docker Compose installed
- That's it!

### Start Everything

```bash
# Clone and enter directory
cd userprofile-api

# Start all services (API, PostgreSQL, Redis)
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Verify It's Running

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "environment": "development",
  "version": "1.0.0",
  "checks": {
    "api": "ok",
    "database": "ok",
    "cache": "ok"
  }
}

# API documentation
open http://localhost:8000/docs  # Swagger UI
open http://localhost:8000/redoc # ReDoc
```

## 📊 What's Included

### Services Running
- **API Server**: http://localhost:8000
- **PostgreSQL**: localhost:5432
  - Database: `activity`
  - User: `activity_user`
  - Password: `activity_password`
- **Redis**: localhost:6379
  - DB 0: Cache
  - DB 1: Rate limiting

### Database State
- ✅ Full schema created (30+ tables)
- ✅ All 23 stored procedures deployed
- ✅ Indexes optimized
- ✅ Ready for use

## 🧪 Test the API

### 1. Get JWT Token (from auth-api)

You need a valid JWT token from your auth-api. The token should include:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "subscription_level": "premium",
  "ghost_mode": false,
  "exp": 1704067200
}
```

### 2. Make Your First Request

```bash
# Set your token
export TOKEN="your-jwt-token-here"

# Get user profile
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users/me

# Update profile
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "profile_description": "Tech enthusiast and outdoor lover"
  }' \
  http://localhost:8000/api/v1/users/me

# Add interests
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tag": "hiking",
    "weight": 1.0
  }' \
  http://localhost:8000/api/v1/users/me/interests

# Search users
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/users/search?q=john&limit=10"
```

### 3. Service-to-Service Calls

```bash
# Increment verification count (requires service API key)
curl -X POST \
  -H "X-Service-API-Key: dev-participation-key" \
  http://localhost:8000/api/v1/users/{user_id}/verify

# Update activity counters
curl -X POST \
  -H "X-Service-API-Key: dev-activities-key" \
  -H "Content-Type: application/json" \
  -d '{
    "created_delta": 1,
    "attended_delta": 0
  }' \
  http://localhost:8000/api/v1/users/{user_id}/activity-counters
```

### 4. Admin Operations

```bash
# Admin JWT token with role: "admin"
export ADMIN_TOKEN="your-admin-jwt-token"

# Get pending photo moderations
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/users/photo-moderation

# Approve photo
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}' \
  http://localhost:8000/api/v1/admin/users/{user_id}/photo-moderation

# Ban user
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Repeated policy violations",
    "expires_at": "2024-12-31T23:59:59Z"
  }' \
  http://localhost:8000/api/v1/admin/users/{user_id}/ban
```

## 📈 Monitor the API

### Prometheus Metrics

```bash
# View metrics
curl http://localhost:8000/metrics

# Metrics include:
# - Request duration (p50, p95, p99)
# - Request count by endpoint
# - Error rate by status code
# - Active requests
```

### Logs

```bash
# View structured JSON logs
docker-compose logs -f api

# Filter for errors
docker-compose logs api | jq 'select(.level=="error")'

# Follow specific user's requests (correlation ID)
docker-compose logs api | jq 'select(.correlation_id=="xxx")'
```

### Database Queries

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U activity_user -d activity

# Test stored procedure
SELECT * FROM activity.sp_get_user_profile(
  'user_id_here'::uuid,
  'requesting_user_id_here'::uuid
);

# View all users
SELECT user_id, username, email, subscription_level FROM activity.users;

# Check cache (Redis)
docker-compose exec redis redis-cli

# View cached profile
GET user_profile:user_id_here

# View rate limits
SELECT 1  # Rate limits are in DB 1
```

## 🔧 Development Tips

### Hot Reload (Development)

```bash
# Instead of docker-compose, run locally with hot reload
pip install -r requirements.txt

# Update .env with local PostgreSQL/Redis
# Then run:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov httpx faker

# Run tests
pytest tests/ -v --cov=app

# Generate coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Database Migrations

```bash
# Apply schema changes
docker-compose exec postgres psql -U activity_user -d activity -f /docker-entrypoint-initdb.d/01-schema.sql

# Update stored procedures
docker-compose exec postgres psql -U activity_user -d activity -f /docker-entrypoint-initdb.d/02-stored-procedures.sql
```

### Clear Cache

```bash
# Flush all Redis cache
docker-compose exec redis redis-cli FLUSHDB

# Or clear specific user cache via API
# Cache is automatically invalidated on updates
```

## 🎯 Common Use Cases

### 1. Complete User Onboarding Flow

```bash
# Step 1: User registers (via auth-api) and gets JWT token
# Step 2: Update profile
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1995-06-15",
    "gender": "female"
  }' \
  http://localhost:8000/api/v1/users/me

# Step 3: Upload main photo (first to image-api, then set URL)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"photo_url": "https://cdn.example.com/photos/main.jpg"}' \
  http://localhost:8000/api/v1/users/me/photos/main

# Step 4: Add interests
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interests": [
      {"tag": "yoga", "weight": 1.0},
      {"tag": "meditation", "weight": 0.9},
      {"tag": "hiking", "weight": 0.8}
    ]
  }' \
  http://localhost:8000/api/v1/users/me/interests

# Step 5: Configure settings
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email_notifications": true,
    "push_notifications": true,
    "language": "en",
    "timezone": "America/New_York"
  }' \
  http://localhost:8000/api/v1/users/me/settings
```

### 2. Photo Moderation Workflow

```bash
# Moderator views pending photos
curl -H "Authorization: Bearer $MODERATOR_TOKEN" \
  http://localhost:8000/api/v1/admin/users/photo-moderation

# Moderator approves photo
curl -X POST -H "Authorization: Bearer $MODERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}' \
  http://localhost:8000/api/v1/admin/users/{user_id}/photo-moderation
```

### 3. Subscription Upgrade

```bash
# Payment processor updates subscription
curl -X POST \
  -H "X-Payment-API-Key: dev-payment-key" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_level": "premium",
    "subscription_expires_at": "2025-12-31T23:59:59Z"
  }' \
  http://localhost:8000/api/v1/users/me/subscription
```

## 🛑 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## ⚠️ Production Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET_KEY` to strong random string
- [ ] Update all service API keys
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper PostgreSQL with replication
- [ ] Set up Redis cluster for high availability
- [ ] Configure monitoring (Prometheus + Grafana)
- [ ] Set up log aggregation (ELK/CloudWatch)
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Configure CORS for production domains
- [ ] Review and adjust rate limits
- [ ] Set up alerts for errors/downtime

## 📚 Next Steps

- Read the full [README.md](README.md) for architecture details
- Review API documentation at http://localhost:8000/docs
- Check the [database schema](sqlschema.sql)
- Explore [stored procedures](database/stored_procedures.sql)
- Review security implementation in `app/core/security.py`

## 🆘 Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs api

# Common issues:
# - Database not ready: Wait 10s and retry
# - Port already in use: Change ports in docker-compose.yml
# - Environment variables: Check .env file
```

### Database connection failed

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U activity_user

# Check database exists
docker-compose exec postgres psql -U activity_user -l
```

### Redis connection failed

```bash
# Verify Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

---

**You're all set!** 🎉

The User Profile API is now running and ready to handle requests. Happy coding!
