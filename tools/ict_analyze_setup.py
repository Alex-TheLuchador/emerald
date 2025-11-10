"""
ICT/SMC Setup Analysis Tool

Master tool for analyzing ICT/SMC trading setups.
Fetches multi-timeframe data and performs complete ICT analysis.

This is the primary tool the agent uses for ICT strategy analysis.
"""

import sys
from pathlib import Path
from typing import Dict, Any
from langchain.tools import tool

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.tool_fetch_hl_raw import fetch_hl_raw, parse_raw_keep_ohlc
from ict.setup_validator import validate_ict_setup, calculate_position_size
from config.settings import ICT_CONFIG


def fetch_multi_timeframe_candles(coin: str) -> Dict[str, Any]:
    """
    Fetch candles for all required timeframes for ICT analysis.

    Args:
        coin: Trading pair symbol (e.g., "BTC")

    Returns:
        Dictionary mapping timeframes to candle lists:
        {
            "1d": [candles],
            "4h": [candles],
            "1h": [candles],
            "5m": [candles]
        }
    """
    timeframe_config = {
        "1d": {"hours": 720, "limit": 30},   # 30 days
        "4h": {"hours": 192, "limit": 50},   # 8 days
        "1h": {"hours": 100, "limit": 100},  # 4 days
        "5m": {"hours": 12, "limit": 150},   # 12 hours
    }

    multi_tf_candles = {}
    errors = []

    for tf, config in timeframe_config.items():
        try:
            status, result = fetch_hl_raw(
                coin=coin,
                interval=tf,
                hours=config["hours"],
                limit=config["limit"],
                convert=False,
            )

            if status == 200 and result.get("raw"):
                candles = parse_raw_keep_ohlc(result["raw"])
                multi_tf_candles[tf] = candles
            else:
                error_msg = result.get("error", f"HTTP {status}")
                errors.append(f"{tf}: {error_msg}")

        except Exception as e:
            errors.append(f"{tf}: {str(e)}")

    return {
        "candles": multi_tf_candles,
        "errors": errors if errors else None,
    }


