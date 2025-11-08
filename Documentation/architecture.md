# EMERALD Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                               │
│                  "What's BTC doing on 1h?"                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY LAYER                                  │
│  Session Manager loads last N messages for context              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT (LangChain)                             │
│  - System Prompt (strategy + personality + limits)              │
│  - Claude Sonnet 4.5 (reasoning engine)                         │
│  - Tool Registry (IE metrics, data fetchers)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
             ┌───────────┴───────────┐
             │                       │
             ▼                       ▼
┌────────────────────────┐  ┌────────────────────────┐
│   PHASE 1 METRICS      │  │   PHASE 2 LIQUIDITY   │
│                        │  │                        │
│ • Order Book           │  │ • Microstructure      │
│ • Funding Rate         │  │ • Liquidations        │
│ • Trade Flow           │  │ • Cross-Exchange Arb  │
│ • Perpetuals Basis     │  │                        │
│ • Open Interest        │  │                        │
└────────────┬───────────┘  └────────────┬───────────┘
             │                           │
             └───────────┬───────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                CONVERGENCE SCORING ENGINE                        │
│  Calculates 0-100 score, assigns A+/A/B/C grade                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FORMATTED RESPONSE                             │
│  - Convergence score                                             │
│  - Grade                                                         │
│  - Aligned signals                                               │
│  - Recommendation                                                │
│  - Entry/Stop/Targets                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
emerald/
├── agent/
│   └── agent.py                 # Main entry point
│
├── config/
│   ├── __init__.py
│   └── settings.py              # All configuration (SINGLE SOURCE OF TRUTH)
│
├── tools/
│   ├── tool_fetch_hl_raw.py     # Hyperliquid candle data fetcher
│   ├── context_manager.py       # Context document loader
│   │
│   ├── ie_fetch_order_book.py           # Phase 1: Order book metrics
│   ├── ie_fetch_funding.py              # Phase 1: Funding rate
│   ├── ie_fetch_trade_flow.py           # Phase 1: Trade flow
│   ├── ie_fetch_perpetuals_basis.py     # Phase 1: Basis spread
│   ├── ie_fetch_open_interest.py        # Phase 1: OI divergence
│   ├── ie_fetch_institutional_metrics.py # Phase 1: Unified tool
│   ├── ie_multi_timeframe_convergence.py # Phase 1: Convergence engine
│   │
│   ├── ie_order_book_microstructure.py  # Phase 2: Spoofing/icebergs
│   ├── ie_liquidation_tracker.py        # Phase 2: Cascades
│   └── ie_cross_exchange_arb.py         # Phase 2: Arb signals
│
├── ie/
│   ├── __init__.py
│   ├── calculations.py          # Pure calculation functions
│   ├── data_models.py           # Dataclasses for all metrics
│   ├── cache.py                 # Thread-safe TTL cache
│   └── oi_history.json          # OI tracking (auto-created)
│
├── memory/
│   ├── __init__.py
│   └── session_manager.py       # Conversation persistence
│
├── agent_context/
│   ├── Mentality and Personality.md     # Agent personality
│   ├── Quantitative_Metrics_Guide.md    # IE guide for agent
│   └── November 2025.md                 # Trading journal
│
├── Documentation/
│   ├── strategy.md              # Trading strategy (READ FIRST)
│   ├── getting-started.md       # Installation & quickstart
│   ├── phase1-quantitative-engine.md
│   ├── phase2-advanced-liquidity.md
│   ├── architecture.md          # This file
│   ├── configuration.md         # Settings reference
│   └── tools-reference.md       # API reference
│
├── conversations/               # Session storage (gitignored)
├── agent_outputs/               # Generated data (gitignored)
│
├── requirements.txt             # Python dependencies
├── .env                         # API keys (gitignored)
└── README.md                    # Overview + TOC
```

---

## Core Components

### 1. Agent (`agent/agent.py`)

**Purpose**: Orchestrates everything - main entry point

**Key Functions**:
```python
def main():
    # 1. Parse CLI arguments (query, session, options)
    # 2. Load environment variables (API keys)
    # 3. Initialize Claude model
    # 4. Load context documents (strategy, personality)
    # 5. Build system prompt (context + constraints + personality)
    # 6. Create LangChain agent with tools
    # 7. Load conversation history (session manager)
    # 8. Invoke agent with query + history
    # 9. Save response to session
    # 10. Display formatted output
