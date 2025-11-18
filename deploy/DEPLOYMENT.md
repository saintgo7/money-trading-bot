# Trading Bot Platform - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [AWS Deployment](#aws-deployment)
4. [DigitalOcean Deployment](#digitalocean-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Post-Deployment](#post-deployment)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- Docker & Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Cloud-Specific Requirements

#### AWS
- AWS CLI configured
- Terraform >= 1.0
- AWS Account with appropriate permissions
- Route53 domain (optional)

#### DigitalOcean
- `doctl` CLI installed and authenticated
- SSH key added to DigitalOcean account
- Domain configured (optional)

#### Kubernetes
- `kubectl` configured
- Helm 3+ (optional)
- Access to Kubernetes cluster

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/trading_bot
POSTGRES_USER=admin
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=trading_bot

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com

# Exchange API Keys
BINANCE_API_KEY=<your-key>
BINANCE_API_SECRET=<your-secret>
BINANCE_TESTNET=false

UPBIT_ACCESS_KEY=<your-key>
UPBIT_SECRET_KEY=<your-secret>

# Monitoring (Optional)
GRAFANA_ADMIN_PASSWORD=<strong-password>
SLACK_WEBHOOK_URL=<your-webhook>
PAGERDUTY_SERVICE_KEY=<your-key>

# Email (Optional)
SMTP_USERNAME=<email>
SMTP_PASSWORD=<password>
```

---

## Deployment Options

### Quick Comparison

| Option | Cost | Setup Time | Scalability | Complexity |
|--------|------|------------|-------------|------------|
| Docker Compose | Low | 10 min | Low | Low |
| DigitalOcean | Medium | 30 min | Medium | Medium |
| AWS | Medium-High | 1-2 hours | High | High |
| Kubernetes | Variable | 2-4 hours | Very High | Very High |

---

## AWS Deployment

### Cost Estimate: ~$150-200/month

**Services Used:**
- ECS Fargate: ~$80/month
- RDS PostgreSQL (db.t3.micro): ~$15/month
- ElastiCache Redis (cache.t3.micro): ~$15/month
- ALB: ~$20/month
- Data transfer & storage: ~$30/month

### Step 1: Prepare Terraform

```bash
cd deploy/aws/terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply
```

### Step 2: Configure Secrets

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name trading-bot/production \
  --secret-string file://.env
```

### Step 3: Deploy Application

```bash
# Build and push Docker images
docker build -t trading-bot-backend:latest ./backend
docker build -t trading-bot-frontend:latest ./frontend

# Tag for ECR
docker tag trading-bot-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/trading-bot-backend:latest
docker tag trading-bot-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/trading-bot-frontend:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/trading-bot-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/trading-bot-frontend:latest

# Update ECS service
aws ecs update-service \
  --cluster trading-bot-cluster \
  --service backend-service \
  --force-new-deployment
```

### Step 4: Verify Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster trading-bot-cluster \
  --services backend-service frontend-service

# Check task health
aws ecs list-tasks --cluster trading-bot-cluster

# Get ALB DNS
aws elbv2 describe-load-balancers \
  --names trading-bot-alb \
  --query 'LoadBalancers[0].DNSName'
```

---

## DigitalOcean Deployment

### Cost Estimate: ~$50-80/month

**Services Used:**
- Droplet (2 vCPU, 4GB RAM): ~$24/month
- Managed PostgreSQL: ~$15/month
- Spaces (storage): ~$5/month
- Bandwidth: ~$5/month

### Automated Deployment

```bash
cd deploy/digitalocean

# Set domain (optional)
export DOMAIN=trading-bot.example.com

# Run deployment script
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Create managed PostgreSQL database
2. Create and configure droplet
3. Install Docker and dependencies
4. Deploy application
5. Configure firewall
6. Setup SSL certificate

### Manual Steps After Deployment

1. Update DNS nameservers to DigitalOcean
2. Add exchange API keys:
```bash
ssh root@<droplet-ip>
cd /opt/money-trading-bot
nano .env  # Add your API keys
docker-compose restart
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Create namespace
kubectl create namespace trading-bot

# Create secrets
kubectl create secret generic trading-bot-secrets \
  --from-literal=postgres-user=admin \
  --from-literal=postgres-password=<password> \
  --from-literal=database-url=<connection-string> \
  --from-literal=secret-key=<secret-key> \
  -n trading-bot
```

### Deploy

```bash
cd deploy/kubernetes

# Apply all resources
kubectl apply -f deployment.yaml

# Verify deployment
kubectl get all -n trading-bot

# Check pod status
kubectl get pods -n trading-bot -w

# Get service URLs
kubectl get svc -n trading-bot
```

### Scale Services

```bash
# Manual scaling
kubectl scale deployment backend --replicas=5 -n trading-bot

# Auto-scaling is configured via HPA (3-10 replicas)
kubectl get hpa -n trading-bot
```

---

## Monitoring Setup

### Deploy Monitoring Stack

```bash
cd deploy/monitoring

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services
docker-compose -f docker-compose.monitoring.yml ps
```

### Access Dashboards

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### Configure Alerts

1. Update `alertmanager.yml` with your Slack/email details
2. Restart Alertmanager:
```bash
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

### Import Dashboards

1. Login to Grafana
2. Go to Dashboards → Import
3. Upload `grafana-dashboard.json`

---

## Post-Deployment

### 1. Database Migrations

```bash
# SSH to server or exec into container
docker-compose exec backend alembic upgrade head
```

### 2. Create Admin User

```bash
# Using API
curl -X POST https://api.yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "username": "admin",
    "password": "secure-password"
  }'