@tool
def ict_analyze_setup(coin: str, account_balance: float = 10000.0) -> str:
    """
    Analyze ICT/SMC trading setup for a coin.

    Fetches multi-timeframe candle data and performs complete ICT analysis:
    - HTF alignment (Daily/4H/1H)
    - Structure bias (HH/HL vs LL/LH)
    - Dealing range identification
    - Discount/premium zone detection
    - Liquidity pool mapping
    - Setup validation
    - Position sizing recommendation

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH", "SOL")
        account_balance: Account balance for position sizing (default: $10,000)

    Returns:
        Detailed ICT setup analysis as formatted string.

    Example:
        >>> result = ict_analyze_setup("BTC", account_balance=10000)
        >>> print(result)
        # Returns formatted analysis with setup validity, entry/exit levels, etc.
    """
    # Fetch multi-timeframe candles
    fetch_result = fetch_multi_timeframe_candles(coin)
    multi_tf_candles = fetch_result["candles"]
    fetch_errors = fetch_result["errors"]

    if fetch_errors:
        return f"❌ Error fetching candles:\n" + "\n".join(f"  - {err}" for err in fetch_errors)

    if not multi_tf_candles:
        return f"❌ No candle data available for {coin}"

    # Get current price from latest 5m candle
    if "5m" in multi_tf_candles and multi_tf_candles["5m"]:
        current_price = float(multi_tf_candles["5m"][-1]["c"])
    elif "1h" in multi_tf_candles and multi_tf_candles["1h"]:
        current_price = float(multi_tf_candles["1h"][-1]["c"])
    else:
        return f"❌ No candles available to determine current price"

    # Validate ICT setup
    setup = validate_ict_setup(multi_tf_candles, current_price)

    # Format output
    if not setup["valid"]:
        # Invalid setup
        output = [
            f"❌ **{coin} - NO VALID ICT SETUP**",
            "",
            f"**Reason**: {setup['reason']}",
            f"**Current Price**: ${current_price:,.2f}",
            "",
        ]

        # Show HTF structure details if available
        if "htf_result" in setup:
            htf = setup["htf_result"]
            output.append("**HTF Structure Analysis**:")
            if htf.get("structures"):
                for tf in ["1d", "4h", "1h"]:
                    if tf in htf["structures"]:
                        s = htf["structures"][tf]
                        bias_icon = "🟢" if s["bias"] == "BULLISH" else "🔴" if s["bias"] == "BEARISH" else "⚪"
                        output.append(f"  {bias_icon} {tf.upper()}: {s['bias']} ({s['pattern']}, confidence: {s['confidence']})")

        return "\n".join(output)

    # Valid setup!
    direction_icon = "🟢" if setup["direction"] == "LONG" else "🔴"

    output = [
        f"{direction_icon} **{coin} - VALID ICT SETUP ({setup['direction']})**",
        "",
        "### HTF Alignment",
        f"**Bias**: {setup['htf_alignment']['bias']}",
        f"**Confidence**: {setup['htf_alignment']['confidence']}",
        f"**Aligned TFs**: {', '.join(setup['htf_alignment']['required_tfs_aligned'])}",
        "",
        "### Dealing Range (1H)",
        f"**Range High**: ${setup['dealing_range']['range_high']:,.2f}",
        f"**Range Low**: ${setup['dealing_range']['range_low']:,.2f}",
        f"**Midpoint**: ${setup['dealing_range']['midpoint']:,.2f}",
        f"**Current Price**: ${current_price:,.2f} ({setup['dealing_range']['current_percent']:.1%} of range)",
        f"**Zone**: {setup['dealing_range']['zone'].upper()}",
        "",
        "### Entry Setup",
        f"**Direction**: {setup['direction']}",
        f"**Entry**: ${setup['entry_price']:,.2f}",
        f"**Stop Loss**: ${setup['stop_loss']:,.2f}",
        f"**Target 1**: ${setup['target_1']:,.2f}",
    ]

    if setup.get("target_2"):
        output.append(f"**Target 2**: ${setup['target_2']:,.2f}")

    output.append(f"**Risk:Reward**: {setup['risk_reward']}")
    output.append(f"**Invalidation**: {setup['invalidation']}")
    output.append("")

    # Position sizing
    position = calculate_position_size(
        account_balance=account_balance,
        risk_pct=ICT_CONFIG.base_position_risk_pct,
        entry_price=setup['entry_price'],
        stop_loss=setup['stop_loss'],
    )

    if "error" not in position:
        output.extend([
            "### Position Sizing",
            f"**Account Balance**: ${account_balance:,.2f}",
            f"**Risk Amount**: ${position['risk_amount']:,.2f} ({ICT_CONFIG.base_position_risk_pct}%)",
            f"**Position Size**: {position['position_size']:.4f} {coin}",
            f"**Notional Value**: ${position['notional_value']:,.2f}",
            "",
        ])

    # Liquidity pools
    if setup.get("liquidity_pools"):
        lp = setup["liquidity_pools"]
        output.extend([
            "### Liquidity Pools",
        ])
        if lp.get("pdh"):
            output.append(f"**PDH**: ${lp['pdh']:,.2f}")
        if lp.get("pdl"):
            output.append(f"**PDL**: ${lp['pdl']:,.2f}")
        if lp.get("nearest_above"):
            output.append(f"**Nearest Above**: ${lp['nearest_above']:,.2f}")
        if lp.get("nearest_below"):
            output.append(f"**Nearest Below**: ${lp['nearest_below']:,.2f}")

    return "\n".join(output)


if __name__ == "__main__":
    # Test the tool
    import json
    result = ict_analyze_setup("BTC", account_balance=10000)
    print(result)
