# Getting Started with EMERALD

## Overview

EMERALD (**E**ffective **M**arket **E**valuation and **R**igorous **A**nalysis for **L**ogical **D**ecisions) is an institutional-grade AI trading assistant for Hyperliquid perpetuals markets.

The system combines:
- **Quantitative analysis** - 5 institutional metrics (order book, funding, trade flow, basis, OI)
- **Multi-signal convergence** - Only trade when 3+ metrics align (70+ score)
- **Advanced liquidity intelligence** - Spoofing detection, liquidation tracking, cross-exchange arb
- **Conversation memory** - Persistent sessions for contextual discussions
- **LangChain-powered AI** - Claude Sonnet 4.5 for intelligent analysis

---

## Prerequisites

- **Python 3.9+**
- **Anthropic API key** (Claude AI access)
- **Git** (for cloning repository)

---

## Installation

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd emerald
```

### 2. Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies**:
- `langchain` - Agent framework
- `anthropic` - Claude AI models
- `requests` - HTTP client for Hyperliquid API
- `python-dotenv` - Environment variable management

### 4. Configure API Key

Create `.env` file in project root:

```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

Get your API key from: https://console.anthropic.com/

### 5. Verify Directory Structure

```bash
# Create required directories
mkdir -p agent_outputs conversations

# Verify structure
ls -la

# Should see:
# - agent/
# - config/
# - tools/
# - ie/
# - memory/
# - agent_context/
# - Documentation/
# - .env
```

---

## Quick Start

### Basic Usage

```bash
# Simple query (auto-continues today's session)
python agent/agent.py "What's BTC doing on 1h?"

# Multi-timeframe analysis
python agent/agent.py "Analyze ETH across Daily, 4H, and 1H"

# Get trade setup with grading
python agent/agent.py "Should I long or short BTC right now?"
```

### With Session Management

```bash
# List all sessions
python agent/agent.py --list-sessions

# Use specific session
python agent/agent.py -s "morning_trades" "Analyze BTC"

# Start fresh session
python agent/agent.py --new "Fresh analysis"

# View session history
python agent/agent.py --show-session "2025-11-08_session"
```

### Advanced Options

```bash
# Custom memory depth (default: 20 messages)
python agent/agent.py --max-history 30 "Complex multi-coin analysis"

# Delete old session
python agent/agent.py --delete-session "old_session_name"
```

---

## Example Workflows

### Workflow 1: Morning Market Check

```bash
# Check overall market bias
python agent/agent.py "What's the overall market sentiment?"

# Analyze top coins
python agent/agent.py "Compare BTC, ETH, and SOL setups on 1h"

# Get specific entry
python agent/agent.py "Which has the cleanest setup right now?"
```

EMERALD remembers the entire conversation, so each query builds on previous context.

### Workflow 2: Trade Setup Validation

```bash
# Start dedicated session
python agent/agent.py -s "btc_scalp" "Analyze BTC 15m for scalp setups"

# Check convergence score
python agent/agent.py -s "btc_scalp" "What's the convergence score?"

# Validate with Phase 2 tools
python agent/agent.py -s "btc_scalp" "Check for spoofing and liquidation cascades"

# Get final decision
python agent/agent.py -s "btc_scalp" "Should I take this trade?"
```

### Workflow 3: Post-Trade Review

```bash
# Document your trade
python agent/agent.py "I longed BTC at $67,800, stopped at $67,500. What went wrong?"

# Get coaching
python agent/agent.py "I keep closing trades early. Any advice?"

# Review strategy
python agent/agent.py "Show me my last 3 trades and find patterns"
```

---

## Understanding Output

### Typical Response Format

```markdown
### BTC 1H Setup - Grade: A+ (Convergence: 85/100)

**ICT Analysis**:
- HTF Bias: Bearish
- Location: Premium (above 50%)
- Setup: Liquidity sweep + FVG

**IE Validation** (85/100):
✓ Order Book: -0.6 (strong ask pressure) → +25 pts
✓ Funding: +12% annualized (extreme) → +20 pts
✓ OI Divergence: Strong bearish → +30 pts
✓ VWAP: +2.1σ above mean → +25 pts
✗ Volume: 0.9x average → -15 pts

**Phase 2 Confluence**:
- Spoofing detected: 2 fake bid walls
- Iceberg sell order at $68,000 (6 refills)
- HL trading 0.12% premium to Binance (arb selling pressure)

**Recommendation**: HIGH CONVICTION SHORT

Entry: $67,800-67,900 (FVG zone)
Stop: $68,200 (above swept high)
TP1: $67,200 (50% off at 1.5R)
TP2: $66,500 (25% off at 3.0R)
Trail: Remaining 25% with 2.0R buffer

Position Size: 1.5% account risk (A+ grade = full size)
Expected R: 2.5R average
```

