# EMERALD Conversation Memory Guide

## Overview

EMERALD now has **persistent conversation memory**! The agent remembers your previous questions, analyses, and discussions within a session.

## What This Means

### Before (No Memory)
```bash
$ python agent/agent.py "What's BTC doing on 1h?"
[Agent analyzes BTC...]

$ python agent/agent.py "What about ETH?"
[Agent analyzes ETH, but has NO CONTEXT about BTC discussion]

$ python agent/agent.py "Which is better?"
"I don't have context. Which coins are you comparing?"
```

### After (With Memory)
```bash
$ python agent/agent.py "What's BTC doing on 1h?"
🆕 Starting new session: 2025-11-08_session
[Agent analyzes BTC and saves to memory...]
💾 Saved to session: 2025-11-08_session

$ python agent/agent.py "What about ETH?"
📝 Continuing session: 2025-11-08_session (2 previous messages)
[Agent analyzes ETH and remembers the BTC discussion]
"ETH looks cleaner than the BTC setup we just looked at..."
💾 Saved to session: 2025-11-08_session

$ python agent/agent.py "Which is better?"
📝 Continuing session: 2025-11-08_session (4 previous messages)
"Based on our analysis, ETH has the edge because..."
💾 Saved to session: 2025-11-08_session
```

---

## Basic Usage

### Default Behavior: Auto-Continue Today's Session

By default, EMERALD automatically continues your conversation from earlier today:

```bash
python agent/agent.py "What's BTC doing on 1h?"
# Creates or continues "2025-11-08_session"
```

**How it works:**
- First message of the day creates a new session
- Subsequent messages continue that same session
- Tomorrow, a new session is automatically created

---

## Session Management Commands

### List All Sessions

See all your conversation sessions:

```bash
python agent/agent.py --list-sessions
# or
python agent/agent.py -l
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Session ID          ┃ Created            ┃ Updated            ┃ Messages ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 2025-11-07_session  │ 2025-11-07 10:30:00│ 2025-11-07 14:22:00│       12 │
│ 2025-11-08_session  │ 2025-11-08 09:15:00│ 2025-11-08 11:45:00│        8 │
└─────────────────────┴────────────────────┴────────────────────┴──────────┘
```

---

### Use a Specific Session

Continue a specific session by name:

```bash
python agent/agent.py --session "morning_trades" "Analyze ETH 15m"
# or
python agent/agent.py -s "morning_trades" "Analyze ETH 15m"
```

**Use cases:**
- Separate sessions for different trading strategies
- Dedicated sessions per coin (btc_analysis, eth_analysis)
- Time-based sessions (morning_trades, afternoon_trades)

---

### Start a New Session

Force create a brand new session:

```bash
python agent/agent.py --new "What's BTC doing?"
# or
python agent/agent.py -n "What's BTC doing?"
```

**Use cases:**
- Starting fresh analysis
- Separating different market contexts
- Testing different strategies

---

### Show Session History

View all messages in a session:

```bash
python agent/agent.py --show-session "2025-11-08_session"
```

**Output:**
```
Session: 2025-11-08_session
Created: 2025-11-08T09:15:23
Messages: 8

User (2025-11-08 09:15):
What's BTC doing on 1h?

Assistant (2025-11-08 09:16):
# BTC 1H Analysis

**HTF Bias**: Bullish
- Daily: HH/HL structure intact...

[Full conversation shown with formatted markdown]
```

---

### Delete a Session

Remove a session you no longer need:

```bash
python agent/agent.py --delete-session "old_session"
```

---

## Advanced Usage

### Control Memory Depth

By default, EMERALD remembers the last **20 messages**. You can adjust this:

```bash
# Remember only last 10 messages (shorter context)
python agent/agent.py --max-history 10 "Analyze BTC"

# Remember last 50 messages (longer context, more tokens)
python agent/agent.py --max-history 50 "Analyze BTC"
```

**Trade-offs:**
- **Lower limit (5-10)**: Faster, cheaper, less context
- **Higher limit (30-50)**: Slower, more expensive, full context

**Token usage:**
- Each message uses ~200-1000 tokens
- 20 messages ≈ 10,000-20,000 tokens
- 50 messages ≈ 25,000-50,000 tokens

---

## Storage Location

Conversations are stored in `conversations/` directory as JSON files:

```
emerald/
└── conversations/
    ├── 2025-11-07_session.json
    ├── 2025-11-08_session.json
    └── morning_trades.json
```

**Format:**
```json
{
  "session_id": "2025-11-08_session",
  "created_at": "2025-11-08T09:15:23.456789",
  "updated_at": "2025-11-08T11:45:12.789456",
  "messages": [
    {
      "role": "user",
      "content": "What's BTC doing on 1h?",
      "timestamp": "2025-11-08T09:15:23.456789"
    },
    {
      "role": "assistant",
      "content": "BTC 1H Analysis...",
      "timestamp": "2025-11-08T09:16:45.123456"
    }
  ],
  "metadata": {
    "coins_discussed": [],
    "message_count": 2
  }
}
```

