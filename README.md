# User Profile API

Complete user lifecycle management API with profiles, photos, interests, settings, subscriptions, and verification.

## Features

- **Profile Management**: Complete user profiles with photo management
- **Interest Tags**: Up to 20 customizable interest tags per user
- **User Settings**: Comprehensive preferences including ghost mode (Premium)
- **Subscription System**: Free/Club/Premium tiers with feature gating
- **Captain Program**: Free Premium for community organizers
- **Trust & Verification**: Peer verification and trust scoring
- **Photo Moderation**: Main photo approval workflow
- **Admin Tools**: User search, moderation queue, ban management

## Technology Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 15 (activity schema)
- **Cache**: Redis 7
- **Authentication**: JWT tokens (HS256)
- **Logging**: Structlog with correlation IDs
- **Monitoring**: Prometheus metrics
- **Rate Limiting**: Redis-based (slowapi)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Access API
curl http://localhost:8000/health
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
psql -U activity_user -d activity -f sqlschema.sql
psql -U activity_user -d activity -f database/stored_procedures.sql

# Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs (development only)
- **ReDoc**: http://localhost:8000/redoc (development only)
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## Architecture

### Project Structure

```
userprofile-api/
├── app/
│   ├── core/           # Core utilities (database, cache, security, logging)
│   ├── middleware/     # Request middleware (correlation, error handling)
│   ├── routes/         # API endpoints (thin HTTP layer)
│   ├── schemas/        # Pydantic models (validation)
│   ├── services/       # Business logic layer
│   ├── config.py       # Centralized configuration
│   └── main.py         # FastAPI application
├── database/
│   └── stored_procedures.sql  # All 23 stored procedures
├── tests/              # Test suite
├── Dockerfile          # Container image
├── docker-compose.yml  # Multi-service orchestration
└── requirements.txt    # Python dependencies
```

### Design Principles

1. **Stored Procedure First**: ALL database operations via stored procedures
2. **Service Layer Pattern**: Business logic separated from HTTP layer
3. **Dependency Injection**: Clean dependencies via FastAPI Depends()
4. **Caching Strategy**: Redis cache with TTL and invalidation
5. **Correlation IDs**: Request tracing across distributed systems
6. **Structured Logging**: JSON logs with context in production

## API Endpoints

### Profile Management (5 endpoints)
- `GET /api/v1/users/me` - Get own profile
- `GET /api/v1/users/{user_id}` - Get public profile
- `PATCH /api/v1/users/me` - Update profile
- `PATCH /api/v1/users/me/username` - Change username
- `DELETE /api/v1/users/me` - Delete account

### Photo Management (3 endpoints)
- `POST /api/v1/users/me/photos/main` - Set main photo
- `POST /api/v1/users/me/photos` - Add extra photo
- `DELETE /api/v1/users/me/photos` - Remove photo

### Interest Tags (4 endpoints)
- `GET /api/v1/users/me/interests` - Get interests
- `PUT /api/v1/users/me/interests` - Replace all interests
- `POST /api/v1/users/me/interests` - Add interest
- `DELETE /api/v1/users/me/interests/{tag}` - Remove interest

### User Settings (2 endpoints)
- `GET /api/v1/users/me/settings` - Get settings
- `PATCH /api/v1/users/me/settings` - Update settings

### Subscription (2 endpoints)
- `GET /api/v1/users/me/subscription` - Get subscription
- `POST /api/v1/users/me/subscription` - Update subscription (payment API)

### Captain Program (2 endpoints)
- `POST /api/v1/users/{user_id}/captain` - Grant captain (admin)
- `DELETE /api/v1/users/{user_id}/captain` - Revoke captain (admin)

### Verification (3 endpoints)
- `GET /api/v1/users/me/verification` - Get trust metrics
- `POST /api/v1/users/{user_id}/verify` - Increment verification (service)
- `POST /api/v1/users/{user_id}/no-show` - Increment no-show (service)

### Activity Counters (1 endpoint)
- `POST /api/v1/users/{user_id}/activity-counters` - Update counters (service)

### Search (1 endpoint)
- `GET /api/v1/users/search` - Search users

### Heartbeat (1 endpoint)
- `POST /api/v1/users/me/heartbeat` - Update last seen

### Moderation (4 endpoints)
- `GET /api/v1/admin/users/photo-moderation` - Pending photos
- `POST /api/v1/admin/users/{user_id}/photo-moderation` - Moderate photo
- `POST /api/v1/admin/users/{user_id}/ban` - Ban user
- `DELETE /api/v1/admin/users/{user_id}/ban` - Unban user

## Security

### Authentication
- JWT tokens from auth-api
- Token validation on all protected endpoints
- Service-to-service API key authentication

### Subscription Gates
- Premium features require subscription validation
- Ghost mode: Premium only
- Profile views: Tracked unless ghost mode

### Privacy
- Asymmetric blocking system
- Blocked users return 404 (no enumeration)
- Ghost mode: No profile view records

### Rate Limiting
- Aggressive: Username change (3/hour), account deletion (1/hour)
- Standard: Profile updates (20/min)
- Read operations: 100/min

## Caching Strategy

- **user_profile:{user_id}** - TTL: 5 minutes
- **user_settings:{user_id}** - TTL: 30 minutes
- **user_interests:{user_id}** - TTL: 1 hour

Cache invalidation on all updates.

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

Returns database and Redis connectivity status.

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

Metrics include:
- Request duration (p50, p95, p99)
- Request count by endpoint
- Error rate by status code
- Database query times

## Development

### Running Tests
```bash
pytest tests/ -v --cov=app
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

## Production Deployment

### Environment Variables

**CRITICAL - Change in production:**
- `JWT_SECRET_KEY` - Use strong random string
- `ACTIVITIES_API_KEY` - Secure service key
- `PARTICIPATION_API_KEY` - Secure service key
- `MODERATION_API_KEY` - Secure service key
- `PAYMENT_API_KEY` - Secure service key

### Database Setup
1. Run `sqlschema.sql` to create schema
2. Run `database/stored_procedures.sql` to create procedures
3. Grant permissions: `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA activity TO activity_user;`

### Recommended Infrastructure
- **API**: 2+ instances behind load balancer
- **Database**: PostgreSQL with replication
- **Cache**: Redis cluster
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK stack or CloudWatch

## License

Proprietary - All rights reserved

## Support

For issues and questions, contact the development team.
