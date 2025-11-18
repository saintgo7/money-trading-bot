# Money Trading Bot - API Architecture

## Overview

This document describes the API architecture and design patterns used in the Money Trading Bot platform.

## Architecture Layers

### 1. API Layer (`src/api/`)
- **Purpose**: Handle HTTP requests and responses
- **Components**:
  - Route handlers
  - Request validation (Pydantic models)
  - Response formatting
  - Error handling

### 2. Service Layer (`src/services/`)
- **Purpose**: Business logic and orchestration
- **Components**:
  - Trading logic
  - Strategy execution
  - Risk management
  - Order management

### 3. Data Layer (`src/models/`)
- **Purpose**: Data persistence and retrieval
- **Components**:
  - SQLAlchemy models
  - Database schemas
  - Relationships

### 4. Integration Layer (`src/exchanges/`)
- **Purpose**: External service integration
- **Components**:
  - Exchange connectors
  - API clients
  - Data transformation

## API Endpoints

### Authentication
```
POST /api/v1/auth/register  - Register new user
POST /api/v1/auth/login     - Login and get token
GET  /api/v1/auth/me        - Get current user
```

### Trading Bots
```
GET    /api/v1/bots/              - List all bots
POST   /api/v1/bots/              - Create new bot
GET    /api/v1/bots/{id}          - Get bot details
PATCH  /api/v1/bots/{id}          - Update bot
DELETE /api/v1/bots/{id}          - Delete bot
POST   /api/v1/bots/{id}/start    - Start bot
POST   /api/v1/bots/{id}/stop     - Stop bot
GET    /api/v1/bots/{id}/orders   - Get bot orders
GET    /api/v1/bots/{id}/trades   - Get bot trades
GET    /api/v1/bots/{id}/performance - Get performance metrics
```

### Strategies
```
GET    /api/v1/strategies/        - List all strategies
POST   /api/v1/strategies/        - Create strategy
GET    /api/v1/strategies/{id}    - Get strategy
PATCH  /api/v1/strategies/{id}    - Update strategy
DELETE /api/v1/strategies/{id}    - Delete strategy
```

### Market Data
```
GET /api/v1/market/ticker/{exchange}/{symbol}      - Get ticker
GET /api/v1/market/candles/{exchange}/{symbol}     - Get OHLCV
GET /api/v1/market/orderbook/{exchange}/{symbol}   - Get order book
GET /api/v1/market/exchanges                       - List exchanges
GET /api/v1/market/trading-pairs/{exchange}        - Get trading pairs
```

## Authentication Flow

1. User registers: `POST /api/v1/auth/register`
2. User logs in: `POST /api/v1/auth/login` → Receives JWT token
3. User includes token in subsequent requests: `Authorization: Bearer <token>`
4. Backend validates token and extracts user information

## Trading Flow

1. **Bot Creation**
   - User creates bot with parameters
   - Bot stored in database with status "stopped"

2. **Bot Activation**
   - User starts bot: `POST /api/v1/bots/{id}/start`
   - Bot status changed to "running"
   - Celery task scheduled

3. **Trading Cycle** (Celery Worker)
   ```python
   1. Fetch market data
   2. Calculate technical indicators
   3. Generate AI predictions
   4. Combine signals
   5. Check risk management rules
   6. Execute trades if conditions met
   7. Update database
   8. Schedule next cycle
   ```

4. **Order Execution**
   - Place order on exchange
   - Store order in database
   - Monitor order status
   - Update positions

5. **Risk Management**
   - Check stop-loss conditions
   - Check take-profit conditions
   - Monitor daily loss limits
   - Execute protective orders if needed

## Database Schema

### Users
```sql
- id (PK)
- email
- username
- hashed_password
- subscription_tier
- created_at
```

### TradingBots
```sql
- id (PK)
- owner_id (FK → users.id)
- name
- exchange
- trading_pair
- status (stopped/running/paused/error)
- initial_capital
- current_capital
- strategy_id (FK → strategies.id)
- risk_parameters (JSON)
- performance_metrics
- created_at, updated_at
```

### Orders
```sql
- id (PK)
- bot_id (FK → trading_bots.id)
- exchange_order_id
- symbol
- side (buy/sell)
- order_type
- quantity, price
- status
- filled_quantity
- created_at, filled_at
```

### Trades
```sql
- id (PK)
- bot_id (FK → trading_bots.id)
- entry_order_id, exit_order_id
- entry_price, exit_price
- quantity
- profit_loss
- is_open
- created_at, closed_at
```

## Security

### Authentication
- JWT tokens with expiration
- Password hashing with bcrypt
- Token refresh mechanism

### Authorization
- User can only access their own resources
- Dependency injection for user verification

### API Security
- CORS configuration
- Rate limiting (TODO)
- Input validation
- SQL injection prevention (SQLAlchemy ORM)

## Error Handling

### HTTP Status Codes
- `200 OK` - Successful GET/PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid token
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "detail": "Error message",
  "error": "Additional error info"
}
```

## Performance Optimization

### Database
- Connection pooling
- Async queries
- Indexes on frequently queried fields
- TimescaleDB for time-series data

### Caching
- Redis for session storage
- Celery result caching
- Market data caching

### Background Processing
- Celery for async tasks
- Celery Beat for scheduled tasks
- Worker autoscaling

## Monitoring

### Logging
- Structured logging with loguru
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request/response logging

### Metrics
- Trading performance
- Order execution time
- API response time
- Error rates

## Deployment

### Docker
- Multi-container setup
- Service isolation
- Volume management
- Health checks

### Environment Variables
- All sensitive data in `.env`
- Different configs for dev/prod
- Secret management

## Future Improvements

- [ ] WebSocket for real-time updates
- [ ] GraphQL API
- [ ] API rate limiting
- [ ] Advanced backtesting
- [ ] Multi-user collaboration
- [ ] Strategy marketplace
- [ ] Mobile API endpoints
- [ ] Webhook integrations
