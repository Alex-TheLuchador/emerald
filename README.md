# Emerald Agent

Emerald is a LangChain-driven command-line assistant focused on Hyperliquid perpetuals. The project combines a lightweight agent wrapper (`agent/agent.py`) and a specialized data-retrieval tool (`tools/tool_fetch_hl_raw.py`) that can annotate market data for strategy exploration.

- **Agent** – orchestrates prompts, model configuration, and tool wiring so that interacting with Hyperliquid feels like chatting with a trading assistant.
- **Tool** – contacts Hyperliquid’s API, normalizes the candle data, and can optionally annotate it with significant swing points and ICT-style Fair Value Gaps (FVGs).

## Setup

- Install Python 3.10+ along with required dependencies:
  ```bash
  pip install anthropic python-dotenv langchain requests rich
  ```
- Create a `.env` in the project root and add `ANTHROPIC_API_KEY=<your key>`.
- (Optional) Drop strategy references anywhere under `agent_context/` (subfolders included). Every `*.md` file is pulled into the agent’s system prompt.

## Basic Usage

- Run the agent with a natural-language prompt:
  ```bash
  python -m agent.agent "Scan SOL 1h for trend-confluence entries"
  ```
  The agent will enforce parameter collection, call `fetch_hl_raw` as needed, and stream the reply with Rich markdown formatting.

- Use the standalone fetcher for ad-hoc data pulls (no agent involved):
  ```bash
  python tools/fetch_hl_raw.py --coin ETH --interval 15m --hours 48 --limit 200 --convert --significant-swings --fvg --out eth_15m.json
  ```
  This script calls the Hyperliquid API directly, prints the raw response plus any requested conversions/annotations, and writes to `agent_outputs/eth_15m.json`. The LangChain-decorated tool lives in `tools/tool_fetch_hl_raw.py` and is reserved for the agent runtime.

## File Walkthrough

### `agent/agent.py`

**Imports and path bootstrap**  
Ensures the project root sits on `sys.path` so `tools` modules are importable even when the script runs as `python agent/agent.py`. Bringing in `anthropic`, `langchain`, `rich`, and `dotenv` here keeps the execution layer small but explicit.

**`load_markdown_context` helper**  
Recursively walks `agent_context/`, gathering every markdown file and prefixing each section with its relative path (e.g., `Trading Journals/November 2025`). It catches per-file I/O failures and records them inline so the agent can continue even if a context document is unreadable.

**API setup**  
`dotenv.load_dotenv()` hydrates environment variables at runtime. The Anthropic client is instantiated once; even though LangChain’s `init_chat_model` manages calls, early instantiation confirms the key is present and errors fast during startup.

**Model initialization**  
`init_chat_model` provides a LangChain-compliant wrapper over Anthropic’s Claude Sonnet 4.5 with tuned parameters:

- `max_tokens=2048` – balances response size with cost.  
- `temperature=0.25` – nudges toward deterministic, trade-focused answers.  
- `timeout` and `max_retries` guard against network hiccups.

**System prompt assembly**  
`SYSTEM_PROMPT_CORE` encodes Emerald’s behavior guidelines—including how many tool calls are allowed and what parameters must be confirmed before fetching data. If context files exist, they are appended beneath a divider so the model can blend mission instructions with strategy notes.

**Agent construction**  
`create_agent(...)` wires the chat model with a single tool (`fetch_hl_raw`). By constraining the toolset, the agent stays focused on market analysis while LangChain handles orchestration (tool routing, retry logic, etc.).

**CLI entry point**  
When run from the command line, the script:

1. Validates that a user prompt was supplied.  
2. Invokes the LangChain agent with the user message and a `max_iterations` cap of five (prevents runaway tool loops).  
3. Pulls the assistant’s final message and renders it as Markdown through Rich’s console pretty-printer.

The CLI keeps I/O minimal—standard print for usage guidance and formatted output for results—leaving state management to LangChain.

### `tools/tool_fetch_hl_raw.py`

