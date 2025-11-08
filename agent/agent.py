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
from config.settings import AGENT_CONFIG, generate_constraint_text
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

CONTEXT_DOCUMENTS = load_markdown_context(BASE_DIR / "agent_context")

# Generate constraint text dynamically from config
LOOKBACK_CONSTRAINTS = generate_constraint_text()

SYSTEM_PROMPT_CORE = f"""You are EMERALD (Effective Market Evaluation and Rigorous Analysis for Logical Decisions), a Hyperliquid perps trading assistant.

Core Directive:
- Strictly adhere to the trading philosophy, mentality, and strategies outlined in your context documents.
- Your responses must reflect the mindset and principles described in those documents.

Behavioral Guidelines:
- Be concise and actionable. No fluff.
- Only call tools if the user requests information that specifically requires current price data or analysis.
- Maximum {AGENT_CONFIG.max_tool_calls_per_response} tool calls per response.
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

Configuration Limits:
{LOOKBACK_CONSTRAINTS}

If a user requests data beyond these limits, you MUST:
1. Explicitly state which limit was exceeded
2. Explain what you're adjusting the parameters to
3. Proceed with the adjusted parameters

Example: "You've requested 5 hours of 1m data, but 1m intervals are limited to 1.5 hours lookback due to configuration constraints. I'll fetch the maximum allowed (1.5 hours) instead."

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