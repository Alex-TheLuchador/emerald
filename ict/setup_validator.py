"""
ICT Setup Validator

Master validation logic that orchestrates all ICT checks to determine
if a valid trading setup exists.

Validates:
1. HTF alignment (Daily/4H/1H)
2. Dealing range clarity
3. Price in discount (longs) or premium (shorts)
4. FVG presence at entry zone (optional confluence)
5. Clear liquidity draw identified
"""

from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ICT_CONFIG
from ict.htf_alignment import check_htf_alignment
from ict.swing_detector import detect_all_swings
from ict.dealing_range import calculate_dealing_range, is_price_in_discount, is_price_in_premium
from ict.liquidity_pools import get_all_liquidity_pools


def _to_num(x: Any) -> float:
    """Convert value to float, return nan if conversion fails."""
    try:
        return float(x)
    except Exception:
        return float("nan")


def validate_bullish_setup(
    multi_tf_candles: Dict[str, List[Dict[str, Any]]],
    current_price: float,
) -> Dict[str, Any]:
    """
    Validate a bullish (long) ICT setup.

    Requirements for valid bullish setup:
    1. HTF alignment: Daily/4H/1H all bullish
    2. Dealing range identified
    3. Current price in discount zone (<50% of dealing range)
    4. Clear target identified (dealing range high or next liquidity pool)

    Args:
        multi_tf_candles: Candle data for all timeframes
        current_price: Current market price

    Returns:
        Setup validation result with entry, stop, targets, risk/reward
    """
    # Check HTF alignment
    htf = check_htf_alignment(multi_tf_candles)

    if not htf["aligned"]:
        return {
            "valid": False,
            "direction": None,
            "reason": "HTF not aligned",
            "htf_result": htf,
        }

    if htf["bias"] != "BULLISH":
        return {
            "valid": False,
            "direction": None,
            "reason": f"HTF bias is {htf['bias']}, not BULLISH",
            "htf_result": htf,
        }

    # Get 1H candles for dealing range calculation
    one_hour_candles = multi_tf_candles.get("1h", [])
    if not one_hour_candles:
        return {
            "valid": False,
            "direction": "LONG",
            "reason": "No 1H candles for dealing range calculation",
        }

    # Detect swings on 1H
    swings = detect_all_swings(one_hour_candles)
    swing_highs = swings["swing_highs"]
    swing_lows = swings["swing_lows"]

    # Calculate dealing range
    dealing_range = calculate_dealing_range(
        one_hour_candles,
        swing_highs,
        swing_lows,
        current_price
    )

    if not dealing_range["valid"]:
        return {
            "valid": False,
            "direction": "LONG",
            "reason": "No clear dealing range",
            "dealing_range": dealing_range,
        }

    # Check if price in discount
    if not is_price_in_discount(dealing_range):
        return {
            "valid": False,
            "direction": "LONG",
            "reason": f"Price in {dealing_range['zone']}, not discount (need <{ICT_CONFIG.discount_threshold - ICT_CONFIG.mid_range_buffer})",
            "dealing_range": dealing_range,
        }

    # Calculate liquidity pools for target identification
    liquidity_pools = get_all_liquidity_pools(
        one_hour_candles,
        swing_highs,
        swing_lows,
        current_price
    )

    # Determine target (dealing range high or nearest liquidity above)
    target_1 = dealing_range["range_high"]
    if liquidity_pools["nearest_above"]:
        # Use nearest liquidity if it's beyond dealing range high
        if liquidity_pools["nearest_above"] > target_1:
            target_2 = liquidity_pools["nearest_above"]
        else:
            target_2 = liquidity_pools["pdh"] if liquidity_pools["pdh"] and liquidity_pools["pdh"] > target_1 else None
    else:
        target_2 = None

    # Calculate stop loss (1:1 R:R)
    reward = target_1 - current_price
    stop_loss = current_price - (reward * ICT_CONFIG.default_risk_reward)

    # Calculate R:R
    risk = current_price - stop_loss
    risk_reward_ratio = reward / risk if risk > 0 else 0

    return {
        "valid": True,
        "direction": "LONG",
        "entry_price": round(current_price, 2),
        "stop_loss": round(stop_loss, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2) if target_2 else None,
        "risk_reward": f"{risk_reward_ratio:.1f}:1",
        "dealing_range": dealing_range,
        "liquidity_pools": liquidity_pools,
        "htf_alignment": htf,
        "invalidation": f"Price breaks below ${dealing_range['range_low']} (dealing range low)",
    }


