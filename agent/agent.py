import os
import sys
from pathlib import Path
import argparse
import anthropic
import dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

#---------------------------
# GET CONTEXT DOCUMENTS
#---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.tool_fetch_hl_raw import fetch_hl_raw
from tools.ict_analyze_setup import ict_analyze_setup
from tools.ie_confluence_for_ict import ict_ie_confluence
from tools.ie_fetch_order_book import fetch_order_book_data
from tools.ie_fetch_funding import fetch_funding_rate_data
from tools.ie_fetch_trade_flow import fetch_trade_flow_data
from tools.ie_fetch_open_interest import fetch_open_interest_data
from tools.ie_liquidation_tracker import fetch_liquidation_tracker_tool
from tools.ie_order_book_microstructure import fetch_order_book_microstructure_tool
from config.settings import AGENT_CONFIG, ICT_CONFIG, generate_constraint_text
from memory.session_manager import SessionManager


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
    max_tokens=AGENT_CONFIG.max_tokens,
    temperature=AGENT_CONFIG.model_temperature,
    timeout=AGENT_CONFIG.model_timeout,
    max_retries=AGENT_CONFIG.max_retries,
)

# Context documents disabled for Phase 1 (ICT/SMC references removed)
# CONTEXT_DOCUMENTS = load_markdown_context(BASE_DIR / "agent_context")
CONTEXT_DOCUMENTS = ""

# Generate constraint text dynamically from config
LOOKBACK_CONSTRAINTS = generate_constraint_text()

SYSTEM_PROMPT_CORE = f"""You are EMERALD (Effective Market Evaluation and Rigorous Analysis for Logical Decisions), an ICT/SMC trading analyst for Hyperliquid perpetuals.

Core Philosophy - ICT/SMC Methodology:
- Markets move from liquidity to liquidity
- Trade WITH higher timeframe structure, never against it
- Enter on pullbacks into discount (longs) or premium (shorts)
- Structure > price action. HTF alignment is MANDATORY.

Behavioral Guidelines:
- Be direct, analytical, structure-focused
- Always state HTF bias clearly (Daily/4H/1H alignment)
- Provide entry zones, not exact prices (discount/premium areas)
- Risk-first: Stop loss, targets, R:R ratio are NON-NEGOTIABLE
- Maximum {AGENT_CONFIG.max_tool_calls_per_response} tool calls per response

PRIMARY TOOL: ict_analyze_setup
This is your main analysis tool. Use it for ALL ICT/SMC setup analysis.

Parameters:
  - coin: Symbol (e.g., "BTC", "ETH", "SOL")
  - account_balance: Optional (default: $10,000)

What it does:
1. Fetches multi-timeframe candles (Daily, 4H, 1H, 5M)
2. Analyzes HTF structure alignment (HH/HL vs LL/LH)
3. Calculates dealing range (swing low to swing high)
4. Determines discount/premium zones
5. Identifies liquidity pools (PDH/PDL, equal highs/lows)
6. Validates setup validity
7. Provides entry/stop/targets with position sizing

Returns:
- ✅ VALID SETUP: Direction, entry zone, stops, targets, R:R
- ❌ INVALID SETUP: Reason (HTF not aligned, wrong zone, no range, etc.)

ICT Setup Requirements (ALL must be true):
1. HTF Alignment: Daily + 4H + 1H must show SAME structure
   - ALL BULLISH (HH/HL) = Look for LONGS only
   - ALL BEARISH (LL/LH) = Look for SHORTS only
   - MIXED = NO TRADE (wait for clarity)

2. Dealing Range: Clear swing high and swing low identified
   - Range forms between liquidity grabs at swing points
   - Midpoint (50%) divides discount from premium

3. Price Position:
   - LONGS: Price must be in DISCOUNT (<50% of range)
   - SHORTS: Price must be in PREMIUM (>50% of range)
   - Mid-range (45-55%) = SKIP (poor R:R)

4. Liquidity Draw: Target must be clear
   - LONGS: Target = dealing range high or PDH
   - SHORTS: Target = dealing range low or PDL

Optional Confluence Tool: ict_ie_confluence
Adds quantitative confirmation to ICT setups.

Parameters:
  - coin: Symbol
  - direction: "LONG" or "SHORT"

Checks:
- Order book pressure aligned? (+20 pts)
- Trade flow aligned? (+20 pts)
- Funding extreme (contrarian)? (+15 pts)
- OI divergence (weak rally/selloff)? (+20 pts)

Grading (IE confluence):
- 60-75: Grade A+ (proceed with full size)
- 40-59: Grade A (proceed with 75% size)
- 20-39: Grade B (proceed with 50% size)
- 0-19: Grade C (valid ICT setup, but weak IE confirmation)

Analysis Workflow:
1. User asks: "Analyze BTC" or "BTC setup?"
2. Call: ict_analyze_setup(coin="BTC", account_balance=10000)
3. If VALID setup returned:
   a. Summarize HTF alignment and structure
   b. Show dealing range and current zone
   c. Present entry, stop, targets
   d. OPTIONALLY call ict_ie_confluence for additional confidence
4. If INVALID: Explain why (HTF conflict, wrong zone, etc.)

Response Format for VALID Setup:
```
🟢 BTC - LONG SETUP (ICT Valid)

**HTF Alignment**: BULLISH
  - Daily: HH/HL (confidence: 0.85)
  - 4H: HH/HL (confidence: 0.90)
  - 1H: HH/HL (confidence: 0.80)

**Dealing Range** (1H):
  - High: $68,000
  - Low: $66,000
  - Midpoint: $67,000
  - Current: $66,200 (10% of range - DEEP DISCOUNT)

**Entry Setup**:
  - Direction: LONG
  - Entry Zone: $66,100 - $66,300
  - Stop Loss: $64,400 (1:1 R:R)
  - Target 1: $68,000 (range high)
  - Target 2: $68,500 (PDH)
  - R:R: 1.0:1

**Liquidity Pools**:
  - PDH: $68,500
  - PDL: $65,800
  - Nearest above: $67,000

**Position Sizing**:
  - Risk: $100 (1% of $10k account)
  - Size: 0.05 BTC

[Optional] IE Confluence: 65/75 (Grade A) - Strong quantitative support
```

Response Format for INVALID Setup:
```
❌ BTC - NO ICT SETUP

**Reason**: HTF not aligned

**Structure Analysis**:
  - Daily: BULLISH (HH/HL)
  - 4H: BEARISH (LL/LH) ← CONFLICT
  - 1H: NEUTRAL

**Recommendation**: Wait for Daily and 4H to align. Currently conflicting timeframes.
```

Additional IE Tools (optional for deep dives):
- fetch_order_book_data: Check current order book pressure
- fetch_funding_rate_data: Check funding extremes
- fetch_trade_flow_data: Check institutional buying/selling
- fetch_open_interest_data: Check OI divergence
- fetch_liquidation_tracker_tool: Check recent liquidation events
- fetch_order_book_microstructure_tool: Check for spoofing/icebergs

Secondary Tool: fetch_hl_raw
Only use if you need raw candle data for custom analysis. The ict_analyze_setup tool already fetches all needed data.

Configuration Limits:
{LOOKBACK_CONSTRAINTS}

Mission:
- Analyze structure, not price predictions
- Only recommend setups with HTF alignment
- Trade WITH the market structure, never against it
- Discount for longs, premium for shorts - no exceptions
- ICT is a systematic methodology, not discretionary trading"""