### Grade Interpretation

- **A+ (70-100)**: High conviction - Full position size, all metrics aligned
- **A (50-69)**: Good setup - 75% position size, most metrics confirm
- **B (30-49)**: Acceptable - 50% position size, some confirmation
- **C (<30)**: Low confidence - Skip entirely

---

## Configuration

### Basic Settings

Edit `config/settings.py` to customize:

```python
# Agent behavior
AGENT_CONFIG = AgentConfig(
    max_tool_calls_per_response=3,  # Tools per query
    model_temperature=0.25,          # Creativity (0.0-1.0)
    max_tokens=2048,                 # Response length
)

# Interval constraints
INTERVAL_CONSTRAINTS = {
    "1m": IntervalConstraints(max_lookback_hours=1.5),
    "15m": IntervalConstraints(max_lookback_hours=24),
    "1h": IntervalConstraints(max_lookback_hours=72),
    # ...
}

# IE thresholds
IE_CONFIG = IEConfig(
    strong_imbalance_threshold=0.4,         # Order book
    extreme_funding_threshold_pct=10.0,     # Funding rate
    a_plus_threshold=70,                    # Grading
)
```

Changes take effect immediately (no restart needed).

### Memory Settings

```bash
# Default: Last 20 messages included in context
python agent/agent.py "Your query"

# Increase for complex analysis
python agent/agent.py --max-history 40 "Multi-coin comparison"

# Decrease for quick questions
python agent/agent.py --max-history 5 "Current BTC price?"
```

---

## File Structure

```
emerald/
├── agent/
│   └── agent.py                 # Main entry point
├── config/
│   └── settings.py              # All configuration
├── tools/
│   ├── ie_fetch_*.py            # Institutional metrics
│   ├── ie_order_book_microstructure.py  # Phase 2
│   └── ie_liquidation_tracker.py        # Phase 2
├── ie/
│   ├── calculations.py          # Metric calculations
│   ├── data_models.py           # Data structures
│   └── cache.py                 # Caching system
├── memory/
│   └── session_manager.py       # Conversation persistence
├── agent_context/
│   ├── Mentality and Personality.md
│   ├── Quantitative_Metrics_Guide.md
│   └── November 2025.md         # Trading journal
├── Documentation/
│   ├── strategy.md              # Trading strategy (READ THIS)
│   └── *.md                     # Other docs
├── conversations/               # Session storage (gitignored)
├── agent_outputs/               # Generated data (gitignored)
└── .env                         # API keys (gitignored)
```

---

## Next Steps

1. **Read [Trading Strategy](strategy.md)** - Understand how we make money
2. **Explore [Phase 1 Features](phase1-quantitative-engine.md)** - Core metrics
3. **Learn [Phase 2 Tools](phase2-advanced-liquidity.md)** - Advanced detection
4. **Study [Architecture](architecture.md)** - How everything works together
5. **Test with live data** - Start small, validate approach

---

## Common First-Time Issues

### Issue: "ANTHROPIC_API_KEY not found"

**Solution**: Create `.env` file with your API key:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
```

### Issue: "ModuleNotFoundError: No module named 'langchain'"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Agent responds without fetching data

**Solution**: Be explicit in your query:
```bash
# Vague (may not trigger tools)
python agent/agent.py "Tell me about BTC"

# Explicit (will trigger tools)
python agent/agent.py "Fetch and analyze BTC 1h data"
```

### Issue: "Configuration error: 1m limited to 1.5 hours"

**Solution**: This is expected. Request less data:
```bash
# Instead of:
python agent/agent.py "Show me 5 hours of 1m data"

# Use:
python agent/agent.py "Show me 1 hour of 1m data"
```

---

## Getting Help

- **Documentation**: Browse `Documentation/` directory
- **Examples**: Check `Usage Examples` section in docs
- **Troubleshooting**: See [troubleshooting.md](troubleshooting.md)
- **Issues**: Report bugs on GitHub issues page

---

**Ready to trade like an institution? Let's go.**