```

**System Prompt Structure**:
```python
SYSTEM_PROMPT = f"""
{CORE_DIRECTIVE}     # Quantitative approach, convergence scoring
{LOOKBACK_CONSTRAINTS}  # Interval limits (from config)
{CONTEXT_DOCUMENTS}  # Strategy, personality, journal
{TOOL_INSTRUCTIONS}  # How to use each tool
"""
```

### 2. Configuration (`config/settings.py`)

**Purpose**: Single source of truth for all settings

**Key Classes**:
```python
@dataclass
class IntervalConstraints:
    max_lookback_hours: float  # API data availability limit
    interval_minutes: int       # Candle duration
    max_candles: int           # Safety cap

@dataclass
class AgentConfig:
    max_tool_calls_per_response: int  # Prevent tool spam
    model_temperature: float           # 0.0-1.0 creativity
    max_tokens: int                    # Response length
    max_iterations: int                # Reasoning loops

@dataclass
class IEConfig:
    # Cache TTLs (seconds)
    order_book_cache_ttl: int = 2
    funding_cache_ttl: int = 300
    oi_cache_ttl: int = 300

    # Metric thresholds
    strong_imbalance_threshold: float = 0.4
    extreme_funding_threshold_pct: float = 10.0

    # Convergence weights
    order_book_weight: int = 25
    funding_weight: int = 20
    oi_weight: int = 30
    vwap_weight: int = 25

    # Grading thresholds
    a_plus_threshold: int = 70   # 70+ = A+
    a_threshold: int = 50        # 50-69 = A
    b_threshold: int = 30        # 30-49 = B
```

**Usage**: Import anywhere in codebase:
```python
from config.settings import AGENT_CONFIG, IE_CONFIG, get_interval_constraint

# Get interval limits
constraints = get_interval_constraint("1m")
if hours > constraints.max_lookback_hours:
    # Handle gracefully
