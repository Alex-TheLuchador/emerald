"""
Configuration settings for EMERALD trading agent.

This module centralizes all configurable parameters for both the tool
and agent behavior, making them easy to adjust without touching core logic.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class IntervalConstraints:
    """Constraints for a specific candle interval."""
    
    max_lookback_hours: float
    """Maximum number of hours to look back for this interval."""
    
    interval_minutes: int
    """Number of minutes in one candle for this interval."""
    
    max_candles: int = 250
    """Maximum number of candles to return (safety cap)."""


# Interval configuration - the single source of truth
INTERVAL_CONSTRAINTS: Dict[str, IntervalConstraints] = {
    "1m": IntervalConstraints(
        max_lookback_hours=1.5,
        interval_minutes=1,
    ),
    "5m": IntervalConstraints(
        max_lookback_hours=6,
        interval_minutes=5,
    ),
    "15m": IntervalConstraints(
        max_lookback_hours=24,
        interval_minutes=15,
    ),
    "1h": IntervalConstraints(
        max_lookback_hours=84,
        interval_minutes=60,
    ),
    "4h": IntervalConstraints(
        max_lookback_hours=336,
        interval_minutes=240,
    ),
    "1d": IntervalConstraints(
        max_lookback_hours=2016,
        interval_minutes=1440,
    ),
}


def get_interval_constraint(interval: str) -> IntervalConstraints:
    """
    Get constraints for a given interval.
    
    Args:
        interval: The interval string (case-insensitive).
        
    Returns:
        IntervalConstraints for the interval.
        
    Raises:
        ValueError: If interval is not recognized.
    """
    normalized = interval.lower()
    if normalized not in INTERVAL_CONSTRAINTS:
        valid = ", ".join(INTERVAL_CONSTRAINTS.keys())
        raise ValueError(
            f"Unrecognized interval '{interval}'. "
            f"Valid intervals: {valid}"
        )
    return INTERVAL_CONSTRAINTS[normalized]


def generate_constraint_text() -> str:
    """
    Generate human-readable constraint text for system prompts.
    
    Returns:
        Formatted string listing all interval constraints.
    """
    lines = [
        f"  - {interval} interval must look back no more than {c.max_lookback_hours} hours."
        for interval, c in INTERVAL_CONSTRAINTS.items()
    ]
    return "\n".join(lines)


# Tool configuration
@dataclass
class ToolConfig:
    """Configuration for the Hyperliquid data fetching tool."""
    
    api_url: str = "https://api.hyperliquid.xyz/info"
    """Hyperliquid API endpoint."""
    
    request_timeout: int = 15
    """HTTP request timeout in seconds."""
    
    max_candles_absolute: int = 250
    """Absolute maximum candles to return (safety cap)."""
    
    default_output_subdir: str = "agent_outputs"
    """Default subdirectory for saved output files."""


# Agent configuration
@dataclass
class AgentConfig:
    """Configuration for the agent behavior."""
    
    max_tool_calls_per_response: int = 3
    """Maximum number of tool invocations in a single response."""
    
    max_iterations: int = 5
    """Maximum agent reasoning iterations."""
    
    model_temperature: float = 0.25
    """Model temperature for response generation."""
    
    max_tokens: int = 2048
    """Maximum tokens in model response."""
    
    model_timeout: int = 45
    """Model API call timeout in seconds."""
    
    max_retries: int = 2
    """Maximum retry attempts for model calls."""


# Global instances - import these in your code
TOOL_CONFIG = ToolConfig()
AGENT_CONFIG = AgentConfig()
