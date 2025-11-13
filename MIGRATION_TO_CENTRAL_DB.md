# Migratie naar Centrale Database

**Datum:** 2025-11-13
**Status:** ✅ Compleet

## Wijzigingen

### 1. Docker Compose Configuratie

**Voor:**
- Eigen PostgreSQL container (postgres:15-alpine)
- Eigen Redis container (redis:7-alpine)
- Eigen netwerk (userprofile-network)
- Port 8000

**Na:**
- ✅ Gebruikt centrale `activity-postgres-db` container
- ✅ Gebruikt gedeelde `auth-redis` container
- ✅ Gebruikt `activity-network` netwerk
- ✅ Port 8008 (om conflicten te voorkomen)

### 2. Database Configuratie

**Database URL:**
```
postgresql://postgres:postgres_secure_password_change_in_prod@activity-postgres-db:5432/activitydb
```

**Belangrijke punten:**
- Host: `activity-postgres-db` (centrale database container)
- Database: `activitydb` (met alle 40 tabellen)
- Schema: `activity` (automatisch via migraties)
- User: `postgres`
- Password: `postgres_secure_password_change_in_prod`
- Connection pool: 10-20 connections

### 3. Redis Configuratie

**Redis URL:**
```
redis://auth-redis:6379/0
```

Gebruikt dezelfde Redis instance als andere APIs voor:
- **DB 0**: Caching (user profiles, settings, interests)
- **DB 1**: Rate limiting

**Cache TTL configuratie:**
- User profiles: 300s (5 minuten)
- User settings: 1800s (30 minuten)
- User interests: 3600s (1 uur)

### 4. Netwerk Configuratie

Gebruikt `activity-network` external network:
- Alle activity services in zelfde netwerk
- Direct communicatie tussen services
- Geen port mapping conflicts

### 5. Container Naam

Container naam: `userprofile-api`
- Makkelijk te identificeren
- Consistent met andere services
- Gebruikt in logs en monitoring

## Database Schema

De userprofile-api gebruikt tabellen uit het centrale schema:

**User Tabellen:**
- `users` (34 kolommen) - Complete user profiles
- `user_settings` (14 kolommen) - User preferences & privacy
- `user_interests` (4 kolommen) - Activity interests
- `user_locations` (7 kolommen) - Preferred locations
- `user_blocks` (5 kolommen) - Blocked users
- `user_reports` (8 kolommen) - User reports

**Social Tabellen:**
- `friendships` (7 kolommen) - Friend connections
- `user_badges` (7 kolommen) - Achievement badges

## Deployment

### Starten

```bash
cd /mnt/d/activity/userprofile-api
docker compose build
docker compose up -d
```

### Logs Checken

```bash
docker compose logs -f userprofile-api
```

### Health Check

```bash
curl http://localhost:8008/health
```

### Stoppen

```bash
docker compose down
```

## Belangrijke Opmerkingen

1. **Geen eigen database meer** - Alle data in centrale database
2. **Gedeelde Redis** - Caching (DB 0) en rate limiting (DB 1)
3. **Port 8008** - Om conflict met andere APIs te voorkomen
4. **External network** - Moet `activity-network` netwerk bestaan
5. **Multi-layer caching** - Verschillende TTL per data type
6. **Service-to-service auth** - API keys voor interne communicatie

## Port Overzicht

| Service | Port | Functie |
|---------|------|---------|
| auth-api | 8000 | Authenticatie & gebruikers |
| moderation-api | 8002 | Content moderatie |
| community-api | 8003 | Communities & posts |
| participation-api | 8004 | Activity deelname |
| social-api | 8005 | Social features |
| notifications-api | 8006 | Notificaties |
| activity-api | 8007 | Activity CRUD & geo-search |
| userprofile-api | 8008 | User profiles & settings |

## Verificatie

Checklist na deployment:
- [ ] Container start zonder errors
- [ ] Database connectie succesvol
- [ ] Redis connectie succesvol (DB 0 + DB 1)
- [ ] Health endpoint reageert
- [ ] Auth-API communicatie werkt
- [ ] Profile endpoints werken
- [ ] Caching werkt (check Redis)
- [ ] Rate limiting werkt

## Rollback

Als er problemen zijn:
```bash
cd /mnt/d/activity/userprofile-api
docker compose down
# Fix issues
docker compose up -d
```

---

**Status:** ✅ Klaar voor gebruik met centrale database en Redis caching
