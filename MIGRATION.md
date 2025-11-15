# Migration Guide: v1.0 → v2.0

## What Changed

### Architecture: Monolithic → Layered

**Before (v1.0):**
```
strategy_monitor/
├── app.py              # 503 lines - UI + business logic
├── metrics.py          # 370 lines - hardcoded metrics
├── signal_generator.py # 374 lines - hardcoded scoring
├── api_client.py       # 365 lines - mixed concerns
└── storage.py          # 478 lines - over-engineered
```

**After (v2.0):**
```
emerald/
├── common/          # Shared models & config
├── data/            # API clients (clean)
├── metrics/         # Pluggable metrics
├── strategies/      # Pluggable strategies
├── api/             # FastAPI REST endpoints
└── ui/              # Streamlit (decoupled)
```

## Key Improvements

### 1. Decoupled Architecture
- **Before:** Streamlit UI tightly coupled with business logic
- **After:** Clean separation - can run as API, CLI, or dashboard

### 2. Pluggable Metrics
- **Before:** All metrics hardcoded in single class
- **After:** Each metric is self-contained, can hot-reload new metrics

### 3. Configuration Management
- **Before:** Static config.py file
- **After:** Pydantic Settings with .env support, environment-aware

### 4. Type Safety
- **Before:** Partial type hints, dict-heavy
- **After:** Full Pydantic models, type-safe everywhere

### 5. API-First Design
- **Before:** No API, only Streamlit
- **After:** FastAPI with Swagger docs, can integrate anywhere

## Migration Steps

### Option 1: Fresh Start (Recommended)

Use the new v2.0 architecture:

```bash
# Install new dependencies
pip install -r requirements.txt

# Run as API
python -m emerald.api.app

# Or run as dashboard
streamlit run emerald/ui/dashboard.py
```

### Option 2: Gradual Migration

Keep v1.0 running while migrating:

1. **Phase 1: Migrate data layer**
   - Replace `api_client.py` imports with `emerald.data.hyperliquid_client`
   - Use `MarketData` models instead of dicts

2. **Phase 2: Migrate metrics**
   - Register v1 metrics in v2 registry
   - Gradually replace with new metric implementations

3. **Phase 3: Migrate UI**
   - Move Streamlit to consume v2 API
   - Remove embedded business logic

### Option 3: Hybrid Approach

Run both versions:

- **v2.0 API** for new integrations (webhooks, bots)
- **v1.0 Dashboard** until full migration

## Breaking Changes

### Data Models

**Before:**
```python
# Dict-based
data = {
    "order_book": {...},
    "perp_data": {...}
}
```

**After:**
```python
# Pydantic models
from emerald.common.models import MarketData

data = MarketData(...)
data.perp_data.funding_rate  # Type-safe access
```

### Configuration

**Before:**
```python
from config import COINS, THRESHOLDS
```

**After:**
```python
from emerald.common.config import get_config

config = get_config()
coins = config.ui.coins
threshold = config.thresholds.funding_extreme
```

### Metrics Calculation

**Before:**
```python
from metrics import MetricsCalculator

calc = MetricsCalculator()
metrics = calc.calculate_all_metrics(...)
```

**After:**
```python
from emerald.metrics import registry

metrics = registry.calculate_all(market_data, historical_oi)
```

### Signal Generation

**Before:**
```python
from signal_generator import SignalGenerator

gen = SignalGenerator()
signal = gen.generate_signal(metrics)
```

**After:**
```python
from emerald.strategies import ConvergenceStrategy

strategy = ConvergenceStrategy()
signal = strategy.generate_signal(market_data, metrics)
```

## Code Comparison

### Example: Analyze BTC

**Before (v1.0):**
```python
import asyncio
from api_client import HyperliquidClient
from metrics import MetricsCalculator
from signal_generator import SignalGenerator

async def analyze():
    async with HyperliquidClient() as client:
        data = await client.get_all_data("BTC")

    calc = MetricsCalculator()
    metrics = calc.calculate_all_metrics(
        data['order_book'],
        data['perp_data'],
        data['spot_data'],
        data['candles'],
        None
    )

    gen = SignalGenerator()
    signal = gen.generate_signal(metrics)

    print(signal['action'])

asyncio.run(analyze())
```

**After (v2.0):**
```python
import asyncio
from emerald import HyperliquidClient, metric_registry, ConvergenceStrategy

async def analyze():
    async with HyperliquidClient() as client:
        market_data = await client.get_market_data("BTC")

    metrics = metric_registry.calculate_all(market_data)
    strategy = ConvergenceStrategy()
    signal = strategy.generate_signal(market_data, metrics)

    print(signal.action.value)

asyncio.run(analyze())
```

### Example: Add Custom Metric

**Before (v1.0):**
```python
# Edit metrics.py, add method to MetricsCalculator
# Edit signal_generator.py to use new metric
# Restart everything
```

**After (v2.0):**
```python
from emerald.metrics.base import BaseMetric
from emerald.metrics import registry

class MyMetric(BaseMetric):
    @property
    def name(self) -> str:
        return "my_metric"

    def calculate(self, market_data, historical_oi=None):
        # Your logic
        return MetricResult(name=self.name, value=42.0)

# Register it
registry.register(MyMetric())

# Done! No need to modify core code
```

## Advantages of v2.0

1. **Testability** - Each layer independently testable
2. **Maintainability** - Clear responsibilities
3. **Extensibility** - Add metrics/strategies without touching core
4. **Scalability** - Can run distributed (API + workers)
5. **Observability** - Easy to add logging at each layer

## Compatibility

### What Still Works

- ✅ Same trading logic (convergence strategy)
- ✅ Same metrics calculations
- ✅ Same Hyperliquid API client logic
- ✅ Same configuration values

### What's Deprecated

- ❌ `strategy_monitor/app.py` (use `emerald/ui/dashboard.py`)
- ❌ Direct dict access (use Pydantic models)
- ❌ Static config imports (use `get_config()`)
- ❌ Hardcoded metrics (use registry)

## Rollback Plan

If issues arise, keep v1.0 intact:

```bash
# v1.0 still exists in strategy_monitor/
cd strategy_monitor
streamlit run app_phase2.py
```

## Support

- **Documentation:** See README_v2.md
- **Tests:** Run `python test_system.py`
- **API Docs:** Run API and visit http://localhost:8000/docs

## Timeline

- **Day 1-2:** Deploy v2.0 API, test in parallel
- **Day 3-5:** Migrate UI consumers to v2.0 API
- **Day 6-7:** Deprecate v1.0 dashboard
- **Week 2:** Remove v1.0 code after validation
