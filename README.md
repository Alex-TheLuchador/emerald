# Emerald

Emerald (Effective Market Evaluation and Rigorous Analysis for Logical Decisions) is a command-line trading assistant built on LangChain. Think of it as a focused copilot for Hyperliquid perpetuals: it knows your playbook, fetches fresh market data on demand, and answers back in plain trading English.

---

## What You Get

- **Hyperliquid perpetuals** talk to the agent about Hyperliquid perps, trading plans, or past journals and get structured responses.
- **On-demand market data** the agent calls a purpose-built Hyperliquid tool that can return raw, converted, or annotated candles.
- **Context-aware answers** Markdown files under `agent_context/` define Emeralds mentality, strategy rules, and trade journals. Sections are tagged so the agent only pulls in what is relevant, keeping latency and token usage low.
- **Rich console output** replies render as nicely formatted Markdown in your terminal.

---

## How the Agent Thinks

1. Loads core personality and philosophy from the context docs at startup.
2. Builds a system prompt that enforces trading guardrails (tool limits, required parameters, risk rules).
3. When you ask for information, it decides whether to answer immediately or call a tool.
4. Tool responses (market data or tagged context) are folded into the conversation and summarized back to you.

The agent currently uses Anthropic Claude Sonnet 4.5 via LangChains `create_agent`. Configuration lives in `agent/agent.py`.

---

## Quick Setup

```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

pip install anthropic python-dotenv langchain requests rich
```

1. Create a `.env` in the project root.
2. Add your Anthropic credentials:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. (Optional) Add or edit the Markdown files in `agent_context/` to customize strategy notes, journals, or personality.

---

## Running Emerald

Start the agent by passing a natural-language prompt:

```bash
python -m agent.agent "Walk me through a BTC 15m short if the 4h BOS just fired"
```

Behind the scenes the agent may:
- Ask clarifying questions if required tool parameters are missing.
- Fetch candles with the Hyperliquid tool (max 3 tool calls per reply).
- Load extra context via `get_context(...)` when it needs deeper strategy details.

Replies print with Rich, so bold text, lists, and tables stay readable.

---

## Tools in the Toolbox

### `get_context`
A LangChain tool that taps the context manager:

```text
get_context(timeframe="15m", concept="entry")
get_context(tag="journal", coin="BTC")
get_context(tag="journal", date="2025-11-03")
```

Markdown sections are tagged with HTML comments:

```markdown
<!-- meta: core, concept=entry, timeframe=15m -->
## 15m Entry Checklist
...
```

Supported metadata keys include `timeframe`, `concept`, `tag`, `date`, and `coin`. The agent only loads the sections that match the filters you give it.

### `fetch_hl_raw`
Defined in `tools/tool_fetch_hl_raw.py` and exposed to LangChain with `@tool`. Key behavior:

- **Inputs:** `coin`, `interval`, `hours`, `limit` (required), plus optional `out`, `convert`, `significant_swings`, and `fvg`.
- **Safety rails:** The agent enforces sensible lookback ceilings (e.g., max 6 hours for `5m`, 24 hours for `15m`) and always writes results to `agent_outputs/<coin>_<interval>.json`.
- **Outputs:** Returns raw API data plus optional human-friendly candles and annotations (significant swing highs/lows, Fair Value Gaps).

There is also a standalone CLI twin (`tools/fetch_hl_raw.py`) without the LangChain decorator:

```bash
python tools/fetch_hl_raw.py --coin ETH --interval 15m --hours 24 --limit 200 --convert --significant-swings --fvg --out eth_15m.json
```

---

## Working with the Context System

The context manager in `tools/context_manager.py` parses every `*.md` file under `agent_context/` and slices them into sections:

- Use metadata tags (`<!-- meta: ... -->`) to describe each section.
- Mark evergreen guidance with `core` so it loads on every run.
- Journal entries can be filtered by `date` or `coin`, making it easy to review only the trades you care about.

Utilities baked into the manager:
- `get_core_context()` � returns all core sections (personality, mindset).
- `get_context_menu()` � prints a menu of available metadata values.
- `search_content("liquidity")` � simple keyword search across indexed sections.
- `get_stats()` � number of sections, total characters, and metadata coverage (shown during CLI startup).

---

## Project Tour

```
agent/
  agent.py                # LangChain agent wiring, system prompt, CLI entrypoint
agent_context/
  Strategy.md             # Core strategy rules tagged with metadata
  Mentality and Personality.md
  November 2025.md        # Example journal with per-trade reviews
agent_outputs/            # Tool results land here (auto-created)
tools/
  tool_fetch_hl_raw.py    # LangChain-ready Hyperliquid tool
  fetch_hl_raw.py         # Standalone CLI variant
  context_manager.py      # Markdown parser and selective loader
  tool_fetch_hl_raw_explained.md  # Annotated walkthrough of the tool
```

---

## Tips & Next Steps

- Extend the context library with more tagged sections (e.g., `<!-- meta: timeframe=5m, concept=execution -->`).
- Record new trade journals in dated files so you can query by week or coin.
- Consider adding tests or smoke scripts for the context manager if you expand the metadata schema.
- Keep an eye on token usage; the current design already minimizes prompt size, but summaries or embeddings could further optimize long-term costs.
