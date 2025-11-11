# Hyperliquid Strategy Monitor

Automated trading signal system that tells you when to trade by analyzing real-time market data.

## How It Works (ELI18)

Think of this as a "bullshit detector" for crypto markets. It watches 5 different signals to figure out if a price move is real or fake:

1. **Order Book** - Shows where big money is waiting. If there's way more buy orders than sell orders, that's bullish pressure.

2. **Funding Rate** - The "crowd sentiment tax". When everyone's long, they pay a high funding rate. High funding = everyone's greedy = time to fade them (contrarian signal).

3. **VWAP** - The average price institutions paid. If price is too far above/below this, it's "stretched" and likely to snap back (mean reversion).

4. **Trade Flow** - Detects who's being aggressive. Rising price on high volume = institutions buying hard. Falling price on high volume = institutions dumping.

5. **Open Interest** - Shows if new positions are opening or closing. Price up + OI up = real trend (new buyers). Price up + OI down = fake rally (shorts just covering, fade it).

**The System:**
- Calculates all 5 metrics every few seconds
- Gives each one a score based on how extreme it is
- Adds them up (max 100 points)
- If score ≥70 AND 3+ signals point the same direction → TRADE
- Otherwise → SKIP

**Output:** "SHORT BTC at $67,850. Stop: $69,207. Target: $66,825. Confidence: HIGH"

No guessing, no emotions. Just math.

## Project Structure

```
strategy_monitor/
├── config.py           # Thresholds and settings
├── api_client.py       # Fetches data from Hyperliquid (async/parallel)
├── storage.py          # Saves Open Interest history (SQLite)
├── metrics.py          # Calculates the 5 metrics
├── signal_generator.py # Generates LONG/SHORT/SKIP signals
├── app.py              # Streamlit UI
├── run.sh              # Launch script (Linux/Mac)
├── run.ps1             # Launch script (Windows)
└── oi_history.db       # Database (auto-created)
```

## Setup

```bash
cd strategy_monitor
pip install -r requirements.txt
```

## Running the UI

**Quick Start:**

Linux/Mac:
```bash
./run.sh
```

Windows (PowerShell):
```powershell
.\run.ps1
```

**Or manually:**
```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501` and auto-refresh every 2 seconds.

## Testing

Test individual components:

```bash
python api_client.py        # Test API (needs internet)
python storage.py           # Test database
python metrics.py           # Test calculations
python signal_generator.py  # Test signal generation
```

## Development Status

- ✅ **Phase 0**: Foundation (API client, storage)
- ✅ **Phase 1**: Metrics engine (all 6 calculations)
- ✅ **Phase 2**: Signal generator (convergence scoring)
- ✅ **Phase 3**: Basic UI (Streamlit dashboard)
- ⏳ **Phase 4**: Multi-asset + charts
- ⏳ **Phase 5**: Polish + optimization
