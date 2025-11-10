"""
Market Structure Analyzer for ICT Strategy

Determines market structure bias based on swing patterns:
- Bullish Structure: Higher Highs (HH) + Higher Lows (HL)
- Bearish Structure: Lower Lows (LL) + Lower Highs (LH)
- Neutral: No clear pattern (skip trades)

Also detects Break of Structure (BOS) and Change of Character (CHoCH) events.
"""

from typing import List, Dict, Any, Literal, Optional
import sys
from pathlib import Path

# Add project root to path for config import
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ICT_CONFIG


StructureBias = Literal["BULLISH", "BEARISH", "NEUTRAL"]


def _to_num(x: Any) -> float:
    """Convert value to float, return nan if conversion fails."""
    try:
        return float(x)
    except Exception:
        return float("nan")


def determine_structure_bias(
    swing_highs: List[Dict[str, Any]],
    swing_lows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Determine market structure bias from swing highs and lows.

    Args:
        swing_highs: List of swing high dictionaries
        swing_lows: List of swing low dictionaries

    Returns:
        Dictionary containing:
        - bias: "BULLISH", "BEARISH", or "NEUTRAL"
        - pattern: "HH/HL", "LL/LH", or "RANGING"
        - last_bos: Most recent Break of Structure event (if any)
        - confidence: 0.0-1.0 (how clear the structure is)

    Example:
        >>> highs = [{"price": 100}, {"price": 105}, {"price": 110}]  # Higher Highs
        >>> lows = [{"price": 95}, {"price": 98}, {"price": 102}]     # Higher Lows
        >>> result = determine_structure_bias(highs, lows)
        >>> result["bias"]  # "BULLISH"
    """
    # Need at least 2 swings to determine structure
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {
            "bias": "NEUTRAL",
            "pattern": "RANGING",
            "last_bos": None,
            "confidence": 0.0,
            "reason": "Insufficient swing data (need 2+ highs and 2+ lows)"
        }

    # Get recent swings (last 3-5 for analysis)
    recent_highs = swing_highs[-5:] if len(swing_highs) >= 5 else swing_highs
    recent_lows = swing_lows[-5:] if len(swing_lows) >= 5 else swing_lows

    # Analyze highs pattern
    higher_highs = 0
    lower_highs = 0
    for i in range(1, len(recent_highs)):
        curr_price = _to_num(recent_highs[i]["price"])
        prev_price = _to_num(recent_highs[i-1]["price"])
        if curr_price > prev_price:
            higher_highs += 1
        elif curr_price < prev_price:
            lower_highs += 1

    # Analyze lows pattern
    higher_lows = 0
    lower_lows = 0
    for i in range(1, len(recent_lows)):
        curr_price = _to_num(recent_lows[i]["price"])
        prev_price = _to_num(recent_lows[i-1]["price"])
        if curr_price > prev_price:
            higher_lows += 1
        elif curr_price < prev_price:
            lower_lows += 1

    # Determine bias
    # Bullish: HH and HL
    if higher_highs > 0 and higher_lows > 0 and lower_highs == 0 and lower_lows == 0:
        # Strong bullish: all swings making highs
        bias = "BULLISH"
        pattern = "HH/HL"
        confidence = 1.0
    elif higher_highs >= lower_highs and higher_lows >= lower_lows and (higher_highs + higher_lows) > 0:
        # Moderate bullish: majority making highs
        bias = "BULLISH"
        pattern = "HH/HL"
        total_swings = higher_highs + higher_lows + lower_highs + lower_lows
        bullish_swings = higher_highs + higher_lows
        confidence = bullish_swings / total_swings if total_swings > 0 else 0.0
    # Bearish: LL and LH
    elif lower_lows > 0 and lower_highs > 0 and higher_highs == 0 and higher_lows == 0:
        # Strong bearish: all swings making lows
        bias = "BEARISH"
        pattern = "LL/LH"
        confidence = 1.0
    elif lower_lows >= higher_lows and lower_highs >= higher_highs and (lower_lows + lower_highs) > 0:
        # Moderate bearish: majority making lows
        bias = "BEARISH"
        pattern = "LL/LH"
        total_swings = higher_highs + higher_lows + lower_highs + lower_lows
        bearish_swings = lower_lows + lower_highs
        confidence = bearish_swings / total_swings if total_swings > 0 else 0.0
    else:
        # Mixed or unclear
        bias = "NEUTRAL"
        pattern = "RANGING"
        confidence = 0.0

    # Apply minimum confidence threshold
    if confidence < ICT_CONFIG.min_structure_confidence:
        bias = "NEUTRAL"
        pattern = "RANGING"

    return {
        "bias": bias,
        "pattern": pattern,
        "last_bos": None,  # BOS detection would require full candle data
        "confidence": round(confidence, 2),
        "highs_analyzed": len(recent_highs),
        "lows_analyzed": len(recent_lows),
        "higher_highs": higher_highs,
        "lower_highs": lower_highs,
        "higher_lows": higher_lows,
        "lower_lows": lower_lows,
    }


def detect_break_of_structure(
    candles: List[Dict[str, Any]],
    structure_bias: StructureBias,
    swing_highs: List[Dict[str, Any]],
    swing_lows: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Detect Break of Structure (BOS) events.

    BOS = Price breaks a swing point IN THE DIRECTION of the trend.
    - Bullish BOS: Price breaks above a recent swing high
    - Bearish BOS: Price breaks below a recent swing low

    Args:
        candles: Recent candle data
        structure_bias: Current structure ("BULLISH" or "BEARISH")
        swing_highs: List of swing highs
        swing_lows: List of swing lows

    Returns:
        BOS event dictionary or None if no BOS detected
    """
    if not candles or structure_bias == "NEUTRAL":
        return None

    current_price = _to_num(candles[-1]["c"])

    if structure_bias == "BULLISH" and swing_highs:
        # Check if price broke above most recent swing high
        most_recent_high = swing_highs[-1]
        if current_price > _to_num(most_recent_high["price"]):
            return {
                "type": "bullish_bos",
                "level": _to_num(most_recent_high["price"]),
                "current_price": current_price,
                "timestamp": candles[-1]["t"],
            }

    elif structure_bias == "BEARISH" and swing_lows:
        # Check if price broke below most recent swing low
        most_recent_low = swing_lows[-1]
        if current_price < _to_num(most_recent_low["price"]):
            return {
                "type": "bearish_bos",
                "level": _to_num(most_recent_low["price"]),
                "current_price": current_price,
                "timestamp": candles[-1]["t"],
            }

    return None


def detect_change_of_character(
    candles: List[Dict[str, Any]],
    structure_bias: StructureBias,
    swing_highs: List[Dict[str, Any]],
    swing_lows: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Detect Change of Character (CHoCH) events.

    CHoCH = Price breaks a swing point AGAINST the prevailing trend.
    - In bullish trend: Price breaks below a recent swing low (bearish CHoCH)
    - In bearish trend: Price breaks above a recent swing high (bullish CHoCH)

    This signals potential trend reversal or structure weakening.

    Args:
        candles: Recent candle data
        structure_bias: Current structure
        swing_highs: List of swing highs
        swing_lows: List of swing lows

    Returns:
        CHoCH event dictionary or None if no CHoCH detected
    """
    if not candles or structure_bias == "NEUTRAL":
        return None

    current_price = _to_num(candles[-1]["c"])

    if structure_bias == "BULLISH" and swing_lows:
        # In bullish structure, breaking below swing low = bearish CHoCH
        most_recent_low = swing_lows[-1]
        if current_price < _to_num(most_recent_low["price"]):
            return {
                "type": "bearish_choch",
                "level": _to_num(most_recent_low["price"]),
                "current_price": current_price,
                "timestamp": candles[-1]["t"],
                "warning": "Bullish structure weakening - potential reversal",
            }

    elif structure_bias == "BEARISH" and swing_highs:
        # In bearish structure, breaking above swing high = bullish CHoCH
        most_recent_high = swing_highs[-1]
        if current_price > _to_num(most_recent_high["price"]):
            return {
                "type": "bullish_choch",
                "level": _to_num(most_recent_high["price"]),
                "current_price": current_price,
                "timestamp": candles[-1]["t"],
                "warning": "Bearish structure weakening - potential reversal",
            }

    return None