# System prompt is pure quantitative now (no context documents in Phase 1)
SYSTEM_PROMPT = SYSTEM_PROMPT_CORE

#---------------------------
# STEP 2: CREATE THE AGENT
#---------------------------
agent = create_agent(
    model=model,
    tools=[
        # Primary ICT/SMC tool
        ict_analyze_setup,
        # IE Confluence for ICT setups
        ict_ie_confluence,
        # Individual IE tools (optional, for deep analysis)
        fetch_order_book_data,
        fetch_funding_rate_data,
        fetch_trade_flow_data,
        fetch_open_interest_data,
        fetch_liquidation_tracker_tool,
        fetch_order_book_microstructure_tool,
        # Raw data tool (rarely needed)
        fetch_hl_raw,
    ],
    system_prompt=SYSTEM_PROMPT,
)

#---------------------------
# STEP 3: SESSION MANAGER
#---------------------------
session_manager = SessionManager(BASE_DIR / "conversations")

#---------------------------
# STEP 4: INVOKE THE AGENT
#---------------------------
def invoke_with_memory(user_prompt: str, session_id: str, max_history: int = 20) -> str:
    """
    Invoke the agent with conversation memory.

    Args:
        user_prompt: The user's message
        session_id: The session ID to use
        max_history: Maximum number of previous messages to include (default: 20)

    Returns:
        The agent's response
    """
    console = Console()

    # Load conversation history (last N messages)
    history = session_manager.get_messages(session_id, limit=max_history)

    # Add current user message
    messages = history + [{"role": "user", "content": user_prompt}]

    # Show session info if there's history
    if history:
        console.print(f"[dim]📝 Continuing session: {session_id} ({len(history)} previous messages)[/dim]\n")
    else:
        console.print(f"[dim]🆕 Starting new session: {session_id}[/dim]\n")

    # Invoke agent with conversation history
    response = agent.invoke(
        {
            "messages": messages,
            "max_iterations": AGENT_CONFIG.max_iterations,
        }
    )

    final_message = response["messages"][-1].content

    # Save conversation to session
    session_manager.add_message(session_id, "user", user_prompt)
    session_manager.add_message(session_id, "assistant", final_message)

    return final_message


