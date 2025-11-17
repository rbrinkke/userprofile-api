# User Profile API Test Script

## Overzicht

`test-userprofile-api.sh` is een uitgebreid test script dat alle 28 endpoints van de User Profile API test met volledige database verificatie.

## Wat test het script?

### Endpoints Coverage (28 totaal)

1. **Profile Management (5)**
   - GET /api/v1/users/me - Ophalen eigen profiel
   - PATCH /api/v1/users/me - Update profiel
   - GET /api/v1/users/{user_id} - Publiek profiel
   - PATCH /api/v1/users/me/username - Username wijzigen
   - DELETE /api/v1/users/me - Account verwijderen (skip in test)

2. **Photo Management (3)**
   - POST /api/v1/users/me/photos/main - Main foto instellen
   - POST /api/v1/users/me/photos - Extra foto toevoegen
   - DELETE /api/v1/users/me/photos - Extra foto verwijderen

3. **Interest Tags (4)**
   - POST /api/v1/users/me/interests - Interest toevoegen
   - GET /api/v1/users/me/interests - Interests ophalen
   - PUT /api/v1/users/me/interests - Bulk replace interests
   - DELETE /api/v1/users/me/interests/{tag} - Interest verwijderen

4. **User Settings (2)**
   - GET /api/v1/users/me/settings - Settings ophalen
   - PATCH /api/v1/users/me/settings - Settings updaten

5. **Subscription Management (2)**
   - GET /api/v1/users/me/subscription - Subscription info
   - POST /api/v1/users/me/subscription - Subscription updaten

6. **Captain Program (2)**
   - POST /api/v1/users/{user_id}/captain - Captain status toekennen (admin)
   - DELETE /api/v1/users/{user_id}/captain - Captain status verwijderen (admin)

7. **Trust & Verification (4)**
   - GET /api/v1/users/me/verification - Verification metrics
   - POST /api/v1/users/{user_id}/verify - Verification increment (S2S)
   - POST /api/v1/users/{user_id}/no-show - No-show increment (S2S)
   - POST /api/v1/users/{user_id}/activity-counters - Activity counters (S2S)

8. **User Search (1)**
   - GET /api/v1/users/search - Zoeken naar users

9. **Activity Tracking (1)**
   - POST /api/v1/users/me/heartbeat - Last seen update

10. **Admin Moderation (4)**
    - GET /api/v1/admin/users/photo-moderation - Pending moderations
    - POST /api/v1/admin/users/{user_id}/photo-moderation - Foto modereren
    - POST /api/v1/admin/users/{user_id}/ban - User bannen
    - DELETE /api/v1/admin/users/{user_id}/ban - User unbannen

### Validatie Tests

- **Authenticatie**: Bearer tokens, Service-to-Service API keys
- **Input validatie**: Verplichte velden, lengtes, regex patterns
- **Grenzen**: Interests max 20, deltas -100..100, username regex
- **Permissies**: Admin-only routes, S2S-only routes, user routes
- **Database verificatie**: Na elke operatie wordt de database gecontroleerd

## Vereisten

### Services Running

```bash
# Check of alle services draaien
docker-compose ps

# Start services indien nodig
docker-compose up -d
```

Vereiste services:
- `auth-api` (port 8000)
- `userprofile-api` (port 8008)
- `activity-postgres-db`
- `auth-redis`

### Environment Variables (Optioneel)

Het script gebruikt default waarden, maar je kunt deze overschrijven:

```bash
export AUTH_API="http://localhost:8000"
export PROFILE_API="http://localhost:8008"
export DB_CONTAINER="activity-postgres-db"
export DB_USER="postgres"
export DB_NAME="activitydb"
export ACTIVITIES_API_KEY="your-activities-key"
export PAYMENT_API_KEY="your-payment-key"
```

## Gebruik

### Basis Gebruik

```bash
# Maak script executable (eenmalig)
chmod +x test-userprofile-api.sh

# Voer alle tests uit
./test-userprofile-api.sh
```

### Met Custom Environment

```bash
# Test tegen een andere instantie
AUTH_API="http://localhost:9000" PROFILE_API="http://localhost:9008" ./test-userprofile-api.sh
```

## Output

Het script geeft gedetailleerde output met:

- **✅ Groene checks**: Geslaagde tests
- **❌ Rode crosses**: Gefaalde tests
- **⏭️ Gele skip**: Overgeslagen tests (bijv. geen admin token)
- **💾 Database verificatie**: Query results uit PostgreSQL
- **📊 Samenvatting**: Totaal passed/failed/skipped

### Voorbeeld Output

