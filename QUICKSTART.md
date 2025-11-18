# Quick Start Guide

Get your Money Trading Bot up and running in 5 minutes!

## 1. Prerequisites

- Docker & Docker Compose installed
- Exchange API keys (optional for paper trading)

## 2. Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/money-trading-bot.git
cd money-trading-bot

# Copy environment file
cp .env.example .env

# (Optional) Edit .env with your API keys
nano .env
```

## 3. Start Services

```bash
# Build and start all services
docker-compose up -d

# Wait for services to be ready (30 seconds)
sleep 30

# Initialize database
docker-compose exec backend python -c "from src.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

## 4. Access the Platform

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 5. Create Your First Bot

### Via Web Dashboard

1. Open http://localhost:3000
2. Register a new account
3. Click "New Bot"
4. Fill in the form:
   - Name: My First Bot
   - Exchange: binance
   - Trading Pair: BTC/USDT
   - Initial Capital: 10000
   - Click "Create"
5. Click "Start" to activate the bot

### Via API (cURL)

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"trader","password":"secret123"}'

# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=trader&password=secret123" | jq -r .access_token)

# Create Bot
curl -X POST http://localhost:8000/api/v1/bots/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "BTC Bot",
    "exchange": "binance",
    "trading_pair": "BTC/USDT",
    "initial_capital": 10000,
    "max_position_size": 10.0,
    "stop_loss_percentage": 5.0,
    "take_profit_percentage": 10.0
  }'

# Start Bot (replace {bot_id} with actual ID)
curl -X POST http://localhost:8000/api/v1/bots/1/start \
  -H "Authorization: Bearer $TOKEN"
```

## 6. Monitor Your Bot

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Celery worker
docker-compose logs -f celery_worker
```

### Check Bot Status
```bash
# Via API
curl -X GET http://localhost:8000/api/v1/bots/1 \
  -H "Authorization: Bearer $TOKEN"

# Via Dashboard
# Open http://localhost:3000/dashboard
```

## 7. Test with Paper Trading

The platform supports paper trading (no real money) using testnet APIs.

**Binance Testnet:**
1. Get testnet API keys from https://testnet.binance.vision/
2. Add to `.env`:
   ```
   BINANCE_API_KEY=your_testnet_key
   BINANCE_API_SECRET=your_testnet_secret
   BINANCE_TESTNET=true
   ```
3. Restart: `docker-compose restart`

## 8. Useful Commands

```bash
# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps

# Access backend shell
docker-compose exec backend /bin/bash

# Run tests
docker-compose exec backend pytest

# Clean everything (including data)
docker-compose down -v
```

## 9. Troubleshooting

**Services not starting:**
```bash
docker-compose down
docker-compose up -d
docker-compose logs
```

**Database issues:**
```bash
docker-compose down -v
docker-compose up -d
# Wait 30 seconds then initialize again
```

**Frontend not loading:**
```bash
docker-compose restart frontend
docker-compose logs frontend
```

## 10. Next Steps

- Read the full [README.md](README.md)
- Explore API docs at http://localhost:8000/docs
- Create custom trading strategies
- Configure risk management parameters
- Set up monitoring and alerts

## Getting Help

- GitHub Issues: https://github.com/yourusername/money-trading-bot/issues
- Documentation: [docs/](docs/)

---

**Happy Trading! 🚀**
