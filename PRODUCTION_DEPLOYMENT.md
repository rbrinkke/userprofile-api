# 🚀 PRODUCTION DEPLOYMENT CHECKLIST

**User Profile API v1.0.0**

Complete pre-productie checklist voor veilige deployment.

---

## ⚠️ KRITIEK - VOOR DEPLOYMENT

### 🔐 Secrets & API Keys

- [ ] **Genereer nieuwe JWT_SECRET_KEY**
  ```bash
  openssl rand -hex 32
  # Vervang JWT_SECRET_KEY in .env
  ```

- [ ] **Genereer nieuwe Service API Keys**
  ```bash
  # Activities API
  openssl rand -hex 32
  # Participation API
  openssl rand -hex 32
  # Moderation API
  openssl rand -hex 32
  # Payment API
  openssl rand -hex 32
  ```

- [ ] **Verwijder development secrets**
  - ❌ Verwijder: `dev-secret-key-change-in-production`
  - ❌ Verwijder: `dev-activities-key`
  - ❌ Verwijder: `dev-*` values

- [ ] **Environment variables beveiligd**
  - [ ] Secrets in environment (niet in code)
  - [ ] `.env` NIET in Git
  - [ ] Secret management tool (AWS Secrets Manager / Vault)

---

### 🗄️ Database Configuratie

- [ ] **PostgreSQL Production Setup**
  ```bash
  # Update in .env:
  DATABASE_URL=postgresql://prod_user:STRONG_PASSWORD@db-host:5432/activity
  DATABASE_POOL_MIN_SIZE=10
  DATABASE_POOL_MAX_SIZE=100  # Verhoogd voor productie
  ```

- [ ] **Schema deployment**
  ```bash
  psql -U prod_user -d activity -f sqlschema.sql
  psql -U prod_user -d activity -f database/stored_procedures.sql

  # Verify
  psql -U prod_user -d activity -c "\df activity.*"
  ```

- [ ] **Indexes verificatie**
  ```sql
  -- Check all indexes exist
  SELECT schemaname, tablename, indexname
  FROM pg_indexes
  WHERE schemaname = 'activity'
  ORDER BY tablename;
  ```

- [ ] **Backup configuratie**
  - [ ] Automated daily backups
  - [ ] Point-in-time recovery enabled
  - [ ] Backup retention: 30 dagen
  - [ ] Test restore procedure

- [ ] **Replication setup** (optioneel maar aanbevolen)
  - [ ] Read replicas voor scaling
  - [ ] Failover configuratie

---

### 🔴 Redis Configuratie

- [ ] **Redis Production Setup**
  ```bash
  # Update in .env:
  REDIS_URL=redis://prod-redis-host:6379/0
  REDIS_CACHE_DB=0
  REDIS_RATE_LIMIT_DB=1
  ```

- [ ] **Redis persistence**
  - [ ] AOF enabled (appendonly yes)
  - [ ] RDB snapshots configured
  - [ ] Backup strategy

- [ ] **Redis cluster** (voor high availability)
  - [ ] 3+ nodes
  - [ ] Sentinel voor failover
  - [ ] Monitoring

---

### 🌐 Network & Security

- [ ] **CORS Configuration**
  ```bash
  # Update in .env met production domains:
  CORS_ORIGINS='["https://app.yourdomain.com","https://www.yourdomain.com"]'
  ```

- [ ] **SSL/TLS Certificates**
  - [ ] HTTPS geconfigureerd
  - [ ] Certificaten geldig
  - [ ] Auto-renewal ingesteld
  - [ ] Redirect HTTP → HTTPS

- [ ] **Firewall Rules**
  - [ ] API alleen toegankelijk via load balancer
  - [ ] Database alleen toegankelijk vanuit API network
  - [ ] Redis alleen toegankelijk vanuit API network
  - [ ] SSH alleen via bastion host

- [ ] **Rate Limiting**
  ```bash
  # Verify in .env:
  RATE_LIMIT_ENABLED=true
  ```

- [ ] **DDoS Protection**
  - [ ] CloudFlare / AWS Shield
  - [ ] Rate limiting per IP
  - [ ] WAF rules

---

### 📊 Monitoring & Observability

- [ ] **Prometheus Setup**
  ```bash
  # Verify metrics endpoint:
  curl https://api.yourdomain.com/metrics
  ```

