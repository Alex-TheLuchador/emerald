import os
import sys
from pathlib import Path
import anthropic
import dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from rich.console import Console
from rich.markdown import Markdown

#---------------------------
# GET CONTEXT DOCUMENTS
#---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.tool_fetch_hl_raw import fetch_hl_raw
from tools.context_manager import ContextManager


#---------------------------
# INITIALIZE CONTEXT MANAGER
#---------------------------
context_mgr = ContextManager(BASE_DIR / "agent_context")


#---------------------------
# CONTEXT RETRIEVAL TOOL
#---------------------------
@tool
def get_context(
    timeframe: str = None,
    concept: str = None,
    tag: str = None,
    date: str = None,
    coin: str = None,
) -> str:
    """Retrieve specific strategy or journal context from documentation.
    
    Use this tool to load detailed context only when needed. This keeps token usage low
    by avoiding loading all documentation on every query.
    
    Args:
        timeframe: Chart timeframe (e.g., "15m", "1h", "4h", "daily")
        concept: Trading concept (e.g., "entry", "structure", "liquidity", "risk")
        tag: Special tags (e.g., "journal" for trade reviews)
        date: Date for journal entries (e.g., "2025-11-03")
        coin: Cryptocurrency symbol for journal entries (e.g., "BTC", "ETH")
    
    Returns:
        Formatted context sections matching the filters.
    
    Examples:
        - get_context(timeframe="15m", concept="entry") → Returns 15m entry setup rules
        - get_context(concept="liquidity") → Returns liquidity concept explanations
        - get_context(tag="journal", date="2025-11-03") → Returns Nov 3 journal entries
        - get_context(tag="journal", coin="BTC") → Returns all BTC trade reviews
    """
    filters = {}
    if timeframe:
        filters['timeframe'] = timeframe
    if concept:
        filters['concept'] = concept
    if tag:
        filters['tag'] = tag
    if date:
        filters['date'] = date
    if coin:
        filters['coin'] = coin
    
    sections = context_mgr.get_sections(**filters)
    
    if not sections:
        available = context_mgr.get_context_menu()
        return f"No sections found matching those filters.\n\n{available}"
    
    # Format sections for context
    formatted = []
    for section in sections:
        formatted.append(f"## {section['title']}")
        formatted.append(f"*Source: {section['source_file']}*\n")
        formatted.append(section['content'])
        formatted.append("")  # Blank line between sections
    
    return "\n".join(formatted)


#---------------------------
# API SETUP
#---------------------------

dotenv.load_dotenv() 
api_key = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(
    api_key=api_key,
)

#---------------------------
# STEP 1: INITIALIZE MODEL
#---------------------------
model = init_chat_model(
    model="anthropic:claude-sonnet-4-5",
    max_tokens=2048,
    temperature=0.25,
    timeout=45,
    max_retries=2,
)

#---------------------------
# STEP 2: BUILD SYSTEM PROMPT
#---------------------------

# Load only core context by default (dramatically reduces token usage)
CORE_CONTEXT = context_mgr.get_core_context()
CONTEXT_MENU = context_mgr.get_context_menu()

# Get context stats for transparency
stats = context_mgr.get_stats()

SYSTEM_PROMPT_CORE = """You are EMERALD (Effective Market Evaluation and Rigorous Analysis for Logical Decisions), a Hyperliquid perps trading assistant.

Core Directive:
- Strictly adhere to the trading philosophy, mentality, and strategies outlined in your context documents.
- Your responses must reflect the mindset and principles described in those documents.

Behavioral Guidelines:
- Be concise and actionable. No fluff.
- Only call tools if the user requests information that specifically requires current price data or analysis.
- Maximum 3 tool calls per response.
- If calling fetch_hl_raw multiple times, use different intervals each time.
- Confirm missing required parameters before calling tools.

Context Management:
- You have access to detailed strategy and journal context via the get_context tool.
- Core personality and philosophy are always loaded.
- Request specific context sections when you need detailed rules or past trade analysis.
- Use get_context to load only what's relevant to the current query—this keeps responses fast and cost-effective.

Tool Usage (fetch_hl_raw):
Required parameters (confirm if missing):
  - coin: Symbol (e.g., "BTC")
  - interval: "1m", "5m", "15m", "1h", "4h", "1d"
  - hours: Lookback period (integer)
  - limit: Max candles (integer)

Standard settings for every call:
  - out="agent_outputs/<coin>_<interval>.json" (always set)
  - convert=True (for human-readable output)
  - significant_swings=True (always annotate swings)
  - fvg=True (always annotate Fair Value Gaps)

Warning: Adhere to these guidelines strictly:
  - 1m interval must look back no more than 1.5 hours.
  - 5m interval must look back no more than 6 hours.
  - 15m interval must look back no more than 24 hours.
  - 1h interval must look back no more than 84 hours.
  - 4h interval must look back no more than 336 hours.
  - 1d interval must look back no more than 2016 hours.

Tool Usage (get_context):
Use this to retrieve specific sections of strategy documentation or journal entries.
Available filters:
  - timeframe: "15m", "1h", "4h", "daily", etc.
  - concept: "entry", "structure", "liquidity", "risk", etc.
  - tag: "journal" for trade reviews
  - date: "2025-11-03" for specific journal dates
  - coin: "BTC", "ETH", etc. for coin-specific journals

Examples:
  - User asks about 15m entries → Call get_context(timeframe="15m", concept="entry")
  - User asks about liquidity → Call get_context(concept="liquidity")
  - User asks what happened in last BTC trade → Call get_context(tag="journal", coin="BTC")
  - User asks for analysis → Fetch data first, THEN load relevant strategy context if needed

Mission:
- Fetch and analyze Hyperliquid perpetuals data
- Identify profitable setups aligned with context document strategies
- Provide clear trade ideas with reasoning based on the documented approach"""

# Show context menu so agent knows what's available
SYSTEM_PROMPT = f"""{SYSTEM_PROMPT_CORE}

---
CONTEXT SYSTEM STATUS:
- Total sections available: {stats['total_sections']}
- Core context loaded by default (personality, philosophy)
- Detailed strategy sections available on-demand

{CONTEXT_MENU}

---
ALWAYS-LOADED CORE CONTEXT:
{CORE_CONTEXT}
"""

#---------------------------
# STEP 3: CREATE THE AGENT
#---------------------------
agent = create_agent(
    model=model,
    tools=[fetch_hl_raw, get_context],
    system_prompt=SYSTEM_PROMPT,
)

#---------------------------
# STEP 4: INVOKE THE AGENT
#---------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py '<your prompt>'")
        print("\nContext System Info:")
        print(f"  - {stats['total_sections']} sections available")
        print(f"  - {stats['total_characters']:,} total characters indexed")
        print(f"  - Metadata keys: {', '.join(stats['metadata_keys'])}")
        sys.exit(1)
    
    user_prompt = " ".join(sys.argv[1:])
    
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ],
            "max_iterations": 5,
        }
    )
    
    final_message = response["messages"][-1].content
    
    # Render markdown beautifully
    console = Console()
    md = Markdown(final_message)
    console.print(md)