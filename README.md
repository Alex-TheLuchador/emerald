# Strategy Monitor

**Real-time trading signal system for Hyperliquid perpetuals.**

Analyzes order book pressure, funding rates, VWAP deviation, trade flow, and open interest to generate high-probability LONG/SHORT signals with precise entry/exit levels.

## Quick Start

```bash
cd strategy_monitor
pip install -r requirements.txt
streamlit run app_phase2.py  # Production dashboard (recommended)
```

**Note:** Two dashboard versions available:
- `app_phase2.py` - **Recommended** - Multi-coin, advanced signals, whale tracking
- `app.py` - Legacy single-coin version (deprecated)

Dashboard opens at `http://localhost:8501` with auto-refresh every 2 seconds.

## How It Works

The system scores 5 market metrics (0-100 points total):

1. **Order Book Pressure** - Detects institutional bid/ask imbalance
2. **Funding Rate** - Contrarian indicator when crowd is overleveraged
3. **VWAP Deviation** - Mean reversion signal when price is stretched
4. **Trade Flow** - Identifies aggressive buying/selling by institutions
5. **Open Interest** - Validates trend strength (new positions vs. liquidations)

**Signal Logic:**
- Score ≥70 + 3+ aligned metrics = HIGH confidence trade
- Score 50-69 + 3+ aligned metrics = MEDIUM confidence trade
- Otherwise = SKIP (no edge)

**Output Format:**
```
SHORT BTC at $67,850
Stop: $69,207 (2% risk)
Target: $66,825 (1.5% profit)
Confidence: HIGH
```

## Project Structure

```
strategy_monitor/
├── app.py              # Streamlit UI (single-coin mode)
├── app_phase2.py       # Multi-coin dashboard with whale tracking
├── api_client.py       # Hyperliquid API client (async/parallel)
├── storage.py          # SQLite storage for OI history
├── metrics.py          # Core metric calculations
├── signal_generator.py # Signal logic and scoring
├── config.py           # Thresholds and settings
├── whale_loader.py     # Whale wallet tracker
└── metrics/            # Modular metric calculators
    ├── positioning.py  # Institutional positioning analysis
    └── liquidity.py    # Liquidity zone detection
```

## Configuration

Edit `strategy_monitor/config.py` to customize:

- **COINS**: Asset watchlist (default: BTC, ETH, SOL)
- **REFRESH_INTERVAL_SECONDS**: Dashboard update frequency
- **OI_LOOKBACK_HOURS**: Open interest history window
- **Metric thresholds**: Min/max values for signal triggers

## Testing

Run individual modules to verify functionality:

```bash
cd strategy_monitor
python api_client.py        # Test Hyperliquid API connection
python storage.py           # Test database operations
python metrics.py           # Test metric calculations
python signal_generator.py  # Test signal generation
```

## Requirements

- Python 3.8+
- Internet connection (Hyperliquid API)
- Dependencies: `aiohttp`, `numpy`, `pandas`, `streamlit`, `plotly`

## Architecture Notes

- **Async API calls**: Parallel data fetching for low latency
- **Local storage**: SQLite for OI history (no external DB required)
- **Stateless design**: No session persistence (restarts are cheap)
- **Modular metrics**: Easy to add/remove signals

## Disclaimer

This is an **analysis tool**, not an automated trading bot. All trading decisions are manual and at your own risk.