- [ ] **Grafana Dashboards**
  - [ ] API response times
  - [ ] Error rates
  - [ ] Database connections
  - [ ] Cache hit rates
  - [ ] Rate limit violations

- [ ] **Alerting Rules**
  - [ ] Error rate > 5%
  - [ ] Response time p95 > 500ms
  - [ ] Database connection pool > 90%
  - [ ] Health check failures
  - [ ] Disk space < 20%

- [ ] **Logging Infrastructure**
  ```bash
  # Update in .env:
  LOG_LEVEL=INFO
  LOG_FORMAT=json
  ENVIRONMENT=production
  ```

  - [ ] Log aggregation (ELK / CloudWatch)
  - [ ] Log retention: 30 dagen
  - [ ] Search & filtering
  - [ ] Error tracking (Sentry)

- [ ] **APM (Application Performance Monitoring)**
  - [ ] New Relic / DataDog / Dynatrace
  - [ ] Transaction tracing
  - [ ] Database query monitoring

---

### 🐳 Container & Orchestration

- [ ] **Docker Image**
  ```bash
  # Build production image:
  docker build -t userprofile-api:1.0.0 .

  # Tag for registry:
  docker tag userprofile-api:1.0.0 your-registry/userprofile-api:1.0.0

  # Push to registry:
  docker push your-registry/userprofile-api:1.0.0
  ```

- [ ] **Security Scanning**
  ```bash
  # Scan image for vulnerabilities:
  docker scan userprofile-api:1.0.0
  # or
  trivy image userprofile-api:1.0.0
  ```

- [ ] **Kubernetes Deployment** (indien van toepassing)
  - [ ] Resource limits (CPU, memory)
  - [ ] Health checks (liveness, readiness)
  - [ ] Horizontal Pod Autoscaling
  - [ ] Rolling updates strategy
  - [ ] Secret management (Kubernetes Secrets)

- [ ] **Load Balancer**
  - [ ] 2+ API instances
  - [ ] Health check endpoint: `/health`
  - [ ] Session affinity: Disabled (stateless API)
  - [ ] SSL termination

---

## 🧪 PRE-DEPLOYMENT TESTING

### Staging Environment

- [ ] **Staging deployment**
  - [ ] Identical to production
  - [ ] Real database (anonymized data)
  - [ ] Real Redis instance

- [ ] **Functional Testing**
  - [ ] All 28 endpoints working
  - [ ] JWT authentication
  - [ ] Subscription gates (free/premium)
  - [ ] Service-to-service auth
  - [ ] Admin operations

- [ ] **Load Testing**
  ```bash
  # Example with k6:
  k6 run --vus 100 --duration 5m load-test.js

  # Targets:
  # - Response time p95 < 500ms
  # - Error rate < 1%
  # - Throughput > 1000 req/s
  ```

- [ ] **Chaos Testing** (optioneel)
  - [ ] Database connection loss
  - [ ] Redis unavailability
  - [ ] Network latency
  - [ ] Pod crashes

- [ ] **Security Testing**
  - [ ] Penetration testing
  - [ ] OWASP Top 10 checks
  - [ ] API key validation
  - [ ] Rate limit enforcement
  - [ ] SQL injection attempts
  - [ ] JWT tampering

---

## 📋 DEPLOYMENT PROCEDURE

### Pre-Deployment

- [ ] **Backup current state** (indien update)
  ```bash
  # Database backup
  pg_dump -U prod_user activity > backup_$(date +%Y%m%d_%H%M%S).sql

  # Redis backup
  redis-cli SAVE
  ```

- [ ] **Maintenance window**
  - [ ] Kommuniceer naar gebruikers
  - [ ] Status page update

### Deployment Steps

1. **Deploy Database Changes** (indien van toepassing)
   ```bash
   # Run migrations
   psql -U prod_user -d activity -f migrations/001_new_feature.sql
   ```

2. **Deploy API**
   ```bash
   # Kubernetes rolling update:
   kubectl set image deployment/userprofile-api \
     api=your-registry/userprofile-api:1.0.0

   # Or Docker Compose:
   docker-compose pull
   docker-compose up -d
   ```

3. **Verify Health**
   ```bash
   # Wait for containers to be ready
   sleep 30

   # Check health
   curl https://api.yourdomain.com/health

   # Expected response:
   # {"status": "healthy", "checks": {"api": "ok", "database": "ok", "cache": "ok"}}
   ```