def validate_bearish_setup(
    multi_tf_candles: Dict[str, List[Dict[str, Any]]],
    current_price: float,
) -> Dict[str, Any]:
    """
    Validate a bearish (short) ICT setup.

    Requirements for valid bearish setup:
    1. HTF alignment: Daily/4H/1H all bearish
    2. Dealing range identified
    3. Current price in premium zone (>50% of dealing range)
    4. Clear target identified (dealing range low or next liquidity pool)

    Args:
        multi_tf_candles: Candle data for all timeframes
        current_price: Current market price

    Returns:
        Setup validation result (same structure as validate_bullish_setup)
    """
    # Check HTF alignment
    htf = check_htf_alignment(multi_tf_candles)

    if not htf["aligned"]:
        return {
            "valid": False,
            "direction": None,
            "reason": "HTF not aligned",
            "htf_result": htf,
        }

    if htf["bias"] != "BEARISH":
        return {
            "valid": False,
            "direction": None,
            "reason": f"HTF bias is {htf['bias']}, not BEARISH",
            "htf_result": htf,
        }

    # Get 1H candles for dealing range calculation
    one_hour_candles = multi_tf_candles.get("1h", [])
    if not one_hour_candles:
        return {
            "valid": False,
            "direction": "SHORT",
            "reason": "No 1H candles for dealing range calculation",
        }

    # Detect swings on 1H
    swings = detect_all_swings(one_hour_candles)
    swing_highs = swings["swing_highs"]
    swing_lows = swings["swing_lows"]

    # Calculate dealing range
    dealing_range = calculate_dealing_range(
        one_hour_candles,
        swing_highs,
        swing_lows,
        current_price
    )

    if not dealing_range["valid"]:
        return {
            "valid": False,
            "direction": "SHORT",
            "reason": "No clear dealing range",
            "dealing_range": dealing_range,
        }

    # Check if price in premium
    if not is_price_in_premium(dealing_range):
        return {
            "valid": False,
            "direction": "SHORT",
            "reason": f"Price in {dealing_range['zone']}, not premium (need >{ICT_CONFIG.premium_threshold + ICT_CONFIG.mid_range_buffer})",
            "dealing_range": dealing_range,
        }

    # Calculate liquidity pools for target identification
    liquidity_pools = get_all_liquidity_pools(
        one_hour_candles,
        swing_highs,
        swing_lows,
        current_price
    )

    # Determine target (dealing range low or nearest liquidity below)
    target_1 = dealing_range["range_low"]
    if liquidity_pools["nearest_below"]:
        # Use nearest liquidity if it's below dealing range low
        if liquidity_pools["nearest_below"] < target_1:
            target_2 = liquidity_pools["nearest_below"]
        else:
            target_2 = liquidity_pools["pdl"] if liquidity_pools["pdl"] and liquidity_pools["pdl"] < target_1 else None
    else:
        target_2 = None

    # Calculate stop loss (1:1 R:R)
    reward = current_price - target_1
    stop_loss = current_price + (reward * ICT_CONFIG.default_risk_reward)

    # Calculate R:R
    risk = stop_loss - current_price
    risk_reward_ratio = reward / risk if risk > 0 else 0

    return {
        "valid": True,
        "direction": "SHORT",
        "entry_price": round(current_price, 2),
        "stop_loss": round(stop_loss, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2) if target_2 else None,
        "risk_reward": f"{risk_reward_ratio:.1f}:1",
        "dealing_range": dealing_range,
        "liquidity_pools": liquidity_pools,
        "htf_alignment": htf,
        "invalidation": f"Price breaks above ${dealing_range['range_high']} (dealing range high)",
    }


def validate_ict_setup(
    multi_tf_candles: Dict[str, List[Dict[str, Any]]],
    current_price: float,
) -> Dict[str, Any]:
    """
    Master ICT setup validator - automatically detects direction.

    This is the main entry point for ICT setup validation.
    Determines bias from HTF alignment, then validates appropriate setup type.

    Args:
        multi_tf_candles: Candle data for all timeframes
        current_price: Current market price

    Returns:
        Complete setup validation result or error dict if no valid setup
    """
    # Check HTF alignment first
    htf = check_htf_alignment(multi_tf_candles)

    if not htf["aligned"]:
        return {
            "valid": False,
            "direction": None,
            "reason": "HTF not aligned",
            "htf_result": htf,
            "error": htf.get("error", "Timeframes showing conflicting structure"),
        }

    # Based on bias, validate appropriate setup
    if htf["bias"] == "BULLISH":
        return validate_bullish_setup(multi_tf_candles, current_price)
    elif htf["bias"] == "BEARISH":
        return validate_bearish_setup(multi_tf_candles, current_price)
    else:
        return {
            "valid": False,
            "direction": None,
            "reason": "HTF bias is NEUTRAL - no clear structure",
            "htf_result": htf,
        }


def calculate_position_size(
    account_balance: float,
    risk_pct: float,
    entry_price: float,
    stop_loss: float,
    leverage: float = 1.0,
) -> Dict[str, Any]:
    """
    Calculate position size based on risk parameters.

    Args:
        account_balance: Total account balance
        risk_pct: Risk per trade as percentage (e.g., 1.0 for 1%)
        entry_price: Planned entry price
        stop_loss: Stop loss price
        leverage: Leverage multiplier (default: 1.0 for no leverage)

    Returns:
        Position sizing result:
        {
            "position_size": 0.15,  # Contracts/units
            "risk_amount": 100.0,   # Dollar risk
            "risk_per_unit": 666.67,
            "notional_value": 10000.0,
            "position_size_usd": 10000.0
        }
    """
    risk_amount = account_balance * (risk_pct / 100.0)
    risk_per_unit = abs(entry_price - stop_loss)

    if risk_per_unit == 0:
        return {
            "error": "Invalid stop loss - same as entry price",
            "position_size": 0,
            "risk_amount": 0,
            "risk_per_unit": 0,
            "notional_value": 0,
            "position_size_usd": 0,
        }

    position_size = (risk_amount / risk_per_unit) * leverage
    notional_value = position_size * entry_price
    position_size_usd = notional_value

    return {
        "position_size": round(position_size, 4),
        "risk_amount": round(risk_amount, 2),
        "risk_per_unit": round(risk_per_unit, 2),
        "notional_value": round(notional_value, 2),
        "position_size_usd": round(position_size_usd, 2),
        "leverage": leverage,
    }
