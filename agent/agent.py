import os
import sys
from pathlib import Path
import anthropic
import dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from rich.console import Console
from rich.markdown import Markdown

#---------------------------
# GET CONTEXT DOCUMENTS
#---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.tool_fetch_hl_raw import fetch_hl_raw


def load_markdown_context(context_dir: Path) -> str:
    """Aggregate markdown files for use as system context."""
    if not context_dir.exists():
        return ""

    docs = []
    for path in sorted(context_dir.rglob("*.md"), key=lambda p: p.relative_to(context_dir).as_posix()):
        relative_title = path.relative_to(context_dir).with_suffix("").as_posix()
        try:
            text = path.read_text(encoding="utf-8").strip()
        except Exception as exc:
            docs.append(f"### {relative_title}\n<Failed to read file: {exc}>")
            continue
        docs.append(f"### {relative_title}\n{text}")
    return "\n\n".join(docs)

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
    max_tokens=2048,  # Balanced limit
    temperature=0.25,
    timeout=45,
    max_retries=2,
)

CONTEXT_DOCUMENTS = load_markdown_context(BASE_DIR / "agent_context")

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

Mission:
- Fetch and analyze Hyperliquid perpetuals data
- Identify profitable setups aligned with context document strategies
- Provide clear trade ideas with reasoning based on the documented approach"""

if CONTEXT_DOCUMENTS:
    SYSTEM_PROMPT = f"{SYSTEM_PROMPT_CORE}\n\n---\nContext Documents:\n{CONTEXT_DOCUMENTS}"
else:
    SYSTEM_PROMPT = SYSTEM_PROMPT_CORE

#---------------------------
# STEP 2: CREATE THE AGENT
#---------------------------
agent = create_agent(
    model=model,
    tools=[fetch_hl_raw],
    system_prompt=SYSTEM_PROMPT,
)

#---------------------------
# STEP 3: INVOKE THE AGENT
#---------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py '<your prompt>'")
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
