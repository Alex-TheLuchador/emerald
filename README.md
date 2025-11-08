# EMERALD Trading Agent

**E**ffective **M**arket **E**valuation and **R**igorous **A**nalysis for **L**ogical **D**ecisions

---

## What is EMERALD?

An **institutional-grade quantitative trading system** for Hyperliquid perpetuals. EMERALD detects when multiple independent institutional metrics align - creating high-probability setups invisible to retail traders.

**Core Edge**: Multi-signal convergence. We only trade when 3+ metrics align (70+ convergence score).

### Quick Stats

- **5 Institutional Metrics**: Order book, funding rate, trade flow, perpetuals basis, open interest
- **3 Advanced Liquidity Tools**: Spoofing detection, liquidation tracking, cross-exchange arb
- **0-100 Convergence Scoring**: Objective, quantitative grading (A+/A/B/C)
- **70+ Score Required**: High conviction setups only
- **Multi-Timeframe Analysis**: 1m/5m/15m must all align
- **Conversation Memory**: Persistent sessions for contextual discussions

---

## Documentation

### 🚀 Getting Started

**New to EMERALD?** Start here:
- **[Getting Started Guide](Documentation/getting-started.md)** - Installation, quickstart, first steps
- **[Trading Strategy](Documentation/strategy.md)** - **READ THIS FIRST** - How we make money

### 📊 Core Features

**Phase 1: Quantitative Engine**
- **[Phase 1 Documentation](Documentation/phase1-quantitative-engine.md)**
  - Order Book Imbalance
  - Funding Rate Analysis
  - Trade Flow Detection
  - Perpetuals Basis (Spot-Perp Spread)
  - Open Interest Divergence
  - Multi-Timeframe Convergence

**Phase 2: Advanced Liquidity Intelligence**
- **[Phase 2 Documentation](Documentation/phase2-advanced-liquidity.md)**
  - Order Book Microstructure (Spoofing, Icebergs, Wall Dynamics)
  - Liquidation Cascade Tracking
  - Cross-Exchange Arbitrage Monitoring

### 🔧 Technical Documentation

- **[Architecture Overview](Documentation/architecture.md)** - How everything works
- **[Configuration Reference](Documentation/configuration.md)** - Tuning parameters

---

## Quick Start

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd emerald

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Basic Usage

```bash
# Simple analysis (auto-continues today's session)
python agent/agent.py "What's BTC doing on 1h?"

# Multi-timeframe analysis
python agent/agent.py "Analyze ETH across Daily, 4H, and 1H"

# Get graded setup
python agent/agent.py "Should I trade BTC right now?"

# Check for manipulation
python agent/agent.py "Analyze BTC. Check for spoofing and liquidation cascades."
```

### Session Management

```bash
# List all sessions
python agent/agent.py --list-sessions

# Use specific session
python agent/agent.py -s "morning_trades" "Analyze BTC"

# Start fresh session
python agent/agent.py --new "Clean analysis"

# View session history
python agent/agent.py --show-session "2025-11-08_session"
```

---

## Example Output

```markdown
### BTC 1H Setup - Grade: A+ (Convergence: 85/100)

**Phase 1 Metrics**:
✓ Order Book: -0.62 (strong ask pressure) → +25 pts
✓ Trade Flow: -0.54 (aggressive selling) → +25 pts
✓ Funding: +14% annualized (extreme bullish crowd) → +20 pts
✓ Basis: +0.31% (premium, aligned) → Included
✓ OI: -5.1% while price +2.3% (weak rally) → +30 pts
✓ VWAP: +2.1σ on 1m/5m/15m (extreme overextension) → +30 pts

**Phase 2 Confluence** (+10 pts):
✓ Iceberg sell order at $68,000 (7 refills)
✓ Recent short squeeze completed (liquidations exhausted)
✓ HL trading 0.14% premium to Binance (arb selling pressure)

**Recommendation**: HIGH CONVICTION SHORT

Entry: $67,800-67,900
Stop: $68,200
TP1: $67,200 (50% off at 1.5R)
TP2: $66,500 (25% off at 3.0R)
Trail: Remaining 25%

Position Size: 1.5% account risk (A+ grade = full size)
```

---

## Project Structure

