import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Setup
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure logger
logger = logging.getLogger("emerald")
logger.setLevel(logging.INFO)

# File handler
log_file = LOG_DIR / "emerald.log"
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger.addHandler(file_handler)

# Console handler (optional, for errors only)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(console_handler)


# Convenience functions
def log_session_start(prompt: str):
    """Log the start of an agent session."""
    logger.info("=" * 80)
    logger.info(f"SESSION START | Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")


def log_session_end(success: bool = True):
    """Log the end of an agent session."""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"SESSION END | Status: {status}")
    logger.info("=" * 80)


def log_context_loading(files_loaded: int, files_failed: int, total_chars: int):
    """Log context document loading stats."""
    logger.info(f"Context Loading | Loaded: {files_loaded} files, Failed: {files_failed}, Total chars: {total_chars:,}")


def log_tool_call(tool_name: str, params: Dict[str, Any]):
    """Log a tool invocation."""
    param_str = ", ".join(f"{k}={v}" for k, v in params.items() if k not in ["url", "out"])
    logger.info(f"Tool Call | {tool_name} | {param_str}")


def log_api_call(coin: str, interval: str, status_code: int, response_size: int, duration_ms: int):
    """Log Hyperliquid API call."""
    logger.info(
        f"API Call | Hyperliquid | {coin} {interval} | "
        f"Status: {status_code} | Size: {response_size} bytes | Duration: {duration_ms}ms"
    )


def log_market_data(coin: str, interval: str, hours: int, candles_received: int):
    """Log market data fetch summary."""
    logger.info(
        f"Market Data | {coin} {interval} | "
        f"Lookback: {hours}h | Candles: {candles_received}"
    )


def log_token_usage(input_tokens: int, output_tokens: int, cost_usd: Optional[float] = None):
    """Log token usage and cost."""
    cost_str = f" | Cost: ${cost_usd:.4f}" if cost_usd else ""
    logger.info(f"Token Usage | Input: {input_tokens:,} | Output: {output_tokens:,}{cost_str}")


def log_strategy_decision(decision: str, reasoning: str):
    """Log a strategy decision with reasoning."""
    logger.info(f"Strategy Decision | {decision}")
    if reasoning:
        # Split long reasoning into multiple lines for readability
        lines = reasoning.split('\n')
        for line in lines[:5]:  # First 5 lines only
            if line.strip():
                logger.info(f"  Reasoning: {line.strip()}")
        if len(lines) > 5:
            logger.info(f"  ... (truncated)")


def log_error(context: str, error: Exception):
    """Log an error with context."""
    logger.error(f"Error | {context} | {type(error).__name__}: {str(error)}")


def log_file_write(file_path: str, size_bytes: int):
    """Log file write operation."""
    logger.info(f"File Write | {file_path} | Size: {size_bytes:,} bytes")