4. **Smoke Tests**
   ```bash
   # Test critical endpoints:
   curl -H "Authorization: Bearer $TEST_TOKEN" \
     https://api.yourdomain.com/api/v1/users/me

   # Test service-to-service:
   curl -H "X-Service-API-Key: $SERVICE_KEY" \
     -X POST https://api.yourdomain.com/api/v1/users/$USER_ID/verify
   ```

5. **Monitor Metrics**
   - [ ] Check Grafana dashboards
   - [ ] Verify no errors in logs
   - [ ] Check response times
   - [ ] Verify database connections

### Post-Deployment

- [ ] **Monitor for 1 hour**
  - [ ] Error rates
  - [ ] Response times
  - [ ] Database queries
  - [ ] Cache performance

- [ ] **Verify core flows**
  - [ ] User profile retrieval
  - [ ] Profile updates
  - [ ] Photo management
  - [ ] Search functionality
  - [ ] Admin operations

- [ ] **Update documentation**
  - [ ] API version in docs
  - [ ] Changelog
  - [ ] Known issues

---

## 🔄 ROLLBACK PROCEDURE

**Indien deployment faalt:**

### Quick Rollback

```bash
# Kubernetes:
kubectl rollout undo deployment/userprofile-api

# Docker Compose:
docker-compose down
# Update docker-compose.yml met vorige versie
docker-compose up -d
```

### Database Rollback

```bash
# Restore backup:
psql -U prod_user -d activity < backup_TIMESTAMP.sql
```

### Verification

```bash
# Check health:
curl https://api.yourdomain.com/health

# Verify version:
curl https://api.yourdomain.com/ | jq .version
```

---

## 🎯 POST-DEPLOYMENT CHECKLIST

### Immediate (0-1 uur)

- [ ] ✅ All health checks passing
- [ ] ✅ No error spikes in logs
- [ ] ✅ Response times within SLA
- [ ] ✅ Database connections stable
- [ ] ✅ Cache hit rate > 80%

### Short-term (1-24 uur)

- [ ] Monitor error rates
- [ ] Check for memory leaks
- [ ] Verify backup completion
- [ ] Review security logs
- [ ] Check rate limiting effectiveness

### Long-term (1-7 dagen)

- [ ] Performance trending
- [ ] Cost optimization
- [ ] User feedback
- [ ] Security scan results
- [ ] Capacity planning

---

## 🆘 INCIDENT RESPONSE

### Severity Levels

**P0 - CRITICAL** (Total outage)
- Response time: < 15 min
- Escalate immediately
- Rollback if needed

**P1 - HIGH** (Major feature broken)
- Response time: < 1 hour
- Fix or rollback

**P2 - MEDIUM** (Minor issues)
- Response time: < 4 hours
- Schedule fix

**P3 - LOW** (Cosmetic/minor)
- Response time: < 24 hours
- Add to backlog

### On-Call Procedures

1. **Alert received**
   - Check Grafana dashboards
   - Check error logs
   - Identify root cause

2. **Mitigation**
   - Rollback if critical
   - Apply hotfix if possible
   - Scale resources if needed

3. **Communication**
   - Update status page
   - Notify stakeholders
   - Post-mortem after resolution

---

## 📞 CONTACTS & RESOURCES

### Team Contacts

- **Engineering Lead**: [email]
- **DevOps**: [email]
- **Database Admin**: [email]
- **Security**: [email]
- **On-Call**: [phone/slack]

### Resources

- **API Docs**: https://api.yourdomain.com/docs
- **Monitoring**: https://grafana.yourdomain.com
- **Logs**: https://logs.yourdomain.com
- **Status Page**: https://status.yourdomain.com
- **Runbooks**: [link to runbooks]

---

## ✅ FINAL SIGN-OFF

**Deployment Lead**: ___________________ Datum: ___________

**DevOps**: ___________________ Datum: ___________

**Security**: ___________________ Datum: ___________

**Engineering Manager**: ___________________ Datum: ___________

---

## 📝 DEPLOYMENT LOG

| Datum | Versie | Deployer | Status | Notes |
|-------|--------|----------|--------|-------|
| 2025-11-13 | 1.0.0 | Claude | ✅ Ready | Initial production release |
|  |  |  |  |  |
|  |  |  |  |  |

---

**Document Versie**: 1.0
**Laatst bijgewerkt**: 2025-11-13
**Eigenaar**: Engineering Team
