#!/bin/bash

# DigitalOcean Deployment Script for Money Trading Bot

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================="
echo "DigitalOcean Deployment"
echo "Money Trading Bot"
echo "========================================="
echo ""

# Configuration
APP_NAME="trading-bot"
REGION="nyc3"
DROPLET_SIZE="s-2vcpu-4gb"  # $24/month
DB_SIZE="db-s-1vcpu-1gb"     # $15/month
DOMAIN="${DOMAIN:-trading-bot.example.com}"

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}Error: doctl CLI is not installed${NC}"
    echo "Install from: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check authentication
echo "Checking DigitalOcean authentication..."
if ! doctl account get &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with DigitalOcean${NC}"
    echo "Run: doctl auth init"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# Create PostgreSQL Database
echo "Creating PostgreSQL database..."
DB_ID=$(doctl databases create $APP_NAME-db \
    --engine pg \
    --region $REGION \
    --size $DB_SIZE \
    --version 15 \
    --format ID \
    --no-header)

if [ -z "$DB_ID" ]; then
    echo -e "${RED}Error: Failed to create database${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Database created: $DB_ID${NC}"
echo "Waiting for database to be ready..."
doctl databases wait $DB_ID
echo ""

# Get database connection details
DB_HOST=$(doctl databases get $DB_ID --format Host --no-header)
DB_PORT=$(doctl databases get $DB_ID --format Port --no-header)
DB_USER=$(doctl databases get $DB_ID --format User --no-header)
DB_PASSWORD=$(doctl databases get $DB_ID --format Password --no-header)
DB_NAME="trading_bot"

echo "Database details:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo ""

# Create database
doctl databases db create $DB_ID $DB_NAME

# Create Droplet for application
echo "Creating application droplet..."
SSH_KEY_ID=$(doctl compute ssh-key list --format ID --no-header | head -n 1)

DROPLET_ID=$(doctl compute droplet create $APP_NAME-app \
    --size $DROPLET_SIZE \
    --image ubuntu-22-04-x64 \
    --region $REGION \
    --ssh-keys $SSH_KEY_ID \
    --format ID \
    --no-header \
    --wait)

if [ -z "$DROPLET_ID" ]; then
    echo -e "${RED}Error: Failed to create droplet${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Droplet created: $DROPLET_ID${NC}"
echo ""

# Get droplet IP
DROPLET_IP=$(doctl compute droplet get $DROPLET_ID --format PublicIPv4 --no-header)
echo "Droplet IP: $DROPLET_IP"
echo ""

# Wait for droplet to be ready
echo "Waiting for droplet to be ready..."
sleep 30

# Install Docker on droplet
echo "Installing Docker and dependencies..."
ssh -o StrictHostKeyChecking=no root@$DROPLET_IP << 'ENDSSH'
# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install git
apt-get install -y git

echo "✓ Docker installed"
ENDSSH

echo -e "${GREEN}✓ Docker installed${NC}"
echo ""

# Clone repository and setup
echo "Deploying application..."
ssh root@$DROPLET_IP << ENDSSH
# Clone repository
cd /opt
git clone https://github.com/yourusername/money-trading-bot.git
cd money-trading-bot

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=$DB_NAME

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://$DOMAIN

# Add your API keys here
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=false

UPBIT_ACCESS_KEY=
UPBIT_SECRET_KEY=
EOF

# Start services
docker-compose up -d --build

# Wait for services
sleep 20

# Run migrations
docker-compose exec -T backend alembic upgrade head

echo "✓ Application deployed"
ENDSSH

echo -e "${GREEN}✓ Application deployed${NC}"
echo ""

# Setup firewall
echo "Configuring firewall..."
doctl compute firewall create \
    --name $APP_NAME-firewall \
    --inbound-rules "protocol:tcp,ports:22,sources:addresses:0.0.0.0/0,sources:addresses:::/0 protocol:tcp,ports:80,sources:addresses:0.0.0.0/0,sources:addresses:::/0 protocol:tcp,ports:443,sources:addresses:0.0.0.0/0,sources:addresses:::/0" \
    --outbound-rules "protocol:tcp,ports:all,destinations:addresses:0.0.0.0/0,destinations:addresses:::/0 protocol:udp,ports:all,destinations:addresses:0.0.0.0/0,destinations:addresses:::/0" \
    --droplet-ids $DROPLET_ID

echo -e "${GREEN}✓ Firewall configured${NC}"
echo ""

# Create domain (if not exists)
if ! doctl compute domain get $DOMAIN &> /dev/null; then
    echo "Creating domain..."
    doctl compute domain create $DOMAIN
    echo -e "${GREEN}✓ Domain created${NC}"
fi

# Create DNS A record
echo "Creating DNS record..."
doctl compute domain records create $DOMAIN \
    --record-type A \
    --record-name @ \
    --record-data $DROPLET_IP \
    --record-ttl 3600

echo -e "${GREEN}✓ DNS record created${NC}"
echo ""

# Setup SSL with Let's Encrypt
echo "Setting up SSL certificate..."
ssh root@$DROPLET_IP << ENDSSH
# Install Certbot
apt-get install -y certbot python3-certbot-nginx

# Get certificate
certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

echo "✓ SSL certificate obtained"
ENDSSH

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Resources created:"
echo "  - Database: $DB_ID"
echo "  - Droplet: $DROPLET_ID ($DROPLET_IP)"
echo "  - Domain: $DOMAIN"
echo ""
echo "Next steps:"
echo "1. Update DNS nameservers to point to DigitalOcean"
echo "2. Add your exchange API keys to /opt/money-trading-bot/.env"
echo "3. Restart services: ssh root@$DROPLET_IP 'cd /opt/money-trading-bot && docker-compose restart'"
echo "4. Access your application at: https://$DOMAIN"
echo ""
echo "Database connection:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""
echo "Management commands:"
echo "  - SSH to droplet: ssh root@$DROPLET_IP"
echo "  - View logs: ssh root@$DROPLET_IP 'cd /opt/money-trading-bot && docker-compose logs -f'"
echo "  - Restart: ssh root@$DROPLET_IP 'cd /opt/money-trading-bot && docker-compose restart'"
echo ""
echo -e "${GREEN}Deployment successful!${NC}"
