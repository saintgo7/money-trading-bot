# Money Trading Bot - AI-Powered Trading Platform

An advanced AI-based cryptocurrency and stock automated trading platform. Users can configure strategies, and the system trades 24/7 automatically using machine learning models and technical analysis.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-14.0-black.svg)

## Features

### Core Features
- **Multi-Exchange Support**: Trade on Binance, Upbit, and more
- **AI-Powered Trading**: LSTM and Transformer models for price prediction
- **Technical Analysis**: 15+ indicators (RSI, MACD, Bollinger Bands, etc.)
- **Automated Execution**: 24/7 automated trading with Celery workers
- **Real-time Monitoring**: WebSocket-based live updates
- **Risk Management**: Stop-loss, take-profit, position sizing
- **Backtesting**: Test strategies on historical data
- **Modern Dashboard**: React-based Next.js frontend

### Trading Strategies
1. **AI Strategy**: Deep learning models (LSTM/Transformer) for predictions
2. **Technical Strategy**: Multiple indicator-based signals
3. **Hybrid Strategy**: Combined AI + Technical analysis

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL + TimescaleDB
- **AI/ML**: PyTorch, Transformers
- **Trading**: CCXT, python-binance, pyupbit
- **Technical Analysis**: TA-Lib, pandas-ta

### Frontend
- **Framework**: Next.js 14 (React)
- **Styling**: TailwindCSS
- **Charts**: Recharts
- **State**: Zustand
- **HTTP**: Axios + SWR

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes-ready
- **Cloud**: AWS/GCP compatible

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- API keys for exchanges (Binance, Upbit, etc.)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/money-trading-bot.git
cd money-trading-bot
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Initialize the database**
```bash
docker-compose exec backend python -c "from src.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup (Without Docker)

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn src.main:app --reload

# Start Celery worker (in another terminal)
celery -A src.tasks.celery_app worker --loglevel=info

# Start Celery beat (in another terminal)
celery -A src.tasks.celery_app beat --loglevel=info
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Configuration

### Exchange API Keys

Add your exchange API keys to `.env`:

```env
# Binance
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=true  # Use testnet for testing

# Upbit
UPBIT_ACCESS_KEY=your_access_key
UPBIT_SECRET_KEY=your_secret_key
```

### Database Configuration

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/trading_bot
```

### Security

Generate a secure secret key:
```bash
openssl rand -hex 32
```

Add to `.env`:
```env
SECRET_KEY=your_generated_secret_key
```

## Usage

### Creating a Trading Bot

1. **Via Dashboard**
   - Navigate to http://localhost:3000
   - Login/Register
   - Click "New Bot"
   - Configure bot settings
   - Start the bot

2. **Via API**
```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v1/auth/login',
    data={'username': 'your_username', 'password': 'your_password'})
token = response.json()['access_token']

# Create bot
headers = {'Authorization': f'Bearer {token}'}
bot_data = {
    'name': 'BTC Bot',
    'exchange': 'binance',
    'trading_pair': 'BTC/USDT',
    'initial_capital': 10000,
    'max_position_size': 10.0,
    'stop_loss_percentage': 5.0,
    'take_profit_percentage': 10.0
}
response = requests.post('http://localhost:8000/api/v1/bots/',
    json=bot_data, headers=headers)

# Start bot
bot_id = response.json()['id']
requests.post(f'http://localhost:8000/api/v1/bots/{bot_id}/start',
    headers=headers)
```

### Creating Custom Strategies

Create a custom strategy in `backend/src/strategies/`:

```python
from .trading_engine import TradingEngine

class MyCustomStrategy(TradingEngine):
    async def _custom_signal(self, df):
        # Your custom logic here
        signal = "buy"  # or "sell" or "hold"
        confidence = 0.8
        return {
            "signal": signal,
            "confidence": confidence,
            "reasoning": "Custom strategy logic"
        }
```

## API Documentation

Full API documentation available at: http://localhost:8000/docs

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

