# Configuration Reference

All configurable parameters live in `config/settings.py`. This provides a single source of truth for system behavior.

---

## Quick Reference

```python
# Import configuration
from config.settings import (
    AGENT_CONFIG,
    IE_CONFIG,
    TOOL_CONFIG,
    INTERVAL_CONSTRAINTS,
    get_interval_constraint
)
```

---

## Interval Constraints

### Purpose
Defines API data availability limits for each candle interval.

### Structure

```python
INTERVAL_CONSTRAINTS = {
    "1m": IntervalConstraints(
        max_lookback_hours=1.5,
        interval_minutes=1,
        max_candles=250
    ),
    "5m": IntervalConstraints(
        max_lookback_hours=6.0,
        interval_minutes=5,
        max_candles=250
    ),
    "15m": IntervalConstraints(
        max_lookback_hours=24.0,
        interval_minutes=15,
        max_candles=250
    ),
    "1h": IntervalConstraints(
        max_lookback_hours=72.0,
        interval_minutes=60,
        max_candles=250
    ),
    "4h": IntervalConstraints(
        max_lookback_hours=336.0,
        interval_minutes=240,
        max_candles=250
    ),
    "1d": IntervalConstraints(
        max_lookback_hours=2160.0,
        interval_minutes=1440,
        max_candles=250
    ),
}
```

### Usage

```python
# Get constraints for specific interval
constraints = get_interval_constraint("1m")

if requested_hours > constraints.max_lookback_hours:
    # Adjust to maximum
    actual_hours = constraints.max_lookback_hours
```

### Customization

Edit values to match your needs:

```python
# Allow more 1m history
"1m": IntervalConstraints(max_lookback_hours=3.0, ...)

# Reduce 15m history to save bandwidth
"15m": IntervalConstraints(max_lookback_hours=12.0, ...)
```

---

## Agent Configuration

### Purpose
Controls agent behavior, model parameters, and tool usage limits.

### Structure

```python
@dataclass
class AgentConfig:
    max_tool_calls_per_response: int = 3
    max_iterations: int = 5
    model_temperature: float = 0.25
    max_tokens: int = 2048
    model_timeout: int = 45
    max_retries: int = 2
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_tool_calls_per_response` | 3 | Maximum tools agent can call in one response (prevents spam) |
| `max_iterations` | 5 | Maximum reasoning loops before forced completion |
| `model_temperature` | 0.25 | Creativity (0.0=deterministic, 1.0=creative) |
| `max_tokens` | 2048 | Maximum response length |
| `model_timeout` | 45 | Seconds before API timeout |
| `max_retries` | 2 | API call retry attempts on failure |

### Tuning Guide

**For faster responses**:
```python
max_iterations=3          # Reduce reasoning depth
model_temperature=0.1     # More deterministic
max_tokens=1024           # Shorter responses
```

**For deeper analysis**:
```python
max_iterations=7          # More reasoning
model_temperature=0.4     # More creative connections
max_tokens=4096           # Longer responses
```

**For conservative API usage**:
```python
max_tool_calls_per_response=2  # Fewer tool calls
max_retries=1             # Don't retry failures
model_timeout=30          # Fail faster
```

---

## Institutional Engine Configuration

### Purpose
Controls metric thresholds, cache TTLs, and convergence scoring.

### Structure

```python
@dataclass
class IEConfig:
    # Cache TTLs (seconds)
    order_book_cache_ttl: int = 2
    funding_cache_ttl: int = 300
    oi_cache_ttl: int = 300
    basis_cache_ttl: int = 10
    trade_flow_cache_ttl: int = 60

    # Metric thresholds
    strong_imbalance_threshold: float = 0.4
    extreme_funding_threshold_pct: float = 10.0
    extreme_basis_threshold_pct: float = 0.3
    extreme_z_score: float = 2.0

    # Volume thresholds
    high_volume_ratio: float = 1.5
    low_volume_ratio: float = 0.6

    # Convergence weights
    order_book_weight: int = 25
    trade_flow_weight: int = 25
    funding_weight: int = 20
    oi_weight: int = 30
    vwap_weight: int = 25

    # Grading thresholds
    a_plus_threshold: int = 70
    a_threshold: int = 50
    b_threshold: int = 30

    # Phase 2 thresholds
    spoof_min_appearances: int = 3
    iceberg_min_refills: int = 3
    cascade_min_liquidations: int = 5
    arb_threshold_pct: float = 0.1
```

### Cache TTLs

**Purpose**: Prevent API spam while maintaining freshness

| Metric | Default TTL | Rationale |
|--------|-------------|-----------|
| Order Book | 2s | Changes every second (real-time) |
| Funding | 300s (5min) | Only updates every 8 hours |
| Open Interest | 300s (5min) | Slow updates |
| Basis | 10s | Moderate price changes |
| Trade Flow | 60s (1min) | Candle-based (1min candles) |