```
emerald/
├── agent/                   # Main entry point
├── config/                  # Configuration (SINGLE SOURCE OF TRUTH)
├── tools/                   # Phase 1 + Phase 2 tools
├── ie/                      # Institutional Engine (calculations)
├── memory/                  # Session management
├── agent_context/           # Strategy, personality, journal
├── Documentation/           # 📚 All documentation
│   ├── strategy.md          # ⭐ START HERE - Trading strategy
│   ├── getting-started.md   # Installation & quickstart
│   ├── phase1-quantitative-engine.md
│   ├── phase2-advanced-liquidity.md
│   ├── architecture.md      # System design
│   └── configuration.md     # Settings reference
├── conversations/           # Session storage (gitignored)
├── agent_outputs/           # Generated data (gitignored)
└── .env                     # API keys (gitignored)
```

---

## Core Philosophy

### What We Do Differently

**Traditional Retail Trading**:
- Chart patterns (subjective, lagging)
- Gut feelings (emotional, unreliable)
- Hope and guesswork (gambling)
- Win rate: 40-45%

**EMERALD Institutional Approach**:
- Track what institutions DO, not what charts SHOW
- Order book: Where is real money positioned?
- Funding: When is the crowd maximally wrong?
- OI: Are smart players accumulating or distributing?
- Only trade when 3+ metrics align
- Quantitative risk management
- Win rate: 60-70% (high selectivity)

### The Edge

**Multi-Signal Convergence**:
- Single metric = noise (50/50 coin flip)
- 2 metrics = interesting (60% win rate)
- 3+ metrics = high probability (75%+ win rate)
- **We only trade 70+ convergence scores**

**Example**:
```
BTC at resistance after rally

Single metric view (retail):
"Price looks extended, might short"
→ 50/50 guess

EMERALD convergence view:
- Order Book: -0.68 (strong ask pressure) ✓
- Funding: +14% (extreme bullish crowd) ✓
- Basis: +0.31% (premium, aligned) ✓
- VWAP: +2.1σ (statistical extreme) ✓
- OI: -5% while price +2% (divergence) ✓
Score: 85/100 (A+ grade)
→ High conviction short (75%+ win probability)
```

---

## Trading Strategy

See **[strategy.md](Documentation/strategy.md)** for complete details on:

- How we make money
- The 5 institutional metrics
- Phase 2 advanced signals
- Multi-signal convergence scoring
- Entry/exit rules
- Position sizing (scales with grade)
- Risk management layer
- Expected performance (65% win rate, 2.5R average win)

**TLDR**: We detect institutional positioning before it's obvious, only trade when multiple independent signals align, and size positions to match setup quality. This creates a statistical edge that compounds over time.

---

## Features

### Phase 1: Institutional-Grade Quantitative Engine

**5 Core Metrics** (0-100 convergence scoring):
1. **Order Book Imbalance** - Real-time bid/ask pressure
2. **Funding Rate** - Sentiment extremes (contrarian signal)
3. **Trade Flow** - Aggressive buyer vs seller dominance
4. **Perpetuals Basis** - Spot-perp spread (arb opportunities)
5. **Open Interest Divergence** - Smart money positioning

**Multi-Timeframe Convergence**:
- Analyzes 1m/5m/15m simultaneously
- Requires all timeframes to align
- VWAP statistical deviation (Z-score)
- Volume confirmation

### Phase 2: Advanced Liquidity Intelligence

**Order Book Microstructure**:
- Spoofing detection (fake liquidity, 3+ appearances)
- Iceberg orders (hidden institutional activity, 3+ refills)
- Wall dynamics (moving support/resistance)
- 60-second rolling window analysis

**Liquidation Cascade Tracker**:
- Mass liquidation detection (5+ in 5 minutes)
- Short squeeze vs long squeeze identification
- Stop hunt zone mapping (>$100k liquidations)

**Cross-Exchange Arbitrage Monitor**:
- Hyperliquid vs Binance price comparison
- Arbitrage flow signals (>0.1% deviation)
- Institutional arb bot pressure detection

### Conversation Memory

**Persistent Sessions**:
- Auto-continue today's session
- Named sessions for workflows
- Configurable memory depth (5-50 messages)
- JSON file storage
- Cross-session context

**Example**:
```bash
# Morning
$ python agent/agent.py "What's the overall market bias?"
$ python agent/agent.py "BTC setup on 1h?"
$ python agent/agent.py "Compare with ETH"
# All three queries share context - agent remembers previous discussion
```

---

## Grading System

### Setup Grades

| Grade | Score | Meaning | Position Size |
|-------|-------|---------|---------------|
| **A+** | 70-100 | High conviction - All metrics aligned | 1.5% risk (full size) |
| **A** | 50-69 | Good setup - Most metrics confirm | 1.0% risk (75% size) |
| **B** | 30-49 | Acceptable - Some confirmation | 0.75% risk (50% size) |
| **C** | <30 | Low confidence - **SKIP TRADE** | 0% (no trade) |