```
════════════════════════════════════════════════════════
  🏆 USER PROFILE API - COMPREHENSIVE TEST SUITE 🏆
════════════════════════════════════════════════════════

Testing all 28 endpoints with:
  ✅ Authentication (Bearer & Service-to-Service)
  ✅ Input validation
  ✅ Database verification
  ✅ Permissions (admin, S2S, user)
  ✅ Error handling

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 1. PROFILE MANAGEMENT (5 endpoints)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TEST] GET /api/v1/users/me - Get my own profile
✅ SUCCESS: Profile retrieved with user_id
✅ SUCCESS: Profile contains email
✅ SUCCESS: Profile contains username
💾 DATABASE: Verifying in database:
...
```

## Database Verificatie

Het script voert automatisch PostgreSQL queries uit om te verifiëren dat:

- Data correct wordt opgeslagen
- Updates daadwerkelijk in de database verschijnen
- Relaties tussen tabellen kloppen
- Constraints worden nageleefd

Voorbeelden van geverifieerde tabellen:
- `activity.users`
- `activity.user_interests`
- `activity.user_settings`

## Test User

Het script maakt automatisch een test user aan:

- **Email**: `testuser@example.com`
- **Username**: `testuser` (wordt gewijzigd naar `testuser_updated`)
- **Password**: `TestPassword123!`

Deze user wordt:
1. Aangemaakt via Auth API
2. Email verified (via database update)
3. Gebruikt voor alle user-level tests
4. Blijft bestaan na test (voor handmatige verificatie)

## Admin Tests

Als er een admin user bestaat, worden ook admin-only endpoints getest:

- Captain program management
- Photo moderation
- User banning/unbanning

Het script probeert automatisch een admin user aan te maken:
- **Email**: `admin@example.com`
- **Username**: `admin`
- **Password**: `AdminPassword123!`

## Troubleshooting

### Services niet beschikbaar

```bash
# Check health endpoints
curl http://localhost:8000/health  # Auth API
curl http://localhost:8008/health  # Profile API

# Restart services
docker-compose restart auth-api userprofile-api
```

### Database connectie errors

```bash
# Check PostgreSQL
docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT 1;"

# Check container naam
docker ps | grep postgres
```

### Authenticatie fouten

Zorg dat `JWT_SECRET_KEY` hetzelfde is in beide services:

```bash
# In auth-api/.env en userprofile-api/.env
JWT_SECRET_KEY=dev-secret-key-change-in-production
```

### Service API Keys

Als S2S tests falen, check de API keys:

```bash
# In userprofile-api/.env
ACTIVITIES_API_KEY=activities-service-key-change-in-production
PAYMENT_API_KEY=payment-processor-key-change-in-production
```

## Handmatige Database Verificatie

Na de test kun je handmatig de database inspecteren:

```bash
# Connect to database
docker exec -it activity-postgres-db psql -U postgres -d activitydb

# Check test user
SELECT * FROM activity.users WHERE email = 'testuser@example.com';

# Check interests
SELECT * FROM activity.user_interests WHERE user_id = '<user-id-from-test>';

# Check settings
SELECT * FROM activity.user_settings WHERE user_id = '<user-id-from-test>';
```

## CI/CD Integratie

Het script is geschikt voor CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run API Tests
  run: |
    docker-compose up -d
    sleep 10  # Wait for services
    ./test-userprofile-api.sh
```

Exit codes:
- `0`: Alle tests geslaagd
- `1`: Setup fout (services niet beschikbaar)
- Test failures worden gelogd maar stoppen het script niet

## Vergelijking met demo-sprint-review.sh

| Feature | test-userprofile-api.sh | demo-sprint-review.sh |
|---------|-------------------------|----------------------|
| Endpoints | Alle 28 | Subset (~14) |
| Validatie | Ja (errors tests) | Nee |
| Admin tests | Ja | Nee |
| S2S tests | Ja | Nee |
| Interactief | Nee (automated) | Ja (met pauzes) |
| Database checks | Na elke test | Na sommige tests |
| Error handling | Uitgebreid | Basis |
| Doel | Comprehensive testing | Demo presentatie |

## Volgende Stappen

Na het runnen van dit script kun je:

1. **Handmatige tests**: Gebruik de test user credentials voor Postman/cURL tests
2. **Database exploratie**: Inspecteer de test data in PostgreSQL
3. **Load testing**: Gebruik tools zoals Apache Bench of k6
4. **Integration tests**: Test met echte image-api en email-api services

## Support

Voor vragen of issues:
1. Check de logs: `docker-compose logs userprofile-api`
2. Verify health: `curl http://localhost:8008/health`
3. Check database: `docker exec -it activity-postgres-db psql ...`

---

**Tip**: Run dit script na elke code change om regressies te voorkomen!