```

### 3. Test API

```bash
# Health check
curl https://api.yourdomain.com/health

# Get token
TOKEN=$(curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -d "username=admin&password=secure-password" | jq -r .access_token)

# Test authenticated endpoint
curl https://api.yourdomain.com/api/v1/bots \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Configure Exchanges

Add exchange credentials via API or directly in database:

```bash
curl -X POST https://api.yourdomain.com/api/v1/exchanges/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "binance",
    "api_key": "your-key",
    "api_secret": "your-secret"
  }'
```

### 5. Setup Backups

#### PostgreSQL Automated Backups

```bash
# Create backup script
cat > /opt/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/opt/backups
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > $BACKUP_DIR/trading_bot_$DATE.sql
# Keep only last 7 days
find $BACKUP_DIR -name "trading_bot_*.sql" -mtime +7 -delete
EOF

chmod +x /opt/backup-db.sh

# Add to cron (daily at 2 AM)
echo "0 2 * * * /opt/backup-db.sh" | crontab -
```

### 6. SSL Certificate Renewal

```bash
# Auto-renewal (already configured if using Let's Encrypt)
# Test renewal
certbot renew --dry-run
```

---

## Rollback Procedures

### AWS ECS Rollback

```bash
# List task definitions
aws ecs list-task-definitions --family-prefix backend-task

# Update service to previous task definition
aws ecs update-service \
  --cluster trading-bot-cluster \
  --service backend-service \
  --task-definition backend-task:PREVIOUS_VERSION
```

### Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment/backend -n trading-bot

# Rollback to previous version
kubectl rollout undo deployment/backend -n trading-bot

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n trading-bot
```

### Docker Compose Rollback

```bash
# Pull previous image
docker pull your-registry/trading-bot-backend:previous-tag

# Update docker-compose.yml with previous tag
# Restart services
docker-compose up -d --force-recreate
```

### Database Rollback

```bash
# Downgrade one migration
docker-compose exec backend alembic downgrade -1

# Downgrade to specific version
docker-compose exec backend alembic downgrade <revision-id>
```

---

## Troubleshooting

### Application Won't Start

**Check logs:**
```bash
# Docker Compose
docker-compose logs -f backend

# Kubernetes
kubectl logs -f deployment/backend -n trading-bot

# AWS ECS
aws logs tail /ecs/backend --follow
```

**Common issues:**
- Database connection failed → Check `DATABASE_URL`
- Redis connection failed → Check `REDIS_URL`
- Missing migrations → Run `alembic upgrade head`

### High Memory Usage

```bash
# Check container stats
docker stats

# Kubernetes
kubectl top pods -n trading-bot

# Restart memory-heavy service
docker-compose restart celery-worker
```

### Database Connection Pool Exhausted

```bash
# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size in backend/src/core/database.py
# max_overflow = 20 → max_overflow = 40
```

### Trading Bot Not Executing

**Check:**
1. Bot status: `curl https://api.yourdomain.com/api/v1/bots/<id>`
2. Celery worker status: `docker-compose logs celery-worker`
3. Exchange API credentials validity
4. API rate limits

```bash
# Check Celery tasks
docker-compose exec backend celery -A src.tasks.celery_app inspect active

# Check scheduled tasks
docker-compose exec backend celery -A src.tasks.celery_app inspect scheduled
```

### SSL Certificate Issues

```bash
# Renew certificate
certbot renew

# Check certificate expiration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com | openssl x509 -noout -dates
```

### Performance Issues

**Enable profiling:**
```bash
# Add to docker-compose.yml
environment:
  - PROFILING_ENABLED=true

# Access profiling data
curl https://api.yourdomain.com/debug/profiler
```

**Check slow queries:**
```sql
-- PostgreSQL slow query log
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor alerts in Slack/email
- Check Grafana dashboards
- Review error logs

**Weekly:**
- Review bot performance metrics
- Check database size and growth
- Review and optimize slow queries
- Update dependencies (security patches)

**Monthly:**
- Review infrastructure costs
- Optimize resource allocation
- Test backup restoration
- Review and update documentation
- Security audit

### Update Procedures

```bash
# 1. Backup database
./backup-db.sh

# 2. Pull latest code
git pull origin main

# 3. Build new images
docker-compose build

# 4. Run migrations
docker-compose exec backend alembic upgrade head

# 5. Restart services with zero-downtime
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend

# 6. Verify health
curl https://api.yourdomain.com/health
```

---

## Security Checklist

- [ ] All secrets stored in environment variables or secret management
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Firewall configured (only 80, 443, 22 open)
- [ ] Database not publicly accessible
- [ ] SSH key-based authentication only
- [ ] Regular security updates enabled
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented
- [ ] Rate limiting enabled on API
- [ ] CORS properly configured
- [ ] API keys rotated regularly

---

## Support

For issues or questions:
- Check logs first
- Review this documentation
- Check Grafana dashboards for metrics
- Open GitHub issue with full error details