**Tuning**:
```python
# More aggressive (fresher data, more API calls)
order_book_cache_ttl=1
basis_cache_ttl=5
trade_flow_cache_ttl=30

# More conservative (less API calls, slightly stale data)
order_book_cache_ttl=5
basis_cache_ttl=30
trade_flow_cache_ttl=120
```

### Metric Thresholds

**Purpose**: Define when metrics are "extreme" and contribute to convergence score

#### Order Book Imbalance
```python
strong_imbalance_threshold=0.4  # |imbalance| > 0.4 = strong pressure

# More sensitive (triggers more often)
strong_imbalance_threshold=0.3

# Less sensitive (higher conviction required)
strong_imbalance_threshold=0.5
```

#### Funding Rate
```python
extreme_funding_threshold_pct=10.0  # >10% annualized = extreme

# More sensitive
extreme_funding_threshold_pct=7.0

# Less sensitive
extreme_funding_threshold_pct=15.0
```

#### Perpetuals Basis
```python
extreme_basis_threshold_pct=0.3  # >0.3% deviation = extreme

# More sensitive
extreme_basis_threshold_pct=0.2

# Less sensitive
extreme_basis_threshold_pct=0.5
```

#### VWAP Z-Score
```python
extreme_z_score=2.0  # >2σ = statistical extreme

# More sensitive (1.5σ standard deviations)
extreme_z_score=1.5

# Less sensitive (2.5σ = very extreme)
extreme_z_score=2.5
```

### Convergence Weights

**Purpose**: Determines how many points each metric contributes to 0-100 score

**Default distribution**:
```python
order_book_weight=25   # 25 points max
trade_flow_weight=25   # 25 points max
funding_weight=20      # 20 points max
oi_weight=30           # 30 points max (most important)
vwap_weight=25         # 25 points max

# Total possible: 100+ (but capped at 100)
```

**Custom weighting example**:
```python
# Emphasize order book and trade flow (real-time signals)
order_book_weight=30
trade_flow_weight=30
funding_weight=15
oi_weight=15
vwap_weight=10

# Emphasize OI and funding (positioning signals)
order_book_weight=15
trade_flow_weight=15
funding_weight=30
oi_weight=35
vwap_weight=5
```

### Grading Thresholds

**Purpose**: Convert convergence scores to letter grades (A+/A/B/C)

```python
a_plus_threshold=70  # 70+ = A+ (high conviction)
a_threshold=50       # 50-69 = A (good setup)
b_threshold=30       # 30-49 = B (acceptable)
# <30 = C (skip)
```

**More conservative** (only trade best setups):
```python
a_plus_threshold=80  # Raise bar for A+
a_threshold=60       # Raise bar for A
b_threshold=40       # Raise bar for B
```

**More aggressive** (trade more setups):
```python
a_plus_threshold=60  # Lower bar for A+
a_threshold=40       # Lower bar for A
b_threshold=20       # Lower bar for B
```

### Phase 2 Thresholds

#### Spoofing Detection
```python
spoof_min_appearances=3  # Order must appear 3+ times to qualify

# More sensitive (detect subtle spoofing)
spoof_min_appearances=2

# Less sensitive (only obvious spoofing)
spoof_min_appearances=5
```

#### Iceberg Orders
```python
iceberg_min_refills=3  # Order must refill 3+ times

# More sensitive
iceberg_min_refills=2

# Less sensitive
iceberg_min_refills=4
```

#### Liquidation Cascades
```python
cascade_min_liquidations=5  # 5+ liquidations in 5 min = cascade

# More sensitive
cascade_min_liquidations=3

# Less sensitive
cascade_min_liquidations=10
```

#### Cross-Exchange Arbitrage
```python
arb_threshold_pct=0.1  # >0.1% deviation triggers signal

# More sensitive (more arb signals)
arb_threshold_pct=0.05

# Less sensitive (only significant deviations)
arb_threshold_pct=0.2
```

---

## Tool Configuration

### Purpose
API connection settings and data fetching defaults.

### Structure

```python
@dataclass
class ToolConfig:
    api_url: str = "https://api.hyperliquid.xyz/info"
    request_timeout: int = 15
    max_candles_absolute: int = 250
    default_output_subdir: str = "agent_outputs"
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_url` | `https://api.hyperliquid.xyz/info` | Hyperliquid API endpoint |
| `request_timeout` | 15 | Seconds before API timeout |
| `max_candles_absolute` | 250 | Hard cap on candles per request |
| `default_output_subdir` | `agent_outputs` | Where to save generated files |

### Tuning

**For slower networks**:
```python
request_timeout=30  # More patient
```

**For more data per request**:
```python
max_candles_absolute=500  # Doubles data (but slower, more API load)
```

---

## Environment Variables

### Required

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your key from: https://console.anthropic.com/

### Optional

