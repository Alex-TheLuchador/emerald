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
from logger import (
    log_session_start,
    log_session_end,
    log_context_loading,
    log_token_usage,
    log_error,
)


def load_markdown_context(context_dir: Path) -> tuple[str, int, int]:
    """Aggregate markdown files for use as system context.
    
    Returns:
        (combined_text, files_loaded, files_failed)
    """
    if not context_dir.exists():
        return "", 0, 0

    docs = []
    files_loaded = 0
    files_failed = 0
    
    for path in sorted(context_dir.rglob("*.md"), key=lambda p: p.relative_to(context_dir).as_posix()):
        relative_title = path.relative_to(context_dir).with_suffix("").as_posix()
        try:
            text = path.read_text(encoding="utf-8").strip()
            docs.append(f"### {relative_title}\n{text}")
            files_loaded += 1
        except Exception as exc:
            docs.append(f"### {relative_title}\n<Failed to read file: {exc}>")
            files_failed += 1
            
    combined = "\n\n".join(docs)
    return combined, files_loaded, files_failed

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

CONTEXT_DOCUMENTS, files_loaded, files_failed = load_markdown_context(BASE_DIR / "agent_context")
log_context_loading(files_loaded, files_failed, len(CONTEXT_DOCUMENTS))

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

Warning: Adhere to these guidelines strictly:
  - 1m interval must look back no more than 1.5 hours.
  - 5m interval must look back no more than 6 hours.
  - 15m interval must look back no more than 24 hours.
  - 1h interval must look back no more than 84 hours.
  - 4h interval must look back no more than 336 hours.
  - 1d interval must look back no more than 2016 hours.

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
# TOKEN COST CALCULATION
#---------------------------
# Claude Sonnet 4.5 pricing (as of Nov 2025)
COST_PER_INPUT_TOKEN = 0.000003  # $3 per million
COST_PER_OUTPUT_TOKEN = 0.000015  # $15 per million

def calculate_cost(usage):
    """Calculate cost from token usage dict."""
    if not usage:
        return None
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost = (input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN)
    return cost

#---------------------------
# STEP 3: INVOKE THE AGENT
#---------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py '<your prompt>'")
        sys.exit(1)
    
    user_prompt = " ".join(sys.argv[1:])
    log_session_start(user_prompt)
    
    try:
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
        
        # Extract token usage if available
        usage = response.get("usage_metadata", {})
        if usage:
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cost = calculate_cost(usage)
            log_token_usage(input_tokens, output_tokens, cost)
        
        final_message = response["messages"][-1].content
        
        # Render markdown beautifully
        console = Console()
        md = Markdown(final_message)
        console.print(md)
        
        log_session_end(success=True)
        
    except Exception as e:
        log_error("Agent invocation", e)
        log_session_end(success=False)
        raise