**Constants**  
Define defaults for the Hyperliquid API endpoint, request headers, project root, and the output directory (`agent_outputs`). Using `Path.resolve()` makes the module robust regardless of where it is imported from.

**Numeric and timestamp helpers (`_to_num`, `_to_iso_utc`)**  
`_to_num` gracefully handles any raw numeric input from the API, returning `NaN` when conversion fails so downstream calculations can skip invalid values. `_to_iso_utc` converts millisecond timestamps into ISO-8601 strings with a “Z” suffix, standardizing displays.

**`fetch_hl_raw` tool**  
Decorated with `@tool`, making it LangChain-callable:

1. **Window calculation** – Derives `startTime` from both requested hours and candle limit, whichever produces the larger historical span. This keeps datasets consistent with user expectations even when the API over-delivers.  
2. **Payload construction** – Builds the minimal `candleSnapshot` request expected by Hyperliquid. All numeric inputs are cast to `int` defensively.  
3. **HTTP request** – Sends a JSON POST with a short timeout. The function captures the HTTP status and attempts to parse JSON, falling back to text when parsing fails so callers can still inspect the body.  
4. **Parsing & enrichment** – `parse_raw_keep_ohlc` normalizes the wire format into structured OHLC dictionaries. Optional conversion to human-readable floats (`convert_to_human`) and per-candle annotations (`annotate_candles`) layer analytical metadata as requested.  
5. **Output selection** – Chooses the richest available representation (annotated > converted > raw) for returning or saving.  
6. **File persistence** – If `out` is provided, resolves relative paths under `agent_outputs`, ensures directories exist, and writes pretty-printed JSON. Returning `saved_to` gives the agent a breadcrumb for surfacing download locations.  
7. **Return value** – Standardizes the result as `(status_code, metadata dict)` so both the agent and the CLI can access the raw response alongside any processed views.

**Raw parsing helpers**  
`_extract_iterable_from_raw` searches common response shapes (`candles`, `data`, `result`, `rows`) so the tool tolerates minor API changes.  
`parse_raw_keep_ohlc` walks each candle payload—handling both object and list formats—pulling the canonical OHLCV fields and chronologically sorting them. The function trims to the most recent 250 entries to prevent overly large in-memory datasets.

**Human-friendly transforms**  
`convert_to_human` outputs floats and ISO timestamps for quick inspection or CSV-style processing, avoiding the need for consumers to redo the same conversions.

**Swing and FVG detection**  
`compute_three_candle_swings_raw` finds local highs/lows over a three-candle window—simple but effective for ICT/SMC concepts.  
`compute_significant_swings_raw` filters those swings by comparing each with its neighbors, surfacing only meaningful pivots.  
`detect_fvgs_raw` evaluates three-candle sequences for price gaps that create bullish or bearish imbalances. All measurements use `_to_num` to stay resilient to malformed data.

**`annotate_candles`**  
Combines the analyses above into a per-candle dictionary that retains the original OHLC values, adds ISO timestamps, and inserts flags (`significantSwingHigh`, `significantSwingLow`) or structured FVG metadata when requested. By returning the same list length as the input, downstream consumers can zip annotations back to raw indices.

**CLI `main`**  
The module still contains an argparse-powered `main`, but because `fetch_hl_raw` is wrapped by LangChain's `@tool`, invoking this file directly results in a `StructuredTool` object instead of a plain function. For manual data pulls, rely on `tools/fetch_hl_raw.py`, which exposes the same functionality without the decorator.

## How Everything Fits Together

1. The agent builds a mission-oriented system prompt, optionally augmented by markdown context files.  
2. When a prompt arrives, LangChain decides whether to answer directly or call `fetch_hl_raw`.  
3. Tool responses include raw and enriched candle data, which the agent can interpret and summarize for the user.  
4. The console renderer in `agent.py` ensures the final explanation or trade idea appears with readable markdown styling.

## Next Steps & To-do

- Reduce token useage
  - Create context summaries and load detailed transcripts upon specific request?
