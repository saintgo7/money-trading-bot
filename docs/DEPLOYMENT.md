# Deployment Guide

Complete guide for deploying Money Trading Bot to production environments.

## Prerequisites

- Docker & Docker Compose
- Domain name (optional but recommended)
- SSL certificate (Let's Encrypt or similar)
- Cloud provider account (AWS, GCP, Azure, or DigitalOcean)

## Environment Setup

### 1. Production Environment Variables

Create `.env` file with production settings:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:STRONG_PASSWORD@db:5432/trading_bot
POSTGRES_USER=user
POSTGRES_PASSWORD=STRONG_PASSWORD  # Change this!
POSTGRES_DB=trading_bot

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=$(openssl rand -hex 32)  # Generate strong secret key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com

# Exchange API Keys
BINANCE_API_KEY=your_production_binance_key
BINANCE_API_SECRET=your_production_binance_secret
BINANCE_TESTNET=false

UPBIT_ACCESS_KEY=your_upbit_key
UPBIT_SECRET_KEY=your_upbit_secret

# Optional: Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Deployment Options

### Option 1: Docker Compose (Simple)

**Best for:** Small to medium deployments, single server

```bash
# 1. Clone repository
git clone https://github.com/yourusername/money-trading-bot.git
cd money-trading-bot

# 2. Set up environment
cp .env.example .env
nano .env  # Edit with production values

# 3. Build and start services
docker-compose up -d --build

# 4. Initialize database
docker-compose exec backend alembic upgrade head

# 5. Create initial admin user (optional)
docker-compose exec backend python -c "
from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.core.security import get_password_hash
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            email='admin@example.com',
            username='admin',
            hashed_password=get_password_hash('changeme'),
            is_superuser=True
        )
        db.add(admin)
        await db.commit()

asyncio.run(create_admin())
"
```

### Option 2: Kubernetes (Advanced)

**Best for:** Large scale, high availability

Create Kubernetes manifests:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-bot-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trading-bot-backend
  template:
    metadata:
      labels:
        app: trading-bot-backend
    spec:
      containers:
      - name: backend
        image: your-registry/trading-bot-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trading-bot-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: trading-bot-backend
spec:
  selector:
    app: trading-bot-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy to Kubernetes:

```bash
# Create secrets
kubectl create secret generic trading-bot-secrets \
  --from-literal=database-url='postgresql+asyncpg://...' \
  --from-literal=secret-key='...'

# Deploy
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services
```

### Option 3: AWS (Elastic Beanstalk)

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker money-trading-bot

# Create environment
eb create trading-bot-prod

# Deploy
eb deploy

# Set environment variables
eb setenv DATABASE_URL="..." SECRET_KEY="..."

# View logs
eb logs
```

### Option 4: DigitalOcean App Platform

1. Connect your GitHub repository
2. Select the repository
3. Configure build settings:
   - **Backend**: Dockerfile at `backend/Dockerfile`
   - **Frontend**: Dockerfile at `frontend/Dockerfile`
4. Add environment variables
5. Deploy

## Database Setup

### PostgreSQL + TimescaleDB

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create TimescaleDB hypertable for time-series data
docker-compose exec postgres psql -U user -d trading_bot -c "
SELECT create_hypertable('market_data', 'timestamp');
"

# Set up retention policy (keep 90 days)
docker-compose exec postgres psql -U user -d trading_bot -c "
SELECT add_retention_policy('market_data', INTERVAL '90 days');
"
```

## SSL/HTTPS Setup

### Using Let's Encrypt with Nginx

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/trading-bot
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring Setup

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'trading-bot'
    static_configs:
      - targets: ['backend:8000']
```

## Backup Strategy

### Database Backups

```bash
# Create backup script
cat > backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="trading_bot_$DATE.sql"

docker-compose exec -T postgres pg_dump -U user trading_bot > "$BACKUP_DIR/$FILENAME"
gzip "$BACKUP_DIR/$FILENAME"

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $FILENAME.gz"
EOF

chmod +x backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
# Restore database
gunzip backup.sql.gz
docker-compose exec -T postgres psql -U user -d trading_bot < backup.sql
```

## Performance Optimization

### 1. Database Connection Pooling

Already configured in `database.py`:
- Pool size: 10
- Max overflow: 20

### 2. Redis Caching

Enable caching for market data:

```python
# In your code
import redis
cache = redis.from_url(settings.REDIS_URL)

# Cache market data for 1 minute
cache.setex(f"ticker:{symbol}", 60, json.dumps(ticker_data))
```

### 3. Celery Worker Scaling

```bash
# Scale workers
docker-compose up -d --scale celery_worker=5
```

### 4. Load Balancing

Use nginx for load balancing multiple backend instances.

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall (UFW, security groups)
- [ ] Regular security updates
- [ ] Enable database encryption
- [ ] Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- [ ] Implement rate limiting
- [ ] Set up fail2ban
- [ ] Regular backups
- [ ] Monitor logs for suspicious activity

## Monitoring & Alerting

### Set Up Alerts

```python
# Add to your code
from prometheus_client import Counter, Histogram

trade_counter = Counter('trades_total', 'Total number of trades')
trade_latency = Histogram('trade_latency_seconds', 'Trade execution latency')
```

### Log Aggregation

Use ELK Stack or similar:

```yaml
# docker-compose.logging.yml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"

  logstash:
    image: logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
```

## Scaling Strategies

### Horizontal Scaling

1. **Add more backend replicas**
   ```bash
   docker-compose up -d --scale backend=3
   ```

2. **Use load balancer** (nginx, HAProxy)

3. **Database read replicas**
   - Master for writes
   - Replicas for reads

### Vertical Scaling

Increase resource limits:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Troubleshooting

### Common Issues

**1. Database connection failed**
```bash
# Check database status
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U user -d trading_bot
```

**2. Celery workers not processing**
```bash
# Check worker status
docker-compose logs celery_worker

# Inspect tasks
docker-compose exec redis redis-cli
> KEYS celery*
```

**3. High memory usage**
```bash
# Check container stats
docker stats

# Restart services
docker-compose restart
```

## Maintenance

### Regular Tasks

- **Daily**: Check logs, monitor performance
- **Weekly**: Review trading performance, update strategies
- **Monthly**: Security updates, backup verification
- **Quarterly**: Performance optimization, cost analysis

### Update Deployment

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head
```

## Cost Optimization

### AWS Cost Estimates

- **t3.medium** EC2: ~$30/month
- **RDS PostgreSQL**: ~$50/month
- **ElastiCache Redis**: ~$20/month
- **Total**: ~$100-150/month

### DigitalOcean

- **Droplet (4GB RAM)**: ~$24/month
- **Managed Database**: ~$15/month
- **Total**: ~$40-50/month

## Support

- Documentation: https://docs.yourdomain.com
- Issues: https://github.com/yourusername/money-trading-bot/issues
- Email: support@yourdomain.com