```

### 3. Tools (`tools/*.py`)

**Purpose**: LangChain-compatible functions for agent to call

**Pattern**:
```python
# Core logic (regular function)
def fetch_data(coin: str) -> Dict[str, Any]:
    """Contains all the business logic."""
    # ... implementation
    return result

# LangChain wrapper
@tool
def fetch_data_tool(coin: str) -> Dict[str, Any]:
    """Thin wrapper for LangChain integration."""
    return fetch_data(coin)
```

**Why this pattern?**:
- Core function can be tested/used independently
- @tool decorator creates StructuredTool object
- Prevents circular reference errors
- Allows type-safe regular function calls

### 4. Institutional Engine (`ie/`)

**Purpose**: Pure calculation functions and data models

**Key Files**:
- `calculations.py`: Stateless calculation functions
- `data_models.py`: Type-safe dataclasses
- `cache.py`: Thread-safe TTL cache (prevents API spam)
- `oi_history.json`: Historical OI tracking for divergence detection

**Example**:
```python
# ie/calculations.py
def calculate_order_book_imbalance(
    bids: List[Tuple[float, float]],
    asks: List[Tuple[float, float]],
    depth: int
) -> Tuple[float, str]:
    """Pure function - no side effects, no state."""
    bid_volume = sum(size for _, size in bids[:depth])
    ask_volume = sum(size for _, size in asks[:depth])

    imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
    strength = classify_imbalance(imbalance)

    return imbalance, strength

# ie/data_models.py
@dataclass
class OrderBookMetrics:
    imbalance: float
    imbalance_strength: str
    top_bid: float
    top_ask: float
    spread: float
    spread_bps: float
    total_bid_volume: float
    total_ask_volume: float
    depth_analyzed: int
```

### 5. Memory System (`memory/session_manager.py`)

**Purpose**: Persistent conversation across invocations

**Key Features**:
- JSON file storage (one file per session)
- Auto-continue today's session by default
- Named sessions for workflows
- Configurable memory depth (last N messages)

**Storage Format**:
```json
{
  "session_id": "2025-11-08_session",
  "created_at": "2025-11-08T09:15:23Z",
  "updated_at": "2025-11-08T11:45:12Z",
  "messages": [
    {
      "role": "user",
      "content": "What's BTC doing?",
      "timestamp": "2025-11-08T09:15:23Z"
    },
    {
      "role": "assistant",
      "content": "BTC analysis...",
      "timestamp": "2025-11-08T09:16:45Z"
    }
  ],
  "metadata": {
    "message_count": 2
  }
}
```

**Usage Flow**:
```python
from memory.session_manager import SessionManager

# Initialize
session_mgr = SessionManager(conversations_dir="conversations/")

# Load history
session_id = "2025-11-08_session"
history = session_mgr.load_history(session_id, max_messages=20)

# Invoke agent with history as context
response = agent.invoke({
    "messages": history + [{"role": "user", "content": user_query}]
})

# Save response
session_mgr.append_message(session_id, "user", user_query)
session_mgr.append_message(session_id, "assistant", response)
```

### 6. Context Documents (`agent_context/*.md`)

**Purpose**: Define agent's knowledge, strategy, and personality

**Key Documents**:
- **Mentality and Personality.md**: Analytical, tough love coaching style
- **Quantitative_Metrics_Guide.md**: How to interpret IE metrics (375 lines)
- **November 2025.md**: Trading journal with real trade reviews

**Loading**:
```python
def load_markdown_context(context_dir: Path) -> str:
    """Aggregate all markdown files into system prompt."""
    docs = []
    for path in sorted(context_dir.rglob("*.md")):
        title = path.relative_to(context_dir).with_suffix("").as_posix()
        text = path.read_text(encoding="utf-8").strip()
        docs.append(f"### {title}\n{text}")
    return "\n\n".join(docs)

# In agent.py:
CONTEXT_DOCUMENTS = load_markdown_context(BASE_DIR / "agent_context")
SYSTEM_PROMPT = f"{CORE_PROMPT}\n\n---\nContext:\n{CONTEXT_DOCUMENTS}"
```

---

## Data Flow

### Example: "Analyze BTC 1h setup"

**Step 1**: User invokes agent
```bash
python agent/agent.py "Analyze BTC 1h setup"
```

**Step 2**: Session manager loads history
```python
session_id = "2025-11-08_session"
history = load_last_20_messages(session_id)
# Returns previous conversation for context
```

**Step 3**: Agent analyzes query
```
System Prompt:
- You are a quantitative trading analyst
- Use fetch_institutional_metrics_tool for analysis
- Grade setups A+/A/B/C based on convergence score
- Only trade 70+ scores
```

**Step 4**: Agent calls tools
```python
# Agent decides to fetch metrics
tool_call_1 = fetch_institutional_metrics_tool(coin="BTC")

# Returns:
{
    "metrics": {
        "order_book": {"imbalance": -0.62, ...},
        "funding": {"annualized_pct": 14.2, ...},
        "basis": {"basis_pct": 0.31, ...},
        # ...
    },
    "summary": {
        "convergence_score": 85,
        "grade": "A+",
        "recommendation": "high_conviction_short"
    }
}

# Agent may also call
tool_call_2 = fetch_multi_timeframe_convergence_tool(
    coin="BTC",
    timeframes=["1m", "5m", "15m"]
)
```

**Step 5**: Agent reasons
```
Claude Sonnet 4.5 analyzes:
- Convergence score: 85/100 (A+ grade)
- All 5 metrics aligned bearish
- Multi-timeframe VWAP extreme (+2σ all timeframes)
- Funding +14% (crowd maximally long)
- Conclusion: High conviction short
```

**Step 6**: Agent formats response
```markdown
### BTC 1H Setup - Grade: A+ (85/100)

**IE Validation**:
✓ Order Book: -0.62 (strong ask pressure)
✓ Funding: +14% annualized (extreme)
✓ Basis: +0.31% (aligned with funding)
✓ VWAP: +2.1σ (extreme overextension)

**Recommendation**: HIGH CONVICTION SHORT
Entry: $67,800-67,900
Stop: $68,200
Target: $66,500
```

**Step 7**: Session manager saves
```python
save_message(session_id, "user", "Analyze BTC 1h setup")
save_message(session_id, "assistant", formatted_response)
```

**Step 8**: User sees response
```
Terminal output displays formatted markdown response
```

---

## Caching Strategy

### Why Caching?

- Reduces API calls (rate limit protection)
- Faster responses (2ms vs 500ms)
- Consistency (same data for related queries)

### TTL by Metric

```python
IE_CONFIG = IEConfig(
    order_book_cache_ttl=2,      # Real-time (changes every second)
    funding_cache_ttl=300,       # 5 min (only updates every 8h)
    oi_cache_ttl=300,           # 5 min (slow updates)
    basis_cache_ttl=10,         # 10 sec (moderate changes)
    trade_flow_cache_ttl=60     # 1 min (candle-based)
)
```

### Implementation

```python
# ie/cache.py
class TTLCache:
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str, ttl: int) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]
            if time.time() - timestamp > ttl:
                del self._cache[key]  # Expired
                return None

            return value

    def set(self, key: str, value: Any):
        """Store value with current timestamp."""
        with self._lock:
            self._cache[key] = (value, time.time())

# Usage in tools:
from ie.cache import get_cache

cache = get_cache()
cache_key = f"order_book:{coin}:{depth}"

cached = cache.get(cache_key, ttl=2)
if cached:
    return cached

# Fetch fresh data
fresh_data = fetch_from_api()
cache.set(cache_key, fresh_data)
return fresh_data
```

---

## Error Handling

### Graceful Degradation

Every tool returns error dictionaries instead of throwing exceptions:

```python
def fetch_metric(coin: str) -> Dict[str, Any]:
    try:
        data = api_call()
        return {"success": True, "data": data}

    except requests.Timeout:
        return {
            "error": "API timeout",
            "coin": coin,
            "success": False
        }

    except ValueError as e:
        return {
            "error": f"Data parsing error: {str(e)}",
            "coin": coin,
            "success": False
        }

    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "coin": coin,
            "success": False
        }
```

### Agent Handles Errors

```python
# If tool returns error, agent continues with available data:
if "error" in order_book_metrics:
    response = "Order book data unavailable. Proceeding with funding + OI only."
else:
    # Use order book in analysis
```

---

## Key Design Principles

1. **Configuration over code** - All settings in `config/settings.py`
2. **Separation of concerns** - Each module has single responsibility
3. **Graceful degradation** - Errors don't crash system
4. **Type safety** - Dataclasses + type hints throughout
5. **Caching intelligence** - Different TTLs for different data types
6. **Tool pattern** - Core function + @tool wrapper
7. **Stateless calculations** - Pure functions in `ie/calculations.py`
8. **Context-aware agent** - System prompt includes strategy + personality
9. **Persistent memory** - Session-based conversation storage
10. **Modular architecture** - Easy to add new metrics/tools

---

## Performance Characteristics

### Typical Response Times

```
Component                    Time
─────────────────────────────────────
Session history load         ~5ms
API calls (parallel)         ~300ms
Data parsing/caching         ~50ms
Agent reasoning (Claude)     ~2-4s
Response formatting          ~10ms
Session save                 ~5ms
─────────────────────────────────────
Total                        ~3-5 seconds
```

### Optimization Opportunities

1. **Parallel tool calls** - Not currently implemented (LangChain limitation)
2. **Selective context loading** - Currently loads all context (can be selective)
3. **Response streaming** - Stream agent response as it's generated
4. **Batch queries** - Process multiple coins in single invocation

---

## Extending the System

### Adding a New Metric

1. **Create calculation function** in `ie/calculations.py`:
```python
def calculate_volume_profile(candles: List[Dict]) -> Dict[str, Any]:
    # Logic here
    return result
```

2. **Create dataclass** in `ie/data_models.py`:
```python
@dataclass
class VolumeProfileMetrics:
    poc: float  # Point of control
    value_area_high: float
    value_area_low: float
```

3. **Create tool** in `tools/ie_fetch_volume_profile.py`:
```python
def fetch_volume_profile(coin: str) -> Dict[str, Any]:
    # Implementation
    return result

@tool
def fetch_volume_profile_tool(coin: str) -> Dict[str, Any]:
    return fetch_volume_profile(coin)
```

4. **Register tool** in `agent/agent.py`:
```python
from tools.ie_fetch_volume_profile import fetch_volume_profile_tool

agent = create_agent(
    model=model,
    tools=[
        fetch_institutional_metrics_tool,
        fetch_volume_profile_tool,  # Add here
        # ...
    ],
    system_prompt=SYSTEM_PROMPT
)
```

### Adding a New Context Document

1. **Create markdown file** in `agent_context/volume_profile_guide.md`
2. **Add metadata tags**:
```markdown
<!-- meta: core, concept=volume-profile -->
## Volume Profile Analysis
...
```
3. **Agent automatically loads on next run**

---

## Summary

EMERALD's architecture is designed for:
- **Modularity**: Easy to add new metrics
- **Reliability**: Graceful error handling
- **Performance**: Intelligent caching
- **Extensibility**: Clean separation of concerns
- **Maintainability**: Configuration over code

Every component has a single, clear purpose. Data flows predictably from API → Cache → Calculations → Agent → User.

See [configuration.md](configuration.md) for detailed settings reference.