def list_sessions_command():
    """List all available conversation sessions."""
    console = Console()
    sessions = session_manager.list_sessions()

    if not sessions:
        console.print("[yellow]No conversation sessions found.[/yellow]")
        return

    # Create table
    table = Table(title="Conversation Sessions", show_header=True, header_style="bold cyan")
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Created", style="green")
    table.add_column("Updated", style="yellow")
    table.add_column("Messages", justify="right", style="magenta")

    for session_id in sessions:
        try:
            info = session_manager.get_session_info(session_id)
            created = info["created_at"][:19].replace("T", " ")
            updated = info["updated_at"][:19].replace("T", " ")
            msg_count = str(info["message_count"])

            table.add_row(session_id, created, updated, msg_count)
        except Exception:
            table.add_row(session_id, "Unknown", "Unknown", "Unknown")

    console.print(table)


def show_session_command(session_id: str):
    """Show messages from a specific session."""
    console = Console()

    try:
        session_data = session_manager.load_session(session_id)
    except FileNotFoundError:
        console.print(f"[red]Session '{session_id}' not found.[/red]")
        return

    console.print(f"\n[bold cyan]Session: {session_id}[/bold cyan]")
    console.print(f"[dim]Created: {session_data['created_at']}[/dim]")
    console.print(f"[dim]Messages: {len(session_data['messages'])}[/dim]\n")

    for msg in session_data["messages"]:
        role = msg["role"]
        content = msg["content"]
        timestamp = msg.get("timestamp", "Unknown")[:19].replace("T", " ")

        if role == "user":
            console.print(f"[bold green]User[/bold green] [dim]({timestamp})[/dim]:")
            console.print(f"{content}\n")
        else:
            console.print(f"[bold blue]Assistant[/bold blue] [dim]({timestamp})[/dim]:")
            md = Markdown(content)
            console.print(md)
            console.print()


def delete_session_command(session_id: str):
    """Delete a conversation session."""
    console = Console()

    if session_manager.delete_session(session_id):
        console.print(f"[green]✓ Session '{session_id}' deleted.[/green]")
    else:
        console.print(f"[red]Session '{session_id}' not found.[/red]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="EMERALD - AI Trading Assistant with Conversation Memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start or continue today's conversation
  python agent.py "What's BTC doing on 1h?"

  # Use a specific session
  python agent.py --session "morning_trades" "Analyze ETH"

  # Start a new session
  python agent.py --new "Fresh analysis on BTC"

  # List all sessions
  python agent.py --list-sessions

  # Show a specific session
  python agent.py --show-session "2025-11-08_session"

  # Delete a session
  python agent.py --delete-session "old_session"
        """
    )

    # Session management arguments
    parser.add_argument("--session", "-s", type=str, help="Use a specific session ID")
    parser.add_argument("--new", "-n", action="store_true", help="Force create a new session")
    parser.add_argument("--list-sessions", "-l", action="store_true", help="List all conversation sessions")
    parser.add_argument("--show-session", type=str, metavar="SESSION_ID", help="Show messages from a session")
    parser.add_argument("--delete-session", type=str, metavar="SESSION_ID", help="Delete a session")
    parser.add_argument("--max-history", type=int, default=20, help="Max number of previous messages to include (default: 20)")

    # The actual prompt/message
    parser.add_argument("prompt", nargs="*", help="Your message to the agent")

    args = parser.parse_args()

    console = Console()

    # Handle session management commands
    if args.list_sessions:
        list_sessions_command()
        sys.exit(0)

    if args.show_session:
        show_session_command(args.show_session)
        sys.exit(0)

    if args.delete_session:
        delete_session_command(args.delete_session)
        sys.exit(0)

    # Get user prompt
    if not args.prompt:
        console.print("[red]Error: Please provide a message for the agent.[/red]")
        console.print("Use --help for usage information.")
        sys.exit(1)

    user_prompt = " ".join(args.prompt)

    # Determine session ID
    if args.new:
        # Force new session
        session_id = session_manager._generate_session_id()
        console.print(f"[dim]🆕 Creating new session: {session_id}[/dim]")
    elif args.session:
        # Use specified session
        session_id = args.session
    else:
        # Auto-continue today's session
        session_id = session_manager.get_today_session_id()

    # Invoke agent with memory
    final_message = invoke_with_memory(user_prompt, session_id, max_history=args.max_history)

    # Render response
    md = Markdown(final_message)
    console.print(md)

    console.print(f"\n[dim]💾 Saved to session: {session_id}[/dim]")