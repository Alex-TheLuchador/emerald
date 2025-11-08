# EMERALD Trading Agent

**E**ffective **M**arket **E**valuation and **R**igorous **A**nalysis for **L**ogical **D**ecisions

A LangChain-powered AI trading assistant for analyzing Hyperliquid perpetuals markets using ICT (Inner Circle Trader) concepts like market structure, liquidity pools, Fair Value Gaps (FVGs), and swing analysis.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [How It Works](#how-it-works)
4. [Configuration System](#configuration-system)
5. [The Data Pipeline](#the-data-pipeline)
6. [Context Management](#context-management)
7. [The Agent](#the-agent)
8. [Conversation Memory](#conversation-memory)
9. [Usage Examples](#usage-examples)
10. [Setup & Installation](#setup--installation)

---

## Overview

EMERALD is a trading assistant that:
- Fetches real-time market data from Hyperliquid's API
- Analyzes price action using swing structure, FVGs, and liquidity concepts
- Provides trade ideas based on a documented strategy
- Maintains a personality that balances analytical coldness with coaching warmth
- **Remembers conversations** - Persistent memory across sessions for contextual discussions

The system is built on four core pillars:

1. **Configuration** - Centralized settings for intervals, limits, and agent behavior
2. **Tools** - Data fetching and technical analysis utilities
3. **Context** - Trading strategy, mentality, and journal documents that guide the agent
4. **Memory** - Session-based conversation persistence for multi-turn discussions

---

## Project Structure

```
EMERALD/
├── agent/
│   └── agent.py                # Main agent entry point
├── config/
│   ├── __init__.py
│   └── settings.py             # All configuration (intervals, limits, etc.)
├── tools/
│   ├── tool_fetch_hl_raw.py    # LangChain tool for fetching Hyperliquid data
│   └── context_manager.py      # Context document loading system
├── memory/
│   ├── __init__.py
│   └── session_manager.py      # Conversation persistence and session management
├── agent_context/
│   ├── Mentality and Personality.md
│   ├── Strategy.md
│   └── November 2025.md        # Trading journal
├── agent_outputs/              # Generated data files
├── conversations/              # Conversation session storage (gitignored)
├── requirements.txt            # Python dependencies
└── MEMORY_GUIDE.md            # Complete memory system documentation
```

---

## How It Works

### The Big Picture

```
User Query
    ↓
Agent (agent.py)
    ↓
System Prompt = Core Directive + Context Documents + Config Limits
    ↓
LLM decides: Need data? → Call fetch_hl_raw tool
    ↓
Tool fetches from Hyperliquid API → Parses → Annotates (swings, FVGs)
    ↓
Agent analyzes data using strategy context
    ↓
Response with trade ideas, analysis, or coaching
```

### Key Flow Example

```python
# 1. User asks: "What's the setup on BTC 15m?"

# 2. Agent sees system prompt with:
#    - Trading strategy (HTF alignment, discount/premium, liquidity)
#    - Interval constraints (15m limited to 24 hours lookback)
#    - Personality (analytical + tough love coaching)

# 3. Agent decides to fetch data and calls:
fetch_hl_raw(
    coin="BTC",
    interval="15m",
    hours=12,
    limit=100,
    convert=True,
    significant_swings=True,
    fvg=True
)

# 4. Tool returns annotated candles with:
#    - OHLC data
#    - Significant swing highs/lows marked
#    - Fair Value Gaps identified
#    - Human-readable timestamps

# 5. Agent analyzes using strategy:
#    - Checks HTF bias (Daily, 4H, 1H)
#    - Identifies dealing range on 1H
#    - Looks for discount/premium positioning
#    - Finds liquidity pools and displacement

# 6. Agent responds with trade setup or coaching
```

---

## Configuration System

**File**: `config/settings.py`

All configurable parameters live here. This makes adjustments easy without touching core logic.

### Interval Constraints

Each interval has limits to prevent excessive API calls and respect data availability:

```python
INTERVAL_CONSTRAINTS = {
    "1m": IntervalConstraints(
        max_lookback_hours=1.5,    # 1m data only goes back 1.5 hours
        interval_minutes=1,
        max_candles=250,
    ),
    "15m": IntervalConstraints(
        max_lookback_hours=24,     # 15m data goes back 24 hours
        interval_minutes=15,
        max_candles=250,
    ),
    # ... more intervals
}
```

**Why this matters**: If a user asks for "5 hours of 1m data," the agent knows it's impossible (1m limit is 1.5 hours) and automatically adjusts:

```python
# Agent sees in system prompt:
"1m interval must look back no more than 1.5 hours."

# Agent responds:
"You requested 5 hours of 1m data, but 1m intervals are limited 
to 1.5 hours. I'll fetch the maximum allowed instead."
```

### Tool Configuration

```python
@dataclass
class ToolConfig:
    api_url: str = "https://api.hyperliquid.xyz/info"
    request_timeout: int = 15
    max_candles_absolute: int = 250
    default_output_subdir: str = "agent_outputs"
```

### Agent Configuration

```python
@dataclass
class AgentConfig:
    max_tool_calls_per_response: int = 3  # Prevent tool spam
    max_iterations: int = 5                # Max reasoning loops
    model_temperature: float = 0.25        # Low = more deterministic
    max_tokens: int = 2048
    model_timeout: int = 45
    max_retries: int = 2
```

**Usage in agent**:

```python
from config.settings import AGENT_CONFIG, generate_constraint_text

# Generate constraint text for system prompt
LOOKBACK_CONSTRAINTS = generate_constraint_text()
# Returns:
#   - 1m interval must look back no more than 1.5 hours.
#   - 5m interval must look back no more than 6 hours.
#   - 15m interval must look back no more than 24 hours.
#   ...

# Use in agent
agent = create_agent(
    model=model,
    tools=[fetch_hl_raw],
    system_prompt=f"{SYSTEM_PROMPT_CORE}\n\n{LOOKBACK_CONSTRAINTS}",
)
```

---

## The Data Pipeline

**File**: `tools/tool_fetch_hl_raw.py`

This is the workhorse that fetches and processes market data.

### Step 1: Fetch Raw Candles

```python
@tool
def fetch_hl_raw(
    coin: str,           # "BTC"
    interval: str,       # "15m"
    hours: int,          # 12
    limit: int,          # 100
    convert: bool,       # True = human-readable
    significant_swings: bool,  # True = mark swing highs/lows
    fvg: bool,          # True = detect Fair Value Gaps
) -> Tuple[int, Dict[str, Any]]:
```

**API Request**:

```python
payload = {
    "type": "candleSnapshot",
    "req": {
        "coin": "BTC",
        "interval": "15m",
        "startTime": now_ms - (12 * 3_600_000),  # 12 hours ago
        "endTime": now_ms,
        "numCandles": 100,
    }
}

response = requests.post(
    "https://api.hyperliquid.xyz/info",
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=15
)
```

### Step 2: Parse & Normalize

Raw API responses vary (dict, list, nested structures). The parser handles all formats:

```python
def parse_raw_keep_ohlc(raw_root):
    # Handles both formats:
    # Dict: {"candles": [{"t": 123, "o": "100", ...}]}
    # List: [[123, "100", "101", "99", "100.5", 1000], ...]
    
    # Normalizes to:
    [
        {"t": 1699200000000, "o": "67890.5", "h": "68000", 
         "l": "67500", "c": "67800", "v": "1234.56"},
        ...
    ]
```

### Step 3: Convert to Human-Readable (Optional)

```python
def convert_to_human(candles_raw):
    return [
        {
            "timestamp": "2025-11-06T14:30:00Z",  # ISO-8601
            "open": 67890.5,                       # float
            "high": 68000.0,
            "low": 67500.0,
            "close": 67800.0,
            "volume": 1234.56,
        },
        ...
    ]
```

### Step 4: Annotate with Technical Features (Optional)

#### Significant Swing Highs/Lows

**Definition**: A swing high where the middle candle's high is higher than both neighbors' highs (and vice versa for lows):

```
Swing High Pattern:
  Candle[i-1].high < Candle[i].high > Candle[i+1].high
  
  67500 < 68000 > 67800  ✓ Swing High at i
```

**Significant Swing**: A swing high/low that is also higher/lower than its neighboring swings:

```python
def compute_significant_swings_raw(swings, swing_type):
    # For each swing, compare to neighbor swings
    # Only keep if it's higher/lower than both
    
    # Example:
    # Swings: [67000, 68000, 67500]
    #               ↑
    #         Significant (higher than neighbors)
```

**In output**:

```json
{
  "t": 1699200000000,
  "ts": "2025-11-06T14:30:00Z",
  "o": "67890.5",
  "h": "68000",
  "l": "67500",
  "c": "67800",
  "significantSwingHigh": true  // ← Marked!
}
```

#### Fair Value Gaps (FVGs)

**Definition**: A gap in price action where price moved so fast it left an "inefficiency."

**Bullish FVG**:
```
Candle[i-1].high < Candle[i+1].low
(Gap between candle i-1 and i+1)

Example:
  i-1: high = 67500
  i:   (doesn't matter)
  i+1: low = 67800
  
  Gap = 67500 to 67800 (300 point FVG)
```

**Bearish FVG**:
```
Candle[i-1].low > Candle[i+1].high
(Previous low is above next high)
```

**In output**:

```json
{
  "t": 1699200000000,
  "ts": "2025-11-06T14:30:00Z",
  "o": "67890.5",
  "h": "68000",
  "l": "67500",
  "c": "67800",
  "fvg": {  // ← FVG detected!
    "type": "bullish",
    "top": "67800",
    "bottom": "67500",
    "size": "300"
  }
}
```

### Step 5: Save Output (Optional)

```python
# If out parameter provided:
output_path = BASE_DIR / "agent_outputs" / "BTC_15m.json"
output_path.write_text(json.dumps(final_payload, indent=2))

# Returns:
{
    "raw": {...},           # Original API response
    "converted": [...],     # Human-readable (if convert=True)
    "annotated": [...],     # With swings/FVGs (if requested)
    "final": [...],         # What was actually saved
    "saved_to": "agent_outputs/BTC_15m.json"
}
```

### Complete Example

```python
status, result = fetch_hl_raw(
    coin="BTC",
    interval="15m",
    hours=12,
    limit=100,
    out="agent_outputs/btc_15m.json",
    convert=True,
    significant_swings=True,
    fvg=True,
)

# Result structure:
{
    "raw": {...},  # Original API response
    "converted": [
        {
            "timestamp": "2025-11-06T14:30:00Z",
            "open": 67890.5,
            "high": 68000.0,
            "low": 67500.0,
            "close": 67800.0,
            "volume": 1234.56
        },
        ...
    ],
    "annotated": [
        {
            "t": 1699200000000,
            "ts": "2025-11-06T14:30:00Z",
            "o": "67890.5",
            "h": "68000",
            "l": "67500",
            "c": "67800",
            "significantSwingHigh": true,
            "fvg": {
                "type": "bullish",
                "top": "67800",
                "bottom": "67500",
                "size": "300"
            }
        },
        ...
    ],
    "final": [...],  # Same as annotated (prioritized over converted)
    "saved_to": "agent_outputs/btc_15m.json"
}
```

---

## Context Management

**Files**: 
- `tools/context_manager.py` (loader)
- `agent_context/*.md` (content)

Context documents define the agent's:
- **Personality**: Analytical, unbiased, tough love coaching
- **Strategy**: HTF alignment, discount/premium, liquidity pools, FVGs
- **Experience**: Trading journal with real trade reviews

### Markdown Metadata Tags

Documents use special comments to tag sections:

```markdown
<!-- meta: core -->
## Personality
As a crypto trader, you are extremely analytical...

<!-- meta: core, concept=market-structure -->
### Market Structure Fundamentals
**Swing High**: Highest high in the middle...

<!-- meta: concept=liquidity -->
### Draw on Liquidity
**Core Concept**: The market moves from liquidity pool to liquidity pool...

<!-- meta: tag=journal, date=2025-11-03, trade=1, coin=BTC -->
### Trade 1 Review
Trade 1 was a hefty loss. I was pennies away from my take-profit...
```

### Loading System (Future Feature)

The `ContextManager` class supports selective loading:

```python
from tools.context_manager import ContextManager

mgr = ContextManager(Path("agent_context"))

# Get all core concepts (always loaded)
core = mgr.get_core_context()

# Get specific timeframe concepts
entry_docs = mgr.get_sections(timeframe="15m", concept="entry")

# Get journal entries for specific coin
btc_trades = mgr.get_sections(tag="journal", coin="BTC")

# Search content
results = mgr.search_content("FVG", limit=5)
```

**Current Implementation**: `agent.py` loads all markdown files at startup:

```python
def load_markdown_context(context_dir: Path) -> str:
    """Aggregate markdown files for use as system context."""
    docs = []
    for path in sorted(context_dir.rglob("*.md")):
        relative_title = path.relative_to(context_dir).with_suffix("").as_posix()
        text = path.read_text(encoding="utf-8").strip()
        docs.append(f"### {relative_title}\n{text}")
    return "\n\n".join(docs)

CONTEXT_DOCUMENTS = load_markdown_context(BASE_DIR / "agent_context")
```

This gives the agent full access to strategy, personality, and journal entries in every response.

---

## The Agent

**File**: `agent.py`

The main orchestrator that connects everything.

### Initialization

```python
# 1. Load environment variables
dotenv.load_dotenv()
api_key = os.environ.get("ANTHROPIC_API_KEY")

# 2. Initialize LLM
model = init_chat_model(
    model="anthropic:claude-sonnet-4-5",
    max_tokens=AGENT_CONFIG.max_tokens,
    temperature=AGENT_CONFIG.model_temperature,
    timeout=AGENT_CONFIG.model_timeout,
    max_retries=AGENT_CONFIG.max_retries,
)

# 3. Load context documents
CONTEXT_DOCUMENTS = load_markdown_context(BASE_DIR / "agent_context")

# 4. Generate constraint text from config
LOOKBACK_CONSTRAINTS = generate_constraint_text()
# Returns formatted string of all interval limits
```

### System Prompt Construction

```python
SYSTEM_PROMPT_CORE = f"""You are EMERALD, a Hyperliquid perps trading assistant.

Core Directive:
- Strictly adhere to the trading philosophy in your context documents.
- Your responses must reflect the mindset described in those documents.

Behavioral Guidelines:
- Be concise and actionable. No fluff.
- Only call tools if the user requests current price data.
- Maximum {AGENT_CONFIG.max_tool_calls_per_response} tool calls per response.
- If calling fetch_hl_raw multiple times, use different intervals each time.

Tool Usage (fetch_hl_raw):
Required parameters:
  - coin: Symbol (e.g., "BTC")
  - interval: "1m", "5m", "15m", "1h", "4h", "1d"
  - hours: Lookback period (integer)
  - limit: Max candles (integer)

Standard settings:
  - out="agent_outputs/<coin>_<interval>.json" (always set)
  - convert=True (for human-readable output)
  - significant_swings=True (always annotate swings)
  - fvg=True (always annotate Fair Value Gaps)

Configuration Limits:
{LOOKBACK_CONSTRAINTS}

If a user requests data beyond these limits:
1. Explicitly state which limit was exceeded
2. Explain what you're adjusting the parameters to
3. Proceed with the adjusted parameters

Mission:
- Fetch and analyze Hyperliquid perpetuals data
- Identify profitable setups aligned with context document strategies
- Provide clear trade ideas with reasoning
"""

# Append context documents
if CONTEXT_DOCUMENTS:
    SYSTEM_PROMPT = f"{SYSTEM_PROMPT_CORE}\n\n---\nContext Documents:\n{CONTEXT_DOCUMENTS}"
else:
    SYSTEM_PROMPT = SYSTEM_PROMPT_CORE
```

### Agent Creation

```python
agent = create_agent(
    model=model,
    tools=[fetch_hl_raw],  # Only one tool registered
    system_prompt=SYSTEM_PROMPT,
)
```

### Invocation

```python
response = agent.invoke(
    {
        "messages": [
            {
                "role": "user", 
                "content": "What's the setup on BTC 15m?"
            }
        ],
        "max_iterations": AGENT_CONFIG.max_iterations,  # Max reasoning loops
    }
)

final_message = response["messages"][-1].content
```

The agent:
1. Reads the user query
2. Consults system prompt (strategy + limits + personality)
3. Decides if tools are needed
4. Calls `fetch_hl_raw` if necessary
5. Analyzes returned data
6. Formulates response based on strategy context
7. Returns formatted markdown output

---

## Conversation Memory

**File**: `memory/session_manager.py`

EMERALD now has **persistent conversation memory** - the agent remembers your previous discussions and can maintain context across multiple invocations.

### How It Works

**Without Memory** (old behavior):
```bash
$ python agent/agent.py "What's BTC doing on 1h?"
[Analysis of BTC...]

$ python agent/agent.py "What about ETH?"
# ❌ No context - agent doesn't remember BTC discussion
```

**With Memory** (current behavior):
```bash
$ python agent/agent.py "What's BTC doing on 1h?"
🆕 Starting new session: 2025-11-08_session
[Analysis of BTC saved to memory...]

$ python agent/agent.py "What about ETH?"
📝 Continuing session: 2025-11-08_session (2 previous messages)
# ✅ Agent remembers BTC and can compare!
"ETH looks cleaner than the BTC setup we just looked at..."
```

### Key Features

- **Automatic Daily Sessions**: Creates or continues sessions based on today's date
- **Named Sessions**: Create dedicated sessions for different strategies or workflows
- **Configurable Memory Depth**: Default 20 messages, adjustable from 5-50+
- **Session Persistence**: All conversations stored as JSON in `conversations/`
- **Rich UI**: Visual indicators showing session status and message count

### Basic Usage

**Default Behavior** (auto-continue today's session):
```bash
python agent/agent.py "What's BTC doing on 1h?"
python agent/agent.py "What about ETH?"
python agent/agent.py "Which setup is better?"
# All three messages are part of the same conversation!
```

**Session Management Commands**:
```bash
# List all sessions
python agent/agent.py --list-sessions

# Use a specific session
python agent/agent.py --session "morning_trades" "Analyze BTC"

# Start a new session
python agent/agent.py --new "Fresh analysis"

# View session history
python agent/agent.py --show-session "2025-11-08_session"

# Delete a session
python agent/agent.py --delete-session "old_session"

# Custom memory depth
python agent/agent.py --max-history 30 "Complex analysis"
```

### Memory Architecture

The memory system uses a simple but effective approach:

1. **Storage**: JSON files (one per session) in `conversations/` directory
2. **Context Window**: Loads last N messages (default: 20) before each invocation
3. **Session Naming**: Auto-generated based on date or custom user-defined
4. **Metadata**: Tracks message count, timestamps, and conversation metadata

**Example Session File** (`conversations/2025-11-08_session.json`):
```json
{
  "session_id": "2025-11-08_session",
  "created_at": "2025-11-08T09:15:23",
  "updated_at": "2025-11-08T11:45:12",
  "messages": [
    {
      "role": "user",
      "content": "What's BTC doing on 1h?",
      "timestamp": "2025-11-08T09:15:23"
    },
    {
      "role": "assistant",
      "content": "BTC 1H Analysis...",
      "timestamp": "2025-11-08T09:16:45"
    }
  ],
  "metadata": {
    "message_count": 2
  }
}
```

### Use Cases

**Daily Trading Session**:
```bash
# Morning - automatic session creation
python agent/agent.py "What's the overall market bias?"
python agent/agent.py "BTC just swept the low. Good entry?"
python agent/agent.py "Compare with ETH setup"
# All saved to today's session automatically
```

**Strategy Development**:
```bash
# Dedicated session for testing a strategy
python agent/agent.py -s "fvg_strategy" "Show me BTC FVGs on 1h"
python agent/agent.py -s "fvg_strategy" "Which FVG is most likely to hold?"
python agent/agent.py -s "fvg_strategy" "How often do these work?"
```

**Multi-Coin Comparison**:
```bash
python agent/agent.py -s "comparison" "Analyze BTC, ETH, SOL on 1h"
python agent/agent.py -s "comparison" "Which has the cleanest setup?"
python agent/agent.py -s "comparison" "Show me the ETH entry"
```

### Token Management

The system automatically manages context to avoid token limits:

- **Default**: Last 20 messages included (≈10k-20k tokens)
- **Adjustable**: Use `--max-history N` to customize
- **Smart Truncation**: Older messages remain in storage (viewable with `--show-session`) but aren't included in context

### Best Practices

1. **Use descriptive session names** for dedicated workflows:
   ```bash
   python agent/agent.py -s "btc_scalping_strategy" "..."
   python agent/agent.py -s "swing_trade_ideas" "..."
   ```

2. **Clean up old sessions** periodically:
   ```bash
   python agent/agent.py --list-sessions
   python agent/agent.py --delete-session "2025-10-15_session"
   ```

3. **Adjust memory depth** based on complexity:
   ```bash
   # Quick questions - low memory
   python agent/agent.py --max-history 5 "Current BTC price?"

   # Deep analysis - high memory
   python agent/agent.py --max-history 40 "Review our strategy discussion"
   ```

### Future Enhancements

This is **Phase 1** of a 3-phase memory roadmap:

- **Phase 2** (planned): SQLite storage, automatic summarization, enhanced metadata
- **Phase 3** (future): Semantic search, interactive REPL, cross-session insights

For complete documentation, see `MEMORY_GUIDE.md`.

---

## Usage Examples

### Example 1: Basic Price Check

```bash
python agent.py "What's BTC doing on the 1h?"
```

**Agent reasoning**:
1. Sees "BTC" and "1h" in query
2. Knows it needs current data
3. Calls tool:
   ```python
   fetch_hl_raw(
       coin="BTC",
       interval="1h",
       hours=24,  # Default reasonable lookback
       limit=50,
       out="agent_outputs/BTC_1h.json",
       convert=True,
       significant_swings=True,
       fvg=True
   )
   ```
4. Receives annotated candles
5. Analyzes:
   - Recent swing highs/lows
   - FVGs present
   - Market structure (HH/HL or LL/LH)
6. Responds with current state and bias

### Example 2: Multi-Timeframe Analysis

```bash
python agent.py "Give me the full picture on ETH - Daily, 4H, and 1H"
```

**Agent reasoning**:
1. Recognizes need for multiple timeframes
2. Calls tool 3 times (max allowed per response):
   ```python
   fetch_hl_raw(coin="ETH", interval="1d", hours=168, limit=30, ...)
   fetch_hl_raw(coin="ETH", interval="4h", hours=168, limit=50, ...)
   fetch_hl_raw(coin="ETH", interval="1h", hours=72, limit=100, ...)
   ```
3. Analyzes hierarchy:
   - Daily: Overall trend (bullish/bearish)
   - 4H: Intermediate structure
   - 1H: Dealing range for entries
4. Checks alignment across timeframes
5. Responds with HTF bias and potential setups

### Example 3: Specific Setup Request

```bash
python agent.py "I want to long BTC. What's the best entry on 15m?"
```

**Agent reasoning**:
1. Understands directional bias (long = bullish)
2. Knows to check HTFs first per strategy
3. Fetches 1H to establish dealing range and bias
4. If HTFs are bullish, fetches 15m for entry
5. Looks for strategy criteria:
   - Price in discount (below 50% of 1H range)
   - Liquidity sweep (Asia low, swing low)
   - Displacement + FVG creation
   - Entry on pullback to FVG/OB
6. Responds with:
   - Entry level
   - Invalidation (stop loss)
   - Targets (internal FVG → external liquidity)
   - Risk management guidance

### Example 4: Constraint Handling

```bash
python agent.py "Show me 10 hours of 1m data on BTC"
```

**Agent response**:
```
You've requested 10 hours of 1m data, but 1m intervals are limited 
to 1.5 hours lookback due to configuration constraints. I'll fetch 
the maximum allowed (1.5 hours) instead.

[Proceeds to fetch 1.5 hours of 1m data and analyzes]
```

**Behind the scenes**:
```python
# In tool:
constraints = get_interval_constraint("1m")
# constraints.max_lookback_hours = 1.5

if hours > constraints.max_lookback_hours:
    return 400, {
        "error": f"1m interval is limited to 1.5 hours lookback. "
                 f"You requested 10 hours. Please reduce.",
        ...
    }
```

### Example 5: Coaching Mode

```bash
python agent.py "I keep closing my trades early. Any advice?"
```

**Agent reasoning**:
1. Recognizes this isn't a data request (no tool call)
2. Consults personality context:
   ```markdown
   As a coach, you can ultimately be summarized with 'tough love'.
   You encourage people to become better traders, to stay disciplined,
   be smart, and work hard.
   ```
3. Checks journal context for similar experiences:
   ```markdown
   ### Trade 3 Review
   I will admit that I closed my position early. 100% paper hands.
   The chart didn't show momentum slowing, so it could actually hit 
   my TP, but I closed early and took profit because I wasn't confident.
   ```
4. Responds with:
   - Acknowledgment of the issue
   - Reference to own journal showing same problem
   - Tough love advice on trusting the plan
   - Strategic reminder: "Thinking is the enemy. You have a plan? You execute."

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- Anthropic API key

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd EMERALD

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Project Setup

```bash
# Ensure directories exist
mkdir -p agent_outputs
mkdir -p agent_context

# Verify structure
tree -L 2
# Should show:
# .
# ├── agent.py
# ├── config/
# │   ├── __init__.py
# │   └── settings.py
# ├── tools/
# │   ├── tool_fetch_hl_raw.py
# │   └── context_manager.py
# ├── agent_context/
# │   ├── Mentality and Personality.md
# │   ├── Strategy.md
# │   └── November 2025.md
# └── agent_outputs/
```

### Running the Agent

```bash
# Basic usage (auto-continues today's session)
python agent/agent.py "Your query here"

# Examples
python agent/agent.py "What's the BTC setup on 1h?"
python agent/agent.py "Analyze ETH across Daily, 4H, 1H"
python agent/agent.py "I want to short. Give me the best entry on 15m"
python agent/agent.py "Why do I keep losing on breakouts?"

# Session management
python agent/agent.py --list-sessions                      # List all sessions
python agent/agent.py -s "morning_trades" "Analyze BTC"    # Use specific session
python agent/agent.py --new "Fresh analysis"               # Force new session
python agent/agent.py --show-session "2025-11-08_session"  # View session history
```

### Configuration Changes

To adjust limits, edit `config/settings.py`:

```python
# Change interval constraints
INTERVAL_CONSTRAINTS = {
    "1m": IntervalConstraints(
        max_lookback_hours=2.0,  # Increased from 1.5
        interval_minutes=1,
    ),
    # ...
}

# Change agent behavior
AGENT_CONFIG = AgentConfig(
    max_tool_calls_per_response=5,  # Increased from 3
    model_temperature=0.1,          # More deterministic
    # ...
)
```

Changes take effect immediately on next agent run (no restart needed).

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                               │
│                  "What's BTC doing on 1h?"                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT ANALYSIS PHASE                           │
│                                                                  │
│  Using Strategy Context:                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Check HTF Bias (W/D/4H/1H)                              │ │
│  │    - Look for HH/HL (bullish) or LL/LH (bearish)          │ │
│  │    - Identify last significant BOS                         │ │
│  │                                                            │ │
│  │ 2. Define Dealing Range (1H)                              │ │
│  │    - Most recent swing low → swing high that produced BOS │ │
│  │    - Calculate 50% level (equilibrium)                    │ │
│  │                                                            │ │
│  │ 3. Check Location Filter                                  │ │
│  │    - Longs: Price below 50% (discount)                    │ │
│  │    - Shorts: Price above 50% (premium)                    │ │
│  │                                                            │ │
│  │ 4. Identify Liquidity Pools                               │ │
│  │    - Previous Day High/Low                                │ │
│  │    - Session Highs/Lows (Asia/London/NY)                  │ │
│  │    - Swing points from annotated data                     │ │
│  │                                                            │ │
│  │ 5. Look for Entry Signals                                 │ │
│  │    - Liquidity sweep (external)                           │ │
│  │    - Displacement + FVG creation                          │ │
│  │    - Pullback to FVG/OB (internal)                        │ │
│  │    - Swing formation + confirmation                       │ │
│  │                                                            │ │
│  │ 6. Formulate Response                                     │ │
│  │    - State bias and reasoning                             │ │
│  │    - Identify setup (if present)                          │ │
│  │    - Specify entry, stops, targets                        │ │
│  │    - Apply personality (analytical + coaching)            │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FORMATTED RESPONSE                          │
│                                                                  │
│  ### BTC 1H Analysis                                             │
│                                                                  │
│  **HTF Bias**: Bearish                                           │
│  - Daily: LL/LH structure intact                                 │
│  - 4H: Recent BOS down confirmed                                 │
│  - 1H: Bearish momentum with displacement                        │
│                                                                  │
│  **Current State**: Price trading at premium (above 50% of 1H    │
│  dealing range). This aligns with short bias.                    │
│                                                                  │
│  **Recent Action**: Swept buy-side liquidity at $68,000 (session │
│  high), created bearish FVG during displacement down.            │
│                                                                  │
│  **Setup**: Short opportunity on pullback                        │
│  - Entry: $67,800 - $67,900 (FVG zone)                           │
│  - Stop: Above $68,200 (invalidation above swept high)           │
│  - Target 1: $67,200 (next FVG - internal liquidity)            │
│  - Target 2: $66,500 (Previous Day Low - external liquidity)    │
│                                                                  │
│  **Execution Notes**: Wait for pullback into the FVG. Don't      │
│  chase. A swing high formation at the FVG with rejection would   │
│  be ideal confirmation. Thinking is the enemy—have your plan,    │
│  execute when price reaches your level.                          │
│                                                                  │
│  Saved analysis to: agent_outputs/BTC_1h.json                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

### 1. **Configuration Over Code**

All tuneable parameters live in `config/settings.py`:

```python
# Bad: Hardcoded limits scattered in code
def fetch_data(interval):
    if interval == "1m":
        max_hours = 1.5  # What if this needs to change?
    elif interval == "5m":
        max_hours = 6
    # ...

# Good: Centralized configuration
INTERVAL_CONSTRAINTS = {
    "1m": IntervalConstraints(max_lookback_hours=1.5, ...),
    "5m": IntervalConstraints(max_lookback_hours=6, ...),
}

# Usage:
constraint = get_interval_constraint(interval)
if hours > constraint.max_lookback_hours:
    # Handle gracefully
```

**Benefits**:
- Change one file to adjust all behavior
- No hunting through code for magic numbers
- Easy to test different configurations
- Agent can communicate limits to users dynamically

### 2. **Separation of Concerns**

Each module has a single, clear responsibility:

```
config/settings.py       → Configuration only
tools/tool_fetch_hl_raw.py → Data fetching & processing
tools/context_manager.py   → Context document loading
agent.py                   → Orchestration & user interface
agent_context/*.md         → Domain knowledge (strategy, personality)
```

This means:
- Bug in data parsing? Only touch `tool_fetch_hl_raw.py`
- Need to adjust agent behavior? Only touch `settings.py`
- Want to refine strategy? Only edit markdown files
- No ripple effects across the codebase

### 3. **Graceful Degradation**

The system handles failures elegantly:

```python
# If API call fails:
try:
    r = requests.post(url, json=payload, timeout=15)
except requests.exceptions.RequestException as e:
    return 500, {
        "error": f"Network error: {str(e)}",
        "raw": None,
        "converted": None,
        "annotated": None,
        "final": None,
        "saved_to": None,
    }

# If parsing fails:
try:
    body = r.json()
except Exception:
    body = r.text  # Fall back to raw text

# If individual candles are malformed:
for c in arr:
    try:
        out.append(normalize(c))
    except Exception:
        continue  # Skip bad candle, keep processing
```

**Result**: One bad data point doesn't crash the entire system.

### 4. **Transparent to User**

The agent communicates constraints clearly:

```python
# System prompt includes:
"""
Configuration Limits:
  - 1m interval must look back no more than 1.5 hours.
  - 5m interval must look back no more than 6 hours.
  ...

If a user requests data beyond these limits, you MUST:
1. Explicitly state which limit was exceeded
2. Explain what you're adjusting the parameters to
3. Proceed with the adjusted parameters
"""

# Agent response:
"You've requested 10 hours of 1m data, but 1m intervals are 
limited to 1.5 hours. I'll fetch the maximum allowed instead."
```

Users understand *why* their request was modified, not just that it was.

### 5. **Type Safety & Documentation**

Python type hints and dataclasses provide self-documenting code:

```python
@dataclass
class IntervalConstraints:
    """Constraints for a specific candle interval."""
    
    max_lookback_hours: float
    """Maximum number of hours to look back for this interval."""
    
    interval_minutes: int
    """Number of minutes in one candle for this interval."""
    
    max_candles: int = 250
    """Maximum number of candles to return (safety cap)."""

def fetch_hl_raw(
    coin: str,
    interval: str,
    hours: int,
    limit: int,
    url: str = None,
    out: Optional[str] = None,
    convert: bool = False,
    significant_swings: bool = False,
    fvg: bool = False,
) -> Tuple[int, Dict[str, Any]]:
    """Fetch raw candle data from Hyperliquid API.
    
    Args:
        coin: The coin symbol (e.g., "BTC").
        interval: The candle interval (e.g., "1m", "5m", "15m", "1h", "4h", "1d").
        hours: Lookback period in hours.
        limit: Maximum number of candles to fetch. 250 at most.
        url: The Hyperliquid API endpoint URL. Defaults to config value.
        out: Optional file path to write output.
        convert: Whether to convert raw to human-usable candles.
        significant_swings: Whether to annotate output with significant swing highs/lows.
        fvg: Whether to annotate output with Fair Value Gaps and size.
        
    Returns:
        A tuple of (HTTP status code, metadata dict containing raw/final payload and optional output info).
    """
```

**Benefits**:
- IDE autocomplete works perfectly
- Type errors caught before runtime
- Documentation lives next to code (can't get outdated)
- Easy for new developers to understand

---

## Advanced Usage

### Custom Context Documents

Add new markdown files to `agent_context/`:

```markdown
<!-- meta: core, concept=risk-management -->
## Risk Management Rules

**Position Sizing**: Risk no more than 1% of account per trade.

**Stop Placement**: Always below/above the invalidation level:
- Longs: Below swept low or OB that launched displacement
- Shorts: Above swept high or OB that launched displacement

**Profit Taking**: Use layered exits:
1. 50% at 1R (risk:reward)
2. 25% at internal liquidity target
3. 25% running to external liquidity with trailing stop
```

The agent automatically loads and uses this in responses.

### Multi-Coin Analysis

```bash
python agent.py "Compare BTC and ETH setups on 1h"
```

Agent will:
1. Fetch both BTC and ETH data
2. Analyze each independently
3. Compare:
   - Which has cleaner structure
   - Which has better discount/premium positioning
   - Which has more confluence (HTF alignment + liquidity + FVG)
4. Recommend the higher probability setup

### Backtesting Integration (Future)

The tool's output format is designed for easy backtesting:

```python
import json

# Load saved data
with open("agent_outputs/BTC_1h.json") as f:
    candles = json.load(f)

# Run backtest
for i, candle in enumerate(candles):
    # Check if setup conditions met
    if candle.get("significantSwingLow") and i > 0:
        prev_candle = candles[i-1]
        if "fvg" in prev_candle and prev_candle["fvg"]["type"] == "bullish":
            # Setup detected
            entry = candle["close"]
            stop = candle["low"] - (candle["high"] - candle["low"]) * 0.1
            target = find_next_fvg(candles, i)
            
            # Simulate trade
            result = simulate_trade(candles[i:], entry, stop, target)
            results.append(result)

# Analyze results
win_rate = calculate_win_rate(results)
avg_rr = calculate_avg_risk_reward(results)
```

### Journal Integration

The agent learns from your trading journal:

```markdown
<!-- meta: tag=journal, tag=lesson, date=2025-11-06 -->
## Key Lesson: Paper Hands

I keep closing trades early when they're still valid. The chart 
shows no momentum slowing, stops are safe, but I close for small 
profits instead of letting them run to targets.

**Root Cause**: Lack of confidence in the plan. I'm not trusting 
the analysis that led me into the trade.

**Solution**: Before entering, write down:
1. Entry reason
2. Invalidation level
3. Target levels
4. Exit plan

Then don't deviate. Thinking is the enemy. Execute the plan.
```

When a user says "I keep closing early," the agent can reference your own journal entry and provide personalized coaching.

---

## Troubleshooting

### Issue: Agent not calling tools

**Symptom**: Agent responds without fetching data when it should.

**Possible causes**:
1. Query too vague: "Tell me about crypto" vs "What's BTC doing on 1h?"
2. System prompt discourages tool use
3. Model temperature too low (being overly conservative)

**Solution**:
```python
# In settings.py, increase temperature slightly:
AGENT_CONFIG = AgentConfig(
    model_temperature=0.35,  # From 0.25
    ...
)
```

Or be more explicit in query:
```bash
python agent.py "Fetch BTC 1h data and analyze the setup"
```

### Issue: Tool returns error "Configuration error: ... limited to X hours"

**Symptom**: Tool rejects request for exceeding interval limits.

**Cause**: Request exceeds configured `max_lookback_hours` for that interval.

**Solution**:
Either adjust config:
```python
# In config/settings.py:
INTERVAL_CONSTRAINTS = {
    "1m": IntervalConstraints(
        max_lookback_hours=3.0,  # Increased from 1.5
        ...
    ),
}
```

Or adjust query:
```bash
# Instead of:
python agent.py "Show me 5 hours of 1m data"

# Request:
python agent.py "Show me 1.5 hours of 1m data"
```

### Issue: Annotations missing (no swings/FVGs)

**Symptom**: Output contains candles but no `significantSwingHigh`, `significantSwingLow`, or `fvg` fields.

**Cause**: Tool parameters `significant_swings=False` or `fvg=False`.

**Solution**: Verify system prompt specifies default true:
```python
# In agent.py system prompt:
"""
Standard settings for every call:
  - significant_swings=True (always annotate swings)
  - fvg=True (always annotate Fair Value Gaps)
"""
```

Or explicitly request in query:
```bash
python agent.py "Fetch BTC 15m with swings and FVGs marked"
```

### Issue: Context documents not loading

**Symptom**: Agent doesn't reference strategy or personality.

**Cause**: 
1. `agent_context/` directory missing or empty
2. Markdown files not properly formatted
3. Loading function failing silently

**Solution**:
```python
# Add debug logging in agent.py:
CONTEXT_DOCUMENTS = load_markdown_context(BASE_DIR / "agent_context")
print(f"Loaded context: {len(CONTEXT_DOCUMENTS)} characters")
print(f"First 500 chars: {CONTEXT_DOCUMENTS[:500]}")

# Verify directory:
ls -la agent_context/
# Should show .md files

# Check file encoding:
file agent_context/*.md
# Should show: UTF-8 Unicode text
```

### Issue: API timeouts

**Symptom**: Requests fail with timeout errors.

**Cause**: Network latency or API slowness.

**Solution**: Increase timeout in config:
```python
# In config/settings.py:
TOOL_CONFIG = ToolConfig(
    request_timeout=30,  # Increased from 15
    ...
)
```

---

## Performance Considerations

### Token Usage

Full context documents can consume significant tokens. Current approach loads everything:

```python
# Current (simple but expensive):
CONTEXT_DOCUMENTS = load_markdown_context(BASE_DIR / "agent_context")
# ~10,000+ tokens for full strategy + journal

# Future optimization (selective loading):
core_context = context_manager.get_core_context()  # ~2,000 tokens
if "entry" in query.lower():
    entry_context = context_manager.get_sections(concept="entry")  # +500 tokens
if "15m" in query.lower():
    tf_context = context_manager.get_sections(timeframe="15m")  # +300 tokens
```

**Trade-off**: 
- Full loading: Higher token cost, complete knowledge always available
- Selective loading: Lower cost, risk missing relevant context

### API Rate Limits

Hyperliquid API has rate limits. Mitigate by:

1. **Caching**: Save fetched data, reuse for multiple analyses
   ```python
   # Check if recent data exists:
   cache_file = f"agent_outputs/BTC_1h.json"
   cache_age = time.time() - os.path.getmtime(cache_file)
   if cache_age < 300:  # Less than 5 minutes old
       # Use cached data
   else:
       # Fetch fresh data
   ```

2. **Batch requests**: Fetch multiple timeframes in one agent call rather than sequential queries

3. **Smart defaults**: Tool defaults to reasonable lookback periods:
   ```python
   # Instead of max data:
   fetch_hl_raw(coin="BTC", interval="1h", hours=168, limit=250)
   
   # Use sensible default:
   fetch_hl_raw(coin="BTC", interval="1h", hours=48, limit=50)
   ```

### Response Time

Typical flow timing:
- API request: 200-500ms
- Parsing & annotation: 50-100ms
- Agent reasoning: 2-5 seconds
- **Total**: ~3-6 seconds per query

To optimize:
1. Reduce `max_iterations` if agent over-thinks:
   ```python
   AGENT_CONFIG = AgentConfig(max_iterations=3, ...)  # From 5
   ```

2. Lower token count by selective context loading

3. Parallel tool calls (requires agent framework support):
   ```python
   # Theoretical:
   results = await asyncio.gather(
       fetch_hl_raw(coin="BTC", interval="1h", ...),
       fetch_hl_raw(coin="BTC", interval="15m", ...),
   )
   ```

---

## Future Enhancements

### 1. Selective Context Loading

Implement the `ContextManager` for on-demand loading:

```python
# In agent.py:
from tools.context_manager import ContextManager

context_mgr = ContextManager(BASE_DIR / "agent_context")

def build_system_prompt(query: str) -> str:
    # Always load core
    core = context_mgr.get_core_context()
    
    # Load relevant sections based on query
    sections = []
    if any(tf in query.lower() for tf in ["1m", "5m", "15m"]):
        sections.extend(context_mgr.get_sections(timeframe="15m"))
    if "entry" in query.lower() or "setup" in query.lower():
        sections.extend(context_mgr.get_sections(concept="entry"))
    if "liquidity" in query.lower():
        sections.extend(context_mgr.get_sections(concept="liquidity"))
    
    formatted = context_mgr._format_sections(sections)
    return f"{SYSTEM_PROMPT_CORE}\n\n{core}\n\n{formatted}"
```

### 2. Real-Time Alerts

Monitor price and notify on setups:

```python
# alert_daemon.py
import time
from agent import agent

watched_coins = ["BTC", "ETH"]
intervals = ["15m", "1h"]

while True:
    for coin in watched_coins:
        for interval in intervals:
            status, result = fetch_hl_raw(
                coin=coin,
                interval=interval,
                hours=6,
                limit=50,
                convert=True,
                significant_swings=True,
                fvg=True,
            )
            
            # Ask agent to analyze
            response = agent.invoke({
                "messages": [{
                    "role": "user",
                    "content": f"Check {coin} {interval} for A+ setups"
                }]
            })
            
            if "A+ setup" in response["messages"][-1].content:
                send_notification(f"{coin} {interval} setup detected!")
    
    time.sleep(300)  # Check every 5 minutes
```

### 3. Trade Execution Integration

Connect to Hyperliquid trading API:

```python
# execution.py
def execute_trade(setup: Dict[str, Any]):
    """
    Execute trade based on agent's analysis.
    
    setup = {
        "coin": "BTC",
        "direction": "long",
        "entry": 67800,
        "stop": 67500,
        "target": 68500,
        "size": calculate_position_size(risk=0.01)
    }
    """
    # Place order via Hyperliquid API
    order = hyperliquid_client.place_order(
        coin=setup["coin"],
        is_buy=setup["direction"] == "long",
        sz=setup["size"],
        limit_px=setup["entry"],
        reduce_only=False,
    )
    
    # Set stop loss
    stop_order = hyperliquid_client.place_order(
        coin=setup["coin"],
        is_buy=not (setup["direction"] == "long"),
        sz=setup["size"],
        limit_px=setup["stop"],
        reduce_only=True,
    )
    
    # Set take profit
    tp_order = hyperliquid_client.place_order(
        coin=setup["coin"],
        is_buy=not (setup["direction"] == "long"),
        sz=setup["size"],
        limit_px=setup["target"],
        reduce_only=True,
    )
```

### 4. Backtesting Framework

Test strategies on historical data:

```python
# backtest.py
class Backtester:
    def __init__(self, strategy_context: str):
        self.agent = create_agent_with_context(strategy_context)
        self.results = []
    
    def run(self, coin: str, interval: str, start_date: str, end_date: str):
        # Fetch historical data
        candles = fetch_historical(coin, interval, start_date, end_date)
        
        # Sliding window analysis
        for i in range(len(candles) - 100):
            window = candles[i:i+100]
            
            # Ask agent for setup
            response = self.agent.invoke({
                "messages": [{
                    "role": "user",
                    "content": f"Analyze this data: {json.dumps(window)}"
                }]
            })
            
            # Parse trade signals
            if "Entry:" in response:
                trade = parse_trade_from_response(response)
                result = simulate_trade(candles[i+100:], trade)
                self.results.append(result)
        
        # Generate report
        return self.analyze_results()
```

### 5. Multi-Agent System

Specialized agents for different tasks:

```python
# multi_agent.py
class TradingSystem:
    def __init__(self):
        self.analyst = create_agent(role="analyst")      # Pure TA
        self.risk_manager = create_agent(role="risk")    # Position sizing
        self.coach = create_agent(role="coach")          # Psychology
        self.executor = create_agent(role="executor")    # Order management
    
    def process_query(self, query: str):
        # Route to appropriate agent
        if "setup" in query.lower():
            analysis = self.analyst.invoke(query)
            risk_check = self.risk_manager.invoke(f"Review: {analysis}")
            return combine_responses(analysis, risk_check)
        
        elif "advice" in query.lower() or "help" in query.lower():
            return self.coach.invoke(query)
        
        elif "execute" in query.lower():
            setup = parse_setup(query)
            return self.executor.invoke(f"Execute: {setup}")
```

---

## Contributing

### Adding New Technical Indicators

1. Add detection function to `tool_fetch_hl_raw.py`:
   ```python
   def detect_order_blocks(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
       """Detect order blocks (last bullish/bearish candle before displacement)."""
       obs = []
       for i in range(len(candles) - 1):
           # Logic here
       return obs
   ```

2. Add to annotation function:
   ```python
   def annotate_candles(..., order_blocks: bool = False):
       # ...
       if order_blocks:
           for ob in detect_order_blocks(candles_raw):
               annotations[ob["i"]]["orderBlock"] = ob
   ```

3. Update tool signature:
   ```python
   def fetch_hl_raw(..., order_blocks: bool = False):
       # ...
       annotated = annotate_candles(..., include_ob=order_blocks)
   ```

4. Update system prompt:
   ```python
   """
   Standard settings:
     - order_blocks=True (always detect order blocks)
   """
   ```

### Adding New Context Documents

1. Create markdown file in `agent_context/`:
   ```markdown
   <!-- meta: core, concept=new-concept -->
   ## New Concept
   
   Explanation here...
   ```

2. Agent automatically loads on next run

3. Optionally add to `ContextManager` filters:
   ```python
   # Usage:
   sections = context_mgr.get_sections(concept="new-concept")
   ```

---

**Remember**: "Thinking is the enemy. You have a plan? You don't think, you execute."