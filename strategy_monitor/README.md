# Hyperliquid Strategy Monitor

Real-time trading signal generator based on institutional order flow, funding rates, and market structure.

## Project Structure

```
strategy_monitor/
├── config.py           # Configuration and thresholds
├── api_client.py       # Hyperliquid API client (async)
├── storage.py          # SQLite storage for OI history
├── metrics.py          # Metric calculations (Phase 1)
├── signal_generator.py # Signal generation logic (Phase 2)
├── app.py             # Streamlit UI (Phase 3+)
└── oi_history.db      # SQLite database (auto-generated)
```

## Setup

```bash
cd strategy_monitor
pip install -r requirements.txt
```

## Development Phases

- ✅ **Phase 0**: Foundation (API client, storage)
- ⏳ **Phase 1**: Metrics engine
- ⏳ **Phase 2**: Signal generator
- ⏳ **Phase 3**: Basic UI
- ⏳ **Phase 4**: Multi-asset + charts
- ⏳ **Phase 5**: Polish + optimization

## Testing

Test individual components:

```bash
python api_client.py    # Test API connectivity
python storage.py       # Test OI storage
python metrics.py       # Test metric calculations (Phase 1)
```

## Strategy Overview

Based on 5 core metrics:
1. **Order Book Imbalance** - Where is liquidity?
2. **Funding Rate** - Sentiment extreme?
3. **VWAP Deviation** - Price stretched?
4. **Trade Flow** - Who's the aggressor?
5. **Open Interest Divergence** - Real trend or fake?

Plus basis spread for validation.

Generates signals when convergence score ≥70 and 3+ metrics align.
