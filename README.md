# Emerald Trading System v2.0

**Decoupled Architecture** - Production-ready cryptocurrency trading signal system.

## Architecture Overview

```
emerald/
├── common/              # Shared models and configuration
│   ├── models.py       # Pydantic data models
│   └── config.py       # Pydantic Settings configuration
├── data/               # Data fetching layer
│   └── hyperliquid_client.py
├── metrics/            # Pluggable metrics system
│   ├── base.py        # Base metric interface
│   └── implementations.py
├── strategies/         # Trading strategies
│   ├── base.py        # Base strategy interface
│   └── convergence.py # Multi-metric convergence
├── api/                # FastAPI REST endpoints
│   └── app.py
├── ui/                 # Streamlit dashboard
│   └── dashboard.py
└── backtesting/        # (Future) Backtesting framework
```

## Key Improvements Over v1.0

### 1. **Decoupled Layers**
- Business logic separated from UI
- Can run as API, CLI, or dashboard
- Easy to add new interfaces (Discord bot, Telegram, etc.)

### 2. **Pluggable Metrics**
- Each metric is self-contained
- Register/unregister metrics dynamically
- Hot-reload new metrics without touching core code

### 3. **Configuration Management**
- Pydantic Settings with .env support
- Environment-aware (dev/staging/prod)
- Type-safe configuration

### 4. **Clean Interfaces**
- `BaseMetric` for all metrics
- `BaseStrategy` for all strategies
- Easy to extend and test

### 5. **API-First Design**
- FastAPI REST endpoints
- Swagger docs at `/docs`
- Can integrate with any frontend

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Option 1: Run as API

```bash
# Start FastAPI server
python -m emerald.api.app

# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Option 2: Run Dashboard

```bash
# Start Streamlit UI
streamlit run emerald/ui/dashboard.py
```

### Option 3: Use as Library

```python
import asyncio
from emerald import HyperliquidClient, metric_registry, ConvergenceStrategy

async def analyze_btc():
    # Fetch data
    async with HyperliquidClient() as client:
        data = await client.get_market_data("BTC")

    # Calculate metrics
    metrics = metric_registry.calculate_all(data)

    # Generate signal
    strategy = ConvergenceStrategy()
    signal = strategy.generate_signal(data, metrics)

    print(f"Action: {signal.action}")
    print(f"Score: {signal.convergence_score}/100")
    print(f"Confidence: {signal.confidence}")

asyncio.run(analyze_btc())
```

## API Endpoints

### Core Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /config` - Current configuration
- `GET /coins` - List monitored coins

### Data Endpoints

- `GET /market/{coin}` - Raw market data
- `GET /metrics/{coin}` - Calculated metrics
- `GET /signal/{coin}` - Trading signal for coin
- `GET /signals` - Signals for all coins (parallel)

### Example: Get Signal

```bash
curl http://localhost:8000/signal/BTC
```

Response:
```json
{
  "action": "LONG",
  "convergence_score": 82,
  "confidence": "HIGH",
  "aligned_signals": 4,
  "entry_price": 67850.0,
  "stop_loss": 66473.0,
  "take_profit": 68867.5,
  "timestamp": "2024-11-15T03:00:00"
}
```

## Configuration

Create `.env` file:

```bash
# API Configuration
API_HYPERLIQUID_URL=https://api.hyperliquid.xyz/info
API_TIMEOUT=30

# Thresholds
THRESHOLD_ORDER_BOOK_IMBALANCE=0.4
THRESHOLD_FUNDING_EXTREME=10.0

# Signal Config
SIGNAL_MIN_CONVERGENCE_SCORE=70
SIGNAL_MIN_ALIGNED_SIGNALS=3

# UI Config
UI_REFRESH_INTERVAL_SECONDS=90
UI_COINS=["BTC","ETH","SOL"]

# App Config
APP_ENVIRONMENT=production
APP_LOG_LEVEL=INFO
```

## Adding Custom Metrics

Create a new metric:

```python
from emerald.metrics.base import BaseMetric
from emerald.common.models import MetricResult, MarketData

class MyCustomMetric(BaseMetric):
    @property
    def name(self) -> str:
        return "my_metric"

    @property
    def description(self) -> str:
        return "My custom metric"

    def calculate(self, market_data: MarketData, historical_oi=None) -> MetricResult:
        # Your calculation logic
        value = 42.0

        return MetricResult(
            name=self.name,
            value=value,
            metadata={"info": "custom"}
        )
```

Register it:

```python
from emerald.metrics import registry

registry.register(MyCustomMetric())
```

## Testing

```bash
# Test API client
python -m emerald.data.hyperliquid_client

# Test metrics
python -m emerald.metrics.implementations

# Start API server for testing
python -m emerald.api.app
```

## Roadmap

- [ ] Backtesting framework
- [ ] Performance metrics (Sharpe, max drawdown)
- [ ] Database persistence (PostgreSQL/TimescaleDB)
- [ ] Webhook notifications
- [ ] Multi-exchange support
- [ ] Machine learning signal enhancement

## Architecture Benefits

1. **Testability** - Each layer can be tested independently
2. **Maintainability** - Clear separation of concerns
3. **Extensibility** - Add metrics/strategies without touching core
4. **Scalability** - Can run distributed (API + workers)
5. **Observability** - Easy to add logging/metrics at each layer

## License

MIT