```bash
# Custom API endpoint (if using proxy)
HYPERLIQUID_API_URL=https://your-proxy.com/info

# Custom conversations directory
CONVERSATIONS_DIR=/custom/path/conversations

# Custom agent outputs directory
AGENT_OUTPUTS_DIR=/custom/path/outputs
```

---

## Configuration Examples

### Example 1: Conservative Trading (High Conviction Only)

```python
# config/settings.py

IE_CONFIG = IEConfig(
    # Stricter thresholds
    strong_imbalance_threshold=0.5,      # Higher bar
    extreme_funding_threshold_pct=15.0,  # Only extreme extremes
    extreme_z_score=2.5,                 # Very stretched

    # Stricter grading
    a_plus_threshold=80,  # 80+ for A+
    a_threshold=65,       # 65+ for A
    b_threshold=50,       # 50+ for B

    # Longer caches (less data churn)
    order_book_cache_ttl=5,
    trade_flow_cache_ttl=120,
)
```

Result: Fewer trades, but higher win rate (target 75%+)

### Example 2: Aggressive Scalping (More Opportunities)

```python
IE_CONFIG = IEConfig(
    # Looser thresholds
    strong_imbalance_threshold=0.3,      # Lower bar
    extreme_funding_threshold_pct=7.0,   # Catch earlier
    extreme_z_score=1.5,                 # Less stretched required

    # Looser grading
    a_plus_threshold=60,  # 60+ for A+
    a_threshold=40,       # 40+ for A
    b_threshold=25,       # 25+ for B

    # Shorter caches (more responsive)
    order_book_cache_ttl=1,
    trade_flow_cache_ttl=30,
)
```

Result: More trades, but lower win rate (target 55-60%)

### Example 3: Order Book Focus (Tape Reading)

```python
IE_CONFIG = IEConfig(
    # Emphasize order book and trade flow
    order_book_weight=35,
    trade_flow_weight=35,
    funding_weight=10,
    oi_weight=10,
    vwap_weight=10,

    # Real-time data priority
    order_book_cache_ttl=1,
    trade_flow_cache_ttl=30,
    funding_cache_ttl=600,  # Don't care about funding updates
)
```

Result: Tape-reading style, focused on immediate order book dynamics

### Example 4: Macro Positioning (Swing Trading)

```python
IE_CONFIG = IEConfig(
    # Emphasize positioning metrics
    order_book_weight=10,
    trade_flow_weight=10,
    funding_weight=35,
    oi_weight=35,
    vwap_weight=10,

    # Longer caches (macro doesn't change fast)
    order_book_cache_ttl=10,
    trade_flow_cache_ttl=300,
    funding_cache_ttl=600,
    oi_cache_ttl=600,
)

AGENT_CONFIG = AgentConfig(
    # Deeper analysis for swings
    max_iterations=7,
    model_temperature=0.3,
    max_tokens=3072,
)
```

Result: Fewer trades, longer holding periods, focused on institutional positioning

---

## Applying Configuration Changes

### Method 1: Edit `config/settings.py`

```python
# Edit directly
IE_CONFIG = IEConfig(
    a_plus_threshold=80,  # Changed from 70
)
```

**Changes take effect immediately** (no restart needed)

### Method 2: Override at Runtime (Advanced)

```python
# In custom script
from config.settings import IE_CONFIG

# Temporarily override
original_threshold = IE_CONFIG.a_plus_threshold
IE_CONFIG.a_plus_threshold = 80

# Run analysis
result = fetch_institutional_metrics("BTC")

# Restore
IE_CONFIG.a_plus_threshold = original_threshold
```

---

## Configuration Validation

### Check Current Settings

```python
from config.settings import AGENT_CONFIG, IE_CONFIG

print(f"Agent Temperature: {AGENT_CONFIG.model_temperature}")
print(f"A+ Threshold: {IE_CONFIG.a_plus_threshold}")
print(f"OB Weight: {IE_CONFIG.order_book_weight}")
```

### Verify Constraints

```python
from config.settings import get_interval_constraint

for interval in ["1m", "5m", "15m", "1h"]:
    c = get_interval_constraint(interval)
    print(f"{interval}: max {c.max_lookback_hours}h, {c.max_candles} candles")
```

---

## Best Practices

1. **Start with defaults** - Don't change settings until you understand their impact
2. **Change one thing at a time** - Isolate effects
3. **Document changes** - Add comments explaining why you changed values
4. **Backtest before live** - Validate new settings on historical data
5. **Monitor win rate** - If it drops below 55%, revert changes

---

## Summary

Configuration is centralized in `config/settings.py` for easy tuning. Key areas:

- **Interval constraints**: Data availability limits
- **Agent config**: Model behavior and tool usage
- **IE config**: Metric thresholds, caching, convergence scoring
- **Tool config**: API settings

All changes take effect immediately. Start conservative, tune based on results.

See [strategy.md](strategy.md) for how configuration impacts trading performance.