**Note:** This directory is `.gitignore`d - your conversations stay private.

---

## Workflow Examples

### Daily Trading Session

```bash
# Morning - start fresh
python agent/agent.py "What's the overall market bias today?"

# Continue throughout the day
python agent/agent.py "BTC just swept the low. Good entry?"
python agent/agent.py "What about ETH? Same setup?"
python agent/agent.py "Compare both"

# All saved to today's session automatically
```

---

### Strategy Development

```bash
# Dedicated session for strategy testing
python agent/agent.py -s "fvg_strategy" "Show me all BTC FVGs on 1h"
python agent/agent.py -s "fvg_strategy" "Which FVG is most likely to hold?"
python agent/agent.py -s "fvg_strategy" "Historical win rate on FVG entries?"

# Separate session for different strategy
python agent/agent.py -s "liquidity_sweeps" "Show me recent liquidity sweeps on ETH"
```

---

### Multi-Coin Analysis

```bash
# Session for comparing multiple coins
python agent/agent.py -s "altcoin_comparison" "Analyze BTC, ETH, SOL on 1h"
python agent/agent.py -s "altcoin_comparison" "Which has the cleanest setup?"
python agent/agent.py -s "altcoin_comparison" "Focus on ETH - show me the entry"
```

---

## How It Works (Technical)

### Memory System Architecture

1. **Session Manager** (`memory/session_manager.py`)
   - Handles CRUD operations for conversations
   - Stores sessions as JSON files
   - Manages session metadata

2. **Message Storage** (JSON format)
   - Each session = one JSON file
   - Messages stored with timestamps
   - Metadata tracks conversation context

3. **Context Window Management**
   - Loads last N messages (default: 20)
   - Prevents token overflow
   - Balances context vs. cost

4. **Agent Integration** (`agent/agent.py`)
   - Loads history before invocation
   - Appends new messages after response
   - Seamless memory integration

### Token Management

The agent automatically manages context window:

```python
# Pseudocode
history = session.get_messages(limit=20)  # Last 20 messages

messages = [
    # History provides context
    {"role": "user", "content": "What's BTC doing?"},
    {"role": "assistant", "content": "BTC is bullish..."},
    # ...18 more messages...
    # New message
    {"role": "user", "content": "What about ETH?"}
]

# Agent has full context of conversation
```

**What happens to older messages?**
- Messages beyond the limit (20) are not included
- They remain in storage (can view with `--show-session`)
- Future Phase 2 will add summarization

---

## Best Practices

### Session Naming

Use descriptive session IDs:

```bash
# Good
python agent/agent.py -s "btc_scalping_nov_8" "..."
python agent/agent.py -s "eth_swing_trades" "..."
python agent/agent.py -s "strategy_backtest_fvg" "..."

# Less helpful
python agent/agent.py -s "session1" "..."
python agent/agent.py -s "test" "..."
```

---

### Session Hygiene

Delete old sessions periodically:

```bash
# List sessions
python agent/agent.py -l

# Delete old ones
python agent/agent.py --delete-session "2025-10-01_session"
python agent/agent.py --delete-session "old_test"
```

---

### Memory Depth

Adjust based on conversation complexity:

```bash
# Quick questions - low memory
python agent/agent.py --max-history 5 "Current BTC price?"

# Complex analysis - high memory
python agent/agent.py --max-history 40 "Compare our 3 strategies"
```

---

## Troubleshooting

### Session Not Found

```bash
$ python agent/agent.py -s "nonexistent" "test"
Error: Session 'nonexistent' not found.
```

**Solution:** Check available sessions with `--list-sessions`

---

### Too Many Messages

If conversations get too long (50+ messages), agent may hit token limits.

**Solution:** Start a new session
```bash
python agent/agent.py --new "Continue analysis from earlier"
```

---

### Corrupted Session File

If a JSON file gets corrupted:

**Solution:** Delete and start fresh
```bash
python agent/agent.py --delete-session "corrupted_session"
python agent/agent.py -s "corrupted_session" "Fresh start"
```

---

## Future Enhancements (Phase 2+)

### Coming Soon

1. **Automatic Summarization**
   - Old messages compressed into summaries
   - Preserves key context while saving tokens

2. **Semantic Search**
   - Find relevant past discussions
   - "Show me when we discussed BTC FVGs"

3. **Interactive Mode**
   - REPL-style continuous conversation
   - No need to type `python agent/agent.py` each time

4. **Metadata Tracking**
   - Track coins discussed
   - Remember user preferences
   - Log trade setups

---

## Quick Reference

```bash
# Basic usage (auto-continue today)
python agent/agent.py "Your message"

# Session management
python agent/agent.py -l                           # List sessions
python agent/agent.py -s "name" "msg"              # Use session
python agent/agent.py -n "msg"                     # New session
python agent/agent.py --show-session "name"        # View history
python agent/agent.py --delete-session "name"      # Delete

# Advanced
python agent/agent.py --max-history 30 "msg"       # Custom memory depth
python agent/agent.py --help                       # Full help
```

---

**Remember:** The agent now has memory - use it to build context across your trading day!