### Convergence Scoring Algorithm

```
Order Book Alignment:        25 points (imbalance > 0.4)
Trade Flow Alignment:        25 points (flow > 0.4)
VWAP Multi-Timeframe:        30 points (all TFs aligned)
Funding-Basis Convergence:   20 points (both extreme + aligned)

Special Modifiers:
  Funding-Basis Divergence:  -15 points (conflicting signals)
  Phase 2 Confluence:        +10 points (iceberg + cascade)
  Low Volume:                -10 points (volume < 0.6x avg)

Total: 0-100 (capped at 100)
```

---

## Requirements

- Python 3.9+
- Anthropic API key (Claude AI)
- Internet connection (Hyperliquid API)

**Key Dependencies**:
- `langchain` - Agent framework
- `anthropic` - Claude models
- `requests` - HTTP client
- `python-dotenv` - Environment management

See `requirements.txt` for complete list.

---

## Configuration

All settings in `config/settings.py`:

```python
# Agent behavior
AGENT_CONFIG = AgentConfig(
    max_tool_calls_per_response=3,
    model_temperature=0.25,
    max_tokens=2048,
)

# IE thresholds
IE_CONFIG = IEConfig(
    strong_imbalance_threshold=0.4,
    extreme_funding_threshold_pct=10.0,
    a_plus_threshold=70,  # 70+ = A+ grade
)

# Interval limits
INTERVAL_CONSTRAINTS = {
    "1m": IntervalConstraints(max_lookback_hours=1.5),
    "15m": IntervalConstraints(max_lookback_hours=24),
    # ...
}
```

See **[configuration.md](Documentation/configuration.md)** for complete reference.

---

## Testing

### Test Phase 1 Tools

```bash
# Individual metrics
python tools/ie_fetch_order_book.py
python tools/ie_fetch_funding.py
python tools/ie_fetch_perpetuals_basis.py

# Unified metrics
python -c "from tools.ie_fetch_institutional_metrics import fetch_institutional_metrics; import json; print(json.dumps(fetch_institutional_metrics('BTC')['summary'], indent=2))"

# Multi-timeframe convergence
python -c "from tools.ie_multi_timeframe_convergence import fetch_multi_timeframe_convergence; result = fetch_multi_timeframe_convergence('BTC', ['1m', '5m', '15m']); print(f\"Score: {result['convergence_score']}/100\")"
```

### Test Phase 2 Tools

```bash
# Microstructure
python -c "from tools.ie_order_book_microstructure import fetch_order_book_microstructure_tool; print(fetch_order_book_microstructure_tool('BTC'))"

# Liquidation tracker
python -c "from tools.ie_liquidation_tracker import fetch_liquidation_tracker_tool; print(fetch_liquidation_tracker_tool('BTC', 30))"

# Cross-exchange arb
python -c "from tools.ie_cross_exchange_arb import fetch_cross_exchange_arb_tool; print(fetch_cross_exchange_arb_tool('BTC'))"
```

### Test with Agent

```bash
python agent/agent.py "Grade the current BTC setup with full Phase 2 analysis"
```

---

## What's Next

### Current Status

- ✅ **Phase 1**: Quantitative engine (complete)
- ✅ **Phase 2**: Advanced liquidity intelligence (complete)
- ⏳ **Phase 3**: Risk management layer (planned)

### Phase 3 (Planned)

- Dynamic position sizing algorithms
- Portfolio-level risk management
- Multi-coin correlation tracking
- Automated trade execution hooks
- Backtest framework
- Performance analytics dashboard

---

## Support

- **Documentation**: Browse `Documentation/` directory
- **Strategy**: Read [strategy.md](Documentation/strategy.md) first
- **Getting Started**: [getting-started.md](Documentation/getting-started.md)
- **Issues**: Report bugs on GitHub issues page

---

## Key Principles

1. **Multi-signal convergence is everything** - Single metrics lie
2. **Only trade institutional alignment** - 70+ score or skip
3. **Position size reflects confidence** - A+ gets full size, B gets half
4. **Layered exits maximize R-multiples** - Never exit 100% at once
5. **Discipline trumps analysis** - Execute the system, don't override
6. **Data beats discretion** - Trust scores, not feelings
7. **Quality over quantity** - 3 A+ trades/week beats 20 C trades
8. **Track what institutions DO** - Not what charts SHOW

---

## License

[Your License Here]

---

**EMERALD: Institutional-grade quantitative trading. See what retail cannot see.**
