# Trading Bot Platform - Rollback Procedures

## Quick Reference

| Issue | Severity | Rollback Method | Time to Rollback |
|-------|----------|----------------|------------------|
| API Deployment Failure | Critical | [ECS Task Rollback](#ecs-task-rollback) | 2-5 minutes |
| Database Migration Error | Critical | [Database Rollback](#database-migration-rollback) | 5-10 minutes |
| Config Change Breaking | High | [Config Rollback](#configuration-rollback) | 1-2 minutes |
| Frontend Issues | Medium | [Frontend Rollback](#frontend-rollback) | 2-3 minutes |
| Complete System Failure | Critical | [Full System Rollback](#full-system-rollback) | 10-15 minutes |

---

## Table of Contents

1. [Pre-Rollback Checklist](#pre-rollback-checklist)
2. [AWS ECS Rollback](#aws-ecs-rollback)
3. [Kubernetes Rollback](#kubernetes-rollback)
4. [Docker Compose Rollback](#docker-compose-rollback)
5. [Database Migration Rollback](#database-migration-rollback)
6. [Configuration Rollback](#configuration-rollback)
7. [Post-Rollback Verification](#post-rollback-verification)
8. [Incident Documentation](#incident-documentation)

---

## Pre-Rollback Checklist

Before initiating any rollback, complete this checklist:

- [ ] **Identify the issue** - What specifically is broken?
- [ ] **Assess impact** - How many users are affected?
- [ ] **Check monitoring** - Grafana, CloudWatch, logs
- [ ] **Notify team** - Alert team members via Slack
- [ ] **Document current state** - Take screenshots, copy error logs
- [ ] **Identify last known good version** - What version/commit was stable?
- [ ] **Verify rollback target** - Ensure target version exists
- [ ] **Pause auto-deployment** - Stop CI/CD pipelines temporarily
- [ ] **Create incident ticket** - Document in issue tracker

### Notification Template

```
🚨 INCIDENT ALERT 🚨
Service: [Backend/Frontend/Database/etc]
Severity: [Critical/High/Medium/Low]
Impact: [Number of users affected]
Issue: [Brief description]
Action: Rolling back to version [X]
ETA: [Expected resolution time]
Incident Commander: [Name]
```

---

## AWS ECS Rollback

### Method 1: Rollback to Previous Task Definition (Recommended)

**Use when:** Latest deployment is causing issues but previous version was stable.

**Steps:**

1. **Identify current and target task definitions**
```bash
# List recent task definitions
aws ecs list-task-definitions \
  --family-prefix backend-task \
  --sort DESC \
  --max-items 5

# Describe current service to see active task definition
aws ecs describe-services \
  --cluster trading-bot-cluster \
  --services backend-service \
  --query 'services[0].taskDefinition'
```

2. **Update service to previous task definition**
```bash
# Rollback backend
aws ecs update-service \
  --cluster trading-bot-cluster \
  --service backend-service \
  --task-definition backend-task:PREVIOUS_REVISION \
  --force-new-deployment

# Rollback frontend
aws ecs update-service \
  --cluster trading-bot-cluster \
  --service frontend-service \
  --task-definition frontend-task:PREVIOUS_REVISION \
  --force-new-deployment
```

3. **Monitor deployment progress**
```bash
# Watch service events
aws ecs describe-services \
  --cluster trading-bot-cluster \
  --services backend-service \
  --query 'services[0].events[0:10]'

# Wait for stable state
aws ecs wait services-stable \
  --cluster trading-bot-cluster \
  --services backend-service
```

**Expected Duration:** 2-5 minutes

### Method 2: Rollback via GitHub Actions

**Use when:** You want to redeploy a previous git commit.

1. **Navigate to GitHub Actions**
2. **Find successful workflow from previous deployment**
3. **Click "Re-run all jobs"**
4. **Monitor deployment progress**

**Expected Duration:** 5-10 minutes (includes build time)

### Method 3: Manual Image Rollback

**Use when:** You need to specify exact Docker image tag.

```bash
# Update task definition with specific image
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json

# Update service
aws ecs update-service \
  --cluster trading-bot-cluster \
  --service backend-service \
  --task-definition backend-task:LATEST
```

---

## Kubernetes Rollback

### Method 1: Automatic Rollback to Previous Revision

**Use when:** Latest rollout is failing.

```bash
# Check rollout status
kubectl rollout status deployment/backend -n trading-bot

# View rollout history
kubectl rollout history deployment/backend -n trading-bot

# Rollback to previous revision
kubectl rollout undo deployment/backend -n trading-bot

# Watch rollback progress
kubectl rollout status deployment/backend -n trading-bot -w
```

**Expected Duration:** 2-5 minutes

### Method 2: Rollback to Specific Revision

**Use when:** You need to go back multiple versions.

```bash
# View revision history with details
kubectl rollout history deployment/backend -n trading-bot

# Check specific revision details
kubectl rollout history deployment/backend --revision=3 -n trading-bot

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=3 -n trading-bot
```

### Method 3: Declarative Rollback

**Use when:** You want to apply a known good manifest.

```bash
# Apply previous version from git
git checkout <previous-commit>
kubectl apply -f deploy/kubernetes/deployment.yaml

# Or apply specific version
kubectl apply -f deploy/kubernetes/deployment-v1.2.3.yaml
```

### Verify Rollback

```bash
# Check pod status
kubectl get pods -n trading-bot -l app=backend

# Check deployment status
kubectl describe deployment backend -n trading-bot

# View recent events
kubectl get events -n trading-bot --sort-by='.lastTimestamp'

# Check logs
kubectl logs -f deployment/backend -n trading-bot --tail=100
```

---

## Docker Compose Rollback

### Method 1: Image Tag Rollback

**Use when:** Running production via Docker Compose.

```bash
# 1. Stop current services
docker-compose down

# 2. Update docker-compose.yml to use previous tag
# Edit docker-compose.yml:
# image: your-registry/backend:v1.2.3  # Change to previous tag

# 3. Pull specific image version
docker-compose pull

# 4. Start services
docker-compose up -d

# 5. Verify
docker-compose ps
docker-compose logs -f backend
```

**Expected Duration:** 3-5 minutes

### Method 2: Git-Based Rollback

**Use when:** You have version-controlled docker-compose files.

```bash
# 1. Find previous working commit
git log --oneline -n 10

# 2. Checkout previous version
git checkout <commit-hash>

# 3. Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# 4. Verify
docker-compose logs -f
```

### Method 3: Manual Container Rollback

**Use when:** You need fine-grained control.

```bash
# 1. Stop specific service
docker-compose stop backend

# 2. Remove container
docker-compose rm -f backend

# 3. Pull specific version
docker pull your-registry/backend:previous-tag

# 4. Update docker-compose.yml and start
docker-compose up -d backend

# 5. Check logs
docker-compose logs -f backend
```

---

## Database Migration Rollback

### ⚠️ CRITICAL: Database Rollbacks Are Risky

**Always:**
- Have a recent backup before rollback
- Test rollback in staging first
- Understand data loss implications
- Notify users of potential downtime

### Method 1: Alembic Downgrade

**Use when:** Migration is reversible and recent (< 1 hour old).

```bash
# 1. Connect to backend container
docker-compose exec backend bash
# or
kubectl exec -it deployment/backend -n trading-bot -- bash

# 2. Check current migration version
alembic current

# 3. View migration history
alembic history

# 4. Downgrade one revision
alembic downgrade -1

# 5. Verify database state
alembic current

# 6. Restart backend to clear caches
docker-compose restart backend
# or
kubectl rollout restart deployment/backend -n trading-bot
```

**Expected Duration:** 1-5 minutes

### Method 2: Specific Revision Downgrade

```bash
# Downgrade to specific revision
alembic downgrade <revision-id>

# Example: Downgrade to revision abc123
alembic downgrade abc123
```

### Method 3: Database Restore from Backup

**Use when:** Migration is irreversible or caused data corruption.

#### AWS RDS Restore

```bash
# 1. Create snapshot of current state (safety measure)
aws rds create-db-snapshot \
  --db-instance-identifier trading-bot-db \
  --db-snapshot-identifier pre-rollback-$(date +%Y%m%d-%H%M%S)

# 2. Find suitable snapshot to restore from
aws rds describe-db-snapshots \
  --db-instance-identifier trading-bot-db \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,SnapshotCreateTime]'

# 3. Restore from snapshot (creates new instance)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier trading-bot-db-restored \
  --db-snapshot-identifier <snapshot-id>

# 4. Wait for restoration
aws rds wait db-instance-available \
  --db-instance-identifier trading-bot-db-restored

# 5. Update connection string in application
# Update DATABASE_URL to point to new instance

# 6. Test with new database
# 7. If successful, delete old instance
```

**Expected Duration:** 15-30 minutes

#### PostgreSQL Manual Restore

```bash
# 1. Stop application to prevent new writes
docker-compose stop backend celery-worker

# 2. Drop and recreate database
psql -U postgres -h localhost << EOF
DROP DATABASE trading_bot;
CREATE DATABASE trading_bot;
EOF

# 3. Restore from backup
psql -U postgres -h localhost trading_bot < /backups/trading_bot_YYYYMMDD.sql

# 4. Verify data
psql -U postgres -h localhost trading_bot -c "SELECT COUNT(*) FROM users;"

# 5. Restart services
docker-compose start backend celery-worker
```

**Expected Duration:** 10-20 minutes (depends on database size)

### Database Rollback Decision Matrix

| Scenario | Recommended Method | Data Loss Risk |
|----------|-------------------|----------------|
| Just ran migration (< 5 min) | Alembic downgrade | None |
| Migration < 1 hour, no new data | Alembic downgrade | None |
| Migration > 1 hour, active users | Restore from backup | Yes (recent data) |
| Data corruption detected | Restore from backup | Yes (corrupted data) |
| Irreversible migration | Restore from backup | Yes (depends on backup age) |

---

## Configuration Rollback

### Environment Variables

**Use when:** Configuration change caused issues.

#### AWS Secrets Manager

```bash
# 1. List secret versions
aws secretsmanager list-secret-version-ids \
  --secret-id trading-bot/production

# 2. Restore previous version
aws secretsmanager update-secret \
  --secret-id trading-bot/production \
  --secret-string "$(aws secretsmanager get-secret-value \
    --secret-id trading-bot/production \
    --version-id <previous-version-id> \
    --query SecretString --output text)"

# 3. Restart services to pick up changes
aws ecs update-service \
  --cluster trading-bot-cluster \
  --service backend-service \
  --force-new-deployment
```

#### Kubernetes ConfigMap/Secret

```bash
# 1. View configmap history (if versioned in git)
git log deploy/kubernetes/configmap.yaml

# 2. Apply previous version
git checkout <previous-commit> -- deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml

# 3. Restart pods to pick up changes
kubectl rollout restart deployment/backend -n trading-bot
```

#### Docker Compose

```bash
# 1. Edit .env file with previous values
nano .env

# 2. Restart services
docker-compose restart backend
```

**Expected Duration:** 1-2 minutes

---

## Frontend Rollback

### CDN Cache Invalidation

**If frontend is cached, clear CDN:**

```bash
# CloudFront
aws cloudfront create-invalidation \
  --distribution-id <distribution-id> \
  --paths "/*"

# CloudFlare
curl -X POST "https://api.cloudflare.com/client/v4/zones/<zone-id>/purge_cache" \
  -H "Authorization: Bearer <api-token>" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

### Static Asset Rollback

```bash
# S3
aws s3 sync s3://trading-bot-frontend-backup/v1.2.3/ s3://trading-bot-frontend/ --delete

# Kubernetes
kubectl set image deployment/frontend \
  frontend=your-registry/frontend:v1.2.3 \
  -n trading-bot
```

---

## Full System Rollback

**Use only in catastrophic failure scenarios.**

### Pre-Rollback

```bash
# 1. Enable maintenance mode
# Update load balancer to show maintenance page

# 2. Notify users
# Send email/push notification about temporary downtime
```

### Execute Rollback

```bash
# 1. Stop all services
docker-compose down
# or
kubectl scale deployment --all --replicas=0 -n trading-bot

# 2. Restore database from backup
# Follow database restore procedure above

# 3. Checkout previous stable version
git checkout <stable-commit>

# 4. Deploy previous version
docker-compose up -d
# or
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl rollout status deployment/backend -n trading-bot

# 5. Verify all services
./scripts/health-check.sh

# 6. Disable maintenance mode
# Restore normal load balancer configuration
```

**Expected Duration:** 20-30 minutes

---

## Post-Rollback Verification

### Automated Health Checks

```bash
#!/bin/bash
# scripts/health-check.sh

echo "=== Health Check ==="

# API Health
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.yourdomain.com/health)
if [ "$API_STATUS" = "200" ]; then
  echo "✓ API: Healthy"
else
  echo "✗ API: Failed (Status: $API_STATUS)"
  exit 1
fi

# Database connection
DB_CHECK=$(docker-compose exec -T backend python -c "from src.core.database import engine; engine.connect(); print('OK')")
if [ "$DB_CHECK" = "OK" ]; then
  echo "✓ Database: Connected"
else
  echo "✗ Database: Connection failed"
  exit 1
fi

# Redis connection
REDIS_CHECK=$(docker-compose exec -T redis redis-cli ping)
if [ "$REDIS_CHECK" = "PONG" ]; then
  echo "✓ Redis: Connected"
else
  echo "✗ Redis: Connection failed"
  exit 1
fi

# Celery workers
CELERY_WORKERS=$(docker-compose exec -T backend celery -A src.tasks.celery_app inspect active | grep -c "OK")
if [ "$CELERY_WORKERS" -gt 0 ]; then
  echo "✓ Celery: $CELERY_WORKERS workers active"
else
  echo "✗ Celery: No workers active"
  exit 1
fi

echo "=== All Systems Healthy ==="
```

### Manual Verification Checklist

- [ ] **API endpoints responding** - Test /health, /api/v1/bots
- [ ] **Authentication working** - Login test
- [ ] **Database queries successful** - Check recent trades
- [ ] **WebSocket connections** - Test real-time updates
- [ ] **Background jobs running** - Check Celery tasks
- [ ] **Monitoring active** - Grafana dashboards showing data
- [ ] **Alerts cleared** - No active critical alerts
- [ ] **User functionality** - Create/start/stop bot test
- [ ] **Logs clean** - No error spam in logs
- [ ] **Performance normal** - Response times < 200ms

### Smoke Tests

```bash
# Quick smoke test script
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -d "username=test&password=test" | jq .access_token

TOKEN="<token-from-above>"

curl https://api.yourdomain.com/api/v1/bots \
  -H "Authorization: Bearer $TOKEN" | jq .

curl https://api.yourdomain.com/api/v1/exchanges \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Incident Documentation

### Incident Report Template

```markdown
# Incident Report: [Brief Title]

## Summary
- **Date:** YYYY-MM-DD HH:MM UTC
- **Duration:** X hours Y minutes
- **Severity:** Critical / High / Medium / Low
- **Affected Users:** X users / X% of user base
- **Root Cause:** [One-line summary]

## Timeline

**Detection:**
- HH:MM - Alert triggered: [Alert name]
- HH:MM - Incident confirmed by [Name]
- HH:MM - Incident commander assigned: [Name]

**Response:**
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Decision to rollback made
- HH:MM - Rollback initiated

**Resolution:**
- HH:MM - Rollback completed
- HH:MM - Services verified healthy
- HH:MM - Incident resolved

## Root Cause Analysis

**What happened:**
[Detailed explanation of what went wrong]

**Why it happened:**
[Technical root cause]

**Why it wasn't caught earlier:**
[Gaps in testing, monitoring, etc.]

## Impact Assessment

**User Impact:**
- X users unable to [action]
- Y failed transactions
- Z support tickets created

**Business Impact:**
- Estimated revenue loss: $X
- SLA breach: Yes/No
- Reputation impact: [Assessment]

## Rollback Details

**Method Used:** [ECS/K8s/Docker rollback type]
**Target Version:** [Version/commit/image tag]
**Duration:** X minutes
**Issues Encountered:** [Any problems during rollback]

## Action Items

- [ ] Fix underlying bug: [Ticket link]
- [ ] Add monitoring for this scenario: [Ticket link]
- [ ] Update deployment checklist: [Ticket link]
- [ ] Add automated test: [Ticket link]
- [ ] Document in runbook: [Ticket link]

## Lessons Learned

**What went well:**
- Quick detection
- Smooth rollback process
- Good team communication

**What could be improved:**
- Earlier detection via monitoring
- Faster decision to rollback
- Better testing coverage

## Preventive Measures

1. [Specific change to prevent recurrence]
2. [Additional monitoring/alerting]
3. [Process improvement]
```

### Post-Incident Review Meeting

**Schedule within 48 hours of resolution**

**Attendees:**
- Incident commander
- Engineers involved
- Product/Engineering leads
- Support team representative

**Agenda:**
1. Review timeline (10 min)
2. Discuss root cause (15 min)
3. Identify contributing factors (10 min)
4. Define action items (15 min)
5. Assign owners and deadlines (10 min)

---

## Prevention Best Practices

### 1. Deployment Strategy

```yaml
# Use blue-green or canary deployments
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0  # Zero-downtime
```

### 2. Automated Rollback Triggers

```yaml
# Auto-rollback on high error rate
if error_rate > 5% for 5 minutes:
  trigger_automatic_rollback()
```

### 3. Feature Flags

```python
# Gradual feature enablement
if feature_flag('new_trading_algorithm', user):
    use_new_algorithm()
else:
    use_stable_algorithm()
```

### 4. Comprehensive Testing

- Unit tests (90%+ coverage)
- Integration tests
- End-to-end tests
- Load testing
- Chaos engineering

### 5. Monitoring & Alerts

- Real-time error tracking
- Performance monitoring
- User behavior analytics
- Automated alerts
- On-call rotation

---

## Quick Command Reference

```bash
# AWS ECS Rollback
aws ecs update-service --cluster trading-bot-cluster --service backend-service --task-definition backend-task:PREV

# Kubernetes Rollback
kubectl rollout undo deployment/backend -n trading-bot

# Docker Compose Rollback
docker-compose down && git checkout PREV && docker-compose up -d

# Database Rollback
alembic downgrade -1

# Check Service Health
curl https://api.yourdomain.com/health
```

---

## Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| On-Call Engineer | TBD | +1-XXX-XXX-XXXX | oncall@yourdomain.com |
| DevOps Lead | TBD | +1-XXX-XXX-XXXX | devops@yourdomain.com |
| CTO | TBD | +1-XXX-XXX-XXXX | cto@yourdomain.com |
| AWS Support | - | - | aws-support-case |

**Escalation Path:**
1. On-Call Engineer (0-15 min)
2. DevOps Lead (15-30 min)
3. CTO (30+ min or business-critical)

---

## Maintenance Windows

**Scheduled maintenance for risky changes:**
- Tuesday & Thursday, 2:00-4:00 AM UTC
- Low traffic period
- Full team available
- Rollback plan prepared

---

Remember: **When in doubt, rollback first, investigate later.**
