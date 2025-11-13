# 🧪 Quick Demo Test Guide

## Pre-Demo Verificatie (5 minuten voor presentatie!)

### 1. Services Check
```bash
cd /mnt/d/activity/userprofile-api

# Check alle services
docker ps | grep -E "auth-api|userprofile|postgres|redis"

# Expected output: 5 containers RUNNING
# - auth-api
# - userprofile-api
# - activity-postgres-db
# - auth-redis
# - activity-redis
```

**Als een service niet draait**:
```bash
cd /mnt/d/activity/auth-api && docker compose up -d
cd /mnt/d/activity/userprofile-api && docker compose up -d
```

### 2. Health Checks
```bash
# Auth API
curl http://localhost:8000/health
# Expected: {"status":"healthy",...}

# User Profile API
curl http://localhost:8008/health
# Expected: {"status":"healthy","environment":"development","version":"1.0.0","checks":{"api":"ok","database":"ok","cache":"ok"}}
```

**Als unhealthy**:
```bash
# Check logs
docker logs auth-api --tail 50
docker logs userprofile-api --tail 50

# Restart als nodig
docker restart auth-api userprofile-api
```

### 3. Database Connectivity
```bash
docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT COUNT(*) FROM activity.users;"
```

**Expected**: Een getal (aantal users in database)

### 4. Cleanup Test User
```bash
docker exec activity-postgres-db psql -U postgres -d activitydb -c "DELETE FROM activity.users WHERE email = 'john.doe@activityapp.com';"
```

**Expected**: `DELETE 0` of `DELETE 1`

---

## Dry Run Test (10 minuten voor presentatie)

### Test 1: Registratie
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Expected**:
```json
{
  "user_id": "...",
  "email": "test@example.com",
  ...
}
```

### Test 2: Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

**Expected**:
```json
{
  "access_token": "eyJ...",
  ...
}
```

**Als login faalt**: User is nog niet verified
```bash
# Verify user
docker exec activity-postgres-db psql -U postgres -d activitydb -c \
  "UPDATE activity.users SET is_verified = TRUE WHERE email = 'test@example.com';"

# Try login again
```

### Test 3: Cleanup
```bash
docker exec activity-postgres-db psql -U postgres -d activitydb -c "DELETE FROM activity.users WHERE email IN ('test@example.com', 'john.doe@activityapp.com');"
```

---

## Full Demo Script Test

### Run Complete Demo
```bash
cd /mnt/d/activity/userprofile-api

# Make sure script is executable
chmod +x demo-sprint-review.sh

# Run demo (INTERACTIVE - will pause at each step)
./demo-sprint-review.sh
```

### What to Watch For

✅ **Green checkmarks** bij elke stap
✅ **Database queries** tonen correcte data
✅ **No errors** in responses
✅ **JWT token** wordt correct verkregen
✅ **All 14 steps** completen succesvol

### Common Issues & Fixes

#### Issue 1: "User already exists"
```bash
# Cleanup en herstart
docker exec activity-postgres-db psql -U postgres -d activitydb -c \
  "DELETE FROM activity.users WHERE email = 'john.doe@activityapp.com';"
./demo-sprint-review.sh
```

#### Issue 2: "401 Unauthorized"
```bash
# JWT secret mismatch - check .env files
cat .env | grep JWT_SECRET_KEY
docker exec auth-api env | grep JWT_SECRET_KEY
# These MUST match!
```

#### Issue 3: "Connection refused"
```bash
# Service not running
docker restart auth-api userprofile-api
sleep 5
./demo-sprint-review.sh
```

#### Issue 4: "Database error"
```bash
# Check stored procedures exist
docker exec activity-postgres-db psql -U postgres -d activitydb -c "\df activity.sp_get_user_profile"

# If missing, redeploy
docker exec -i activity-postgres-db psql -U postgres -d activitydb < database/stored_procedures.sql
```

---

## Pre-Presentation Checklist

**15 minuten voor presentatie**:

- [ ] Alle services draaien (docker ps)
- [ ] Health checks zijn groen
- [ ] Database is bereikbaar
- [ ] Test user is verwijderd
- [ ] Demo script is executable
- [ ] Terminal in fullscreen
- [ ] Browser met /docs open (backup)
- [ ] Dit document print/open voor reference

**5 minuten voor presentatie**:

- [ ] Dry run succesvol gedraaid
- [ ] Cleanup gedaan
- [ ] Terminal schoongemaakt (clear)
- [ ] Kalm en voorbereid 😊

**Direct voor presentatie**:

- [ ] Laatste health check
- [ ] Clear terminal
- [ ] Diep ademhalen
- [ ] Glimlach! 🎉

---

## Emergency Backup Commands

### Manual Demo (if script fails)

```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register -H "Content-Type: application/json" -d '{"email":"john.doe@activityapp.com","username":"johndoe","password":"SecurePassword123!","first_name":"John","last_name":"Doe"}'

# 2. Verify (in DB)
docker exec activity-postgres-db psql -U postgres -d activitydb -c "UPDATE activity.users SET is_verified = TRUE WHERE email = 'john.doe@activityapp.com';"

# 3. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"email":"john.doe@activityapp.com","password":"SecurePassword123!"}' | jq -r '.access_token')

# 4. Get Profile
curl -H "Authorization: Bearer $TOKEN" http://localhost:8008/api/v1/users/me | jq .

# 5. Show in Database
docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT * FROM activity.users WHERE email = 'john.doe@activityapp.com';"
```

---

## Success Indicators

### ✅ Perfect Demo Run

- All services healthy
- Script runs without errors
- Database verification shows correct data
- JWT authentication works
- All 14 steps complete
- Total time: ~10-12 minutes
- Audience is impressed 🎉

### 🟡 Good Demo Run (acceptable)

- 1-2 minor glitches recovered
- Manual intervention needed once
- Database shows correct final state
- Main flow demonstrated
- Audience understands the system

### 🔴 Failed Demo (abort and use backup)

- Multiple service failures
- JWT authentication broken
- Database queries failing
- Script errors not recoverable
- → Switch to Swagger UI demo or pre-recorded video

---

## Final Confidence Boost

**You got this!** 💪

- Script is tested and works
- All services are operational
- Database is solid
- You know the system inside-out
- The directeur will be impressed

**Remember**:
> "I'm not just showing code, I'm demonstrating a production-ready enterprise API that we built from scratch in record time!"

🚀 **Let's crush this presentation!** 🚀
