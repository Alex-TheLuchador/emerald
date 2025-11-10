"""
Higher Timeframe (HTF) Alignment Checker

Critical principle: Only trade when higher timeframes align.

Required alignment: Daily + 4H + 1H must all show same structure
Optional: Weekly alignment is bonus but not required

This prevents counter-trend trades and ensures you're trading WITH the market.
"""

from typing import Dict, Any, List
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ICT_CONFIG
from ict.swing_detector import detect_all_swings
from ict.structure_analyzer import determine_structure_bias, StructureBias


def check_htf_alignment(
    multi_tf_candles: Dict[str, List[Dict[str, Any]]],
    required_timeframes: List[str] = None,
) -> Dict[str, Any]:
    """
    Check if multiple timeframes show aligned structure.

    Args:
        multi_tf_candles: Dictionary mapping timeframes to candle data
            Example: {
                "1w": [candles],
                "1d": [candles],
                "4h": [candles],
                "1h": [candles]
            }
        required_timeframes: List of timeframes that MUST align (default: from config)

    Returns:
        Dictionary containing:
        - aligned: True if all required TFs show same bias
        - bias: "BULLISH", "BEARISH", or None if not aligned
        - structures: Dict mapping each TF to its structure result
        - conflicts: List of conflicting timeframes (if any)
        - confidence: 0.0-1.0 (higher if weekly also aligns)

    Example:
        >>> result = check_htf_alignment({
        >>>     "1d": daily_candles,
        >>>     "4h": four_hour_candles,
        >>>     "1h": one_hour_candles
        >>> })
        >>> if result["aligned"] and result["bias"] == "BULLISH":
        >>>     # Safe to look for long setups
    """
    if required_timeframes is None:
        required_timeframes = ICT_CONFIG.htf_required_timeframes

    # Validate structure for each timeframe
    structures = {}
    for tf, candles in multi_tf_candles.items():
        structures[tf] = validate_timeframe_structure(candles, tf)

    # Check if required timeframes exist
    missing_tfs = [tf for tf in required_timeframes if tf not in structures]
    if missing_tfs:
        return {
            "aligned": False,
            "bias": None,
            "structures": structures,
            "conflicts": [],
            "confidence": 0.0,
            "error": f"Missing required timeframes: {', '.join(missing_tfs)}"
        }

    # Get biases from required timeframes
    required_biases = [structures[tf]["bias"] for tf in required_timeframes]

    # Check for NEUTRAL bias (invalid for trading)
    if "NEUTRAL" in required_biases:
        neutral_tfs = [tf for tf in required_timeframes if structures[tf]["bias"] == "NEUTRAL"]
        return {
            "aligned": False,
            "bias": None,
            "structures": structures,
            "conflicts": neutral_tfs,
            "confidence": 0.0,
            "error": f"Neutral structure on: {', '.join(neutral_tfs)}"
        }

    # Check if all required timeframes agree
    first_bias = required_biases[0]
    all_agree = all(bias == first_bias for bias in required_biases)

    if not all_agree:
        # Find conflicts
        bullish_tfs = [tf for tf in required_timeframes if structures[tf]["bias"] == "BULLISH"]
        bearish_tfs = [tf for tf in required_timeframes if structures[tf]["bias"] == "BEARISH"]
        conflicts = bullish_tfs if len(bearish_tfs) > len(bullish_tfs) else bearish_tfs

        return {
            "aligned": False,
            "bias": None,
            "structures": structures,
            "conflicts": conflicts,
            "confidence": 0.0,
            "error": f"HTF conflict: {', '.join(bullish_tfs)} bullish vs {', '.join(bearish_tfs)} bearish"
        }

    # All required timeframes aligned!
    # Calculate confidence (bonus if optional TFs also align)
    aligned_count = len(required_timeframes)
    total_count = len(required_timeframes)

    # Check optional timeframes for bonus confidence
    optional_tfs = ICT_CONFIG.htf_optional_timeframes
    for tf in optional_tfs:
        if tf in structures and structures[tf]["bias"] == first_bias:
            aligned_count += 1
        if tf in structures:
            total_count += 1

    confidence = aligned_count / total_count if total_count > 0 else 0.0

    # Get average structure confidence from aligned timeframes
    avg_structure_confidence = sum(
        structures[tf]["confidence"]
        for tf in required_timeframes
    ) / len(required_timeframes)

    # Combined confidence
    final_confidence = (confidence + avg_structure_confidence) / 2.0

    return {
        "aligned": True,
        "bias": first_bias,
        "structures": structures,
        "conflicts": [],
        "confidence": round(final_confidence, 2),
        "aligned_timeframes": [tf for tf in multi_tf_candles.keys() if structures.get(tf, {}).get("bias") == first_bias],
        "required_tfs_aligned": required_timeframes,
    }


def validate_timeframe_structure(
    candles: List[Dict[str, Any]],
    timeframe: str,
) -> Dict[str, Any]:
    """
    Validate structure for a single timeframe.

    Helper function that detects swings and determines structure for one TF.

    Args:
        candles: Candle data for this timeframe
        timeframe: Timeframe string ("1d", "4h", etc.)

    Returns:
        Structure result for this single timeframe:
        {
            "timeframe": "1h",
            "bias": "BULLISH",
            "pattern": "HH/HL",
            "confidence": 0.85,
            "swing_highs_count": 5,
            "swing_lows_count": 5,
            ...
        }
    """
    if not candles or len(candles) < 5:
        return {
            "timeframe": timeframe,
            "bias": "NEUTRAL",
            "pattern": "RANGING",
            "confidence": 0.0,
            "error": f"Insufficient candles for {timeframe} (need 5+, got {len(candles)})"
        }

    # Detect swings
    swings = detect_all_swings(candles, significant_only=False)
    swing_highs = swings["swing_highs"]
    swing_lows = swings["swing_lows"]

    # Determine structure bias
    structure = determine_structure_bias(swing_highs, swing_lows)

    # Add timeframe info
    structure["timeframe"] = timeframe
    structure["swing_highs_count"] = len(swing_highs)
    structure["swing_lows_count"] = len(swing_lows)
    structure["candles_analyzed"] = len(candles)

    return structure
