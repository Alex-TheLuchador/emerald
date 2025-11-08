"""
EMERALD configuration package.

This package centralizes all configurable parameters for the trading agent
and data fetching tools.
"""

from .settings import (
    AGENT_CONFIG,
    TOOL_CONFIG,
    INTERVAL_CONSTRAINTS,
    IntervalConstraints,
    get_interval_constraint,
    generate_constraint_text,
)

__all__ = [
    "AGENT_CONFIG",
    "TOOL_CONFIG",
    "INTERVAL_CONSTRAINTS",
    "IntervalConstraints",
    "get_interval_constraint",
    "generate_constraint_text",
]