#### Trading Bots
- `GET /api/v1/bots/` - List all bots
- `POST /api/v1/bots/` - Create bot
- `GET /api/v1/bots/{id}` - Get bot details
- `POST /api/v1/bots/{id}/start` - Start bot
- `POST /api/v1/bots/{id}/stop` - Stop bot
- `GET /api/v1/bots/{id}/performance` - Get performance metrics

#### Market Data
- `GET /api/v1/market/ticker/{exchange}/{symbol}` - Get ticker
- `GET /api/v1/market/candles/{exchange}/{symbol}` - Get OHLCV data
- `GET /api/v1/market/orderbook/{exchange}/{symbol}` - Get order book

## Architecture

```
money-trading-bot/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── exchanges/      # Exchange connectors
│   │   ├── models/         # Database models
│   │   ├── strategies/     # Trading strategies
│   │   ├── tasks/          # Celery tasks
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities
│   │   └── types/         # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Trading Flow

1. **Market Analysis**: Fetch OHLCV data and calculate indicators
2. **Signal Generation**: AI model + technical analysis generate signals
3. **Risk Management**: Check position size, stop-loss, take-profit
4. **Order Execution**: Place orders on exchange
5. **Monitoring**: Track positions and performance
6. **Automated Cycles**: Celery runs trading cycles periodically

## Performance Metrics

The platform tracks:
- Total trades
- Win rate
- Profit & Loss (P&L)
- Return on Investment (ROI)
- Sharpe ratio
- Maximum drawdown
- Average trade duration

## Safety Features

- **Paper Trading**: Test strategies without real money (use testnet)
- **Position Limits**: Maximum position size per trade
- **Stop Loss**: Automatic loss prevention
- **Take Profit**: Lock in profits automatically
- **Daily Loss Limit**: Stop trading after max daily loss
- **Health Checks**: Monitor bot health and stop if issues detected

## Development

### Running Tests
```bash
cd backend
pytest tests/
```

### Code Formatting
```bash
# Backend
black backend/src/
isort backend/src/

# Frontend
cd frontend
npm run lint
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG=false` in `.env`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure proper CORS origins
- [ ] Use production database (not SQLite)
- [ ] Enable HTTPS/SSL
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure backup strategy
- [ ] Use environment-specific API keys
- [ ] Enable rate limiting
- [ ] Set up logging aggregation

### Deploy to AWS/GCP

See [docs/deployment.md](docs/deployment.md) for detailed deployment guides.

## Monitoring

Access monitoring dashboards:
- **Celery Flower**: http://localhost:5555 (add to docker-compose)
- **Application Logs**: `docker-compose logs -f`
- **Database**: Connect via pgAdmin or similar tools

## Troubleshooting

### Common Issues

**Bot not starting:**
- Check exchange API keys are valid
- Verify sufficient balance
- Check bot configuration

**Database connection errors:**
- Ensure PostgreSQL is running
- Verify `DATABASE_URL` in `.env`

**Celery tasks not running:**
- Check Redis connection
- Verify Celery worker is running
- Check task logs

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## Disclaimer

**IMPORTANT**: This software is for educational purposes only. Trading cryptocurrencies and stocks carries significant risk.

- Use at your own risk
- Start with paper trading (testnet)
- Never invest more than you can afford to lose
- Past performance does not guarantee future results
- The developers are not responsible for any financial losses

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: https://github.com/yourusername/money-trading-bot/issues
- **Discussions**: https://github.com/yourusername/money-trading-bot/discussions

## Roadmap

- [ ] More exchange integrations (Coinbase, Kraken, etc.)
- [ ] Advanced AI models (Reinforcement Learning)
- [ ] Sentiment analysis from social media
- [ ] Mobile app (React Native)
- [ ] Portfolio optimization
- [ ] Copy trading features
- [ ] Strategy marketplace
- [ ] Advanced backtesting with multiple metrics
- [ ] Multi-asset portfolio support
- [ ] Advanced risk management tools

## Acknowledgments

- [CCXT](https://github.com/ccxt/ccxt) - Cryptocurrency exchange library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Next.js](https://nextjs.org/) - React framework
- [PyTorch](https://pytorch.org/) - Machine learning framework

---

**Made with ❤️ for algorithmic traders**
