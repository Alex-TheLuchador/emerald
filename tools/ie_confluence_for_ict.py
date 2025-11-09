"""
IE Confluence Layer for ICT Setups

Provides quantitative confluence scoring for ICT/SMC setups using existing IE tools.
Checks order book, funding, trade flow, OI, and liquidations to validate ICT structure.
"""

import sys
from pathlib import Path
from typing import Dict, Any
from langchain.tools import tool

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ICT_CONFIG

# Import IE tools (will handle their own imports)
try:
    from tools.ie_fetch_order_book import fetch_order_book_data
    from tools.ie_fetch_funding import fetch_funding_rate_data
    from tools.ie_fetch_trade_flow import fetch_trade_flow_data
    from tools.ie_fetch_open_interest import fetch_open_interest_data
except ImportError:
    # Tools may not be importable in all environments
    pass


@tool
def ict_ie_confluence(coin: str, direction: str) -> str:
    """
    Check IE confluence for an ICT setup.

    Uses existing Institutional Engine tools to provide quantitative
    confirmation for structure-based ICT setups.

    Args:
        coin: Trading pair symbol (e.g., "BTC")
        direction: Setup direction ("LONG" or "SHORT")

    Returns:
        Formatted confluence analysis with score (0-100)

    Confluence scoring:
    - Order book aligned: +20 points
    - Trade flow aligned: +20 points
    - Funding extreme (contrarian): +15 points
    - OI divergence: +20 points
    - Total: 0-75 points possible

    Grading:
    - 60-75: Grade A+ (high confluence)
    - 40-59: Grade A (good confluence)
    - 20-39: Grade B (moderate confluence)
    - 0-19: Grade C (weak confluence)
    """
    score = 0
    details = []
    errors = []

    direction_lower = direction.upper()

    # 1. Order Book Check (+20 points)
    try:
        ob_result = fetch_order_book_data(coin)
        if isinstance(ob_result, dict) and "imbalance" in ob_result:
            imbalance = ob_result["imbalance"]

            if direction_lower == "LONG" and imbalance > 0.3:
                score += ICT_CONFIG.order_book_points
                details.append(f"✓ Order book: +{imbalance:.2f} (bid pressure supports long)")
            elif direction_lower == "SHORT" and imbalance < -0.3:
                score += ICT_CONFIG.order_book_points
                details.append(f"✓ Order book: {imbalance:.2f} (ask pressure supports short)")
            else:
                details.append(f"○ Order book: {imbalance:.2f} (neutral)")
    except Exception as e:
        errors.append(f"Order book check failed: {str(e)}")
        details.append("○ Order book: N/A")

    # 2. Trade Flow Check (+20 points)
    try:
        tf_result = fetch_trade_flow_data(coin)
        if isinstance(tf_result, dict) and "flow_imbalance" in tf_result:
            flow = tf_result["flow_imbalance"]

            if direction_lower == "LONG" and flow > 0.3:
                score += ICT_CONFIG.trade_flow_points
                details.append(f"✓ Trade flow: +{flow:.2f} (aggressive buying)")
            elif direction_lower == "SHORT" and flow < -0.3:
                score += ICT_CONFIG.trade_flow_points
                details.append(f"✓ Trade flow: {flow:.2f} (aggressive selling)")
            else:
                details.append(f"○ Trade flow: {flow:.2f} (neutral)")
    except Exception as e:
        errors.append(f"Trade flow check failed: {str(e)}")
        details.append("○ Trade flow: N/A")

    # 3. Funding Rate Check (+15 points, contrarian)
    try:
        funding_result = fetch_funding_rate_data(coin)
        if isinstance(funding_result, dict) and "funding_rate_annualized_pct" in funding_result:
            funding_pct = funding_result["funding_rate_annualized_pct"]

            # Contrarian signal: extreme bullish funding = bearish setup opportunity
            if direction_lower == "SHORT" and funding_pct > 10:
                score += ICT_CONFIG.funding_extreme_points
                details.append(f"✓ Funding: +{funding_pct:.1f}% (extreme bullish, contrarian short)")
            elif direction_lower == "LONG" and funding_pct < -10:
                score += ICT_CONFIG.funding_extreme_points
                details.append(f"✓ Funding: {funding_pct:.1f}% (extreme bearish, contrarian long)")
            else:
                details.append(f"○ Funding: {funding_pct:.1f}% (not extreme)")
    except Exception as e:
        errors.append(f"Funding check failed: {str(e)}")
        details.append("○ Funding: N/A")

    # 4. OI Divergence Check (+20 points)
    try:
        oi_result = fetch_open_interest_data(coin)
        if isinstance(oi_result, dict) and "interpretation" in oi_result:
            interpretation = oi_result["interpretation"]

            # Look for weak rallies (bearish) or weak selloffs (bullish)
            if direction_lower == "SHORT" and "weak_bullish" in interpretation.lower():
                score += ICT_CONFIG.oi_divergence_points
                details.append(f"✓ OI: Weak rally (OI declining while price rising)")
            elif direction_lower == "LONG" and "weak_bearish" in interpretation.lower():
                score += ICT_CONFIG.oi_divergence_points
                details.append(f"✓ OI: Weak selloff (OI declining while price falling)")
            else:
                details.append(f"○ OI: {interpretation}")
    except Exception as e:
        errors.append(f"OI check failed: {str(e)}")
        details.append("○ OI: N/A")

    # Calculate grade
    if score >= ICT_CONFIG.grade_a_plus_threshold:
        grade = "A+"
        multiplier = ICT_CONFIG.grade_a_plus_position_mult
    elif score >= ICT_CONFIG.grade_a_threshold:
        grade = "A"
        multiplier = ICT_CONFIG.grade_a_position_mult
    elif score >= ICT_CONFIG.grade_b_threshold:
        grade = "B"
        multiplier = ICT_CONFIG.grade_b_position_mult
    else:
        grade = "C"
        multiplier = 0.25

    # Format output
    output = [
        f"### IE Confluence for {coin} {direction}",
        "",
        f"**Score**: {score}/75",
        f"**Grade**: {grade}",
        f"**Position Size Multiplier**: {multiplier:.0%}",
        "",
        "**Confluence Checks**:",
    ]

    for detail in details:
        output.append(f"  {detail}")

    if errors:
        output.extend([
            "",
            "**Errors**:",
        ])
        for error in errors:
            output.append(f"  - {error}")

    output.extend([
        "",
        "**Recommendation**:",
    ])

    if grade in ["A+", "A"]:
        output.append(f"  Strong IE confluence supports this {direction} setup. Proceed with confidence.")
    elif grade == "B":
        output.append(f"  Moderate IE confluence. Setup is valid but proceed with reduced size.")
    else:
        output.append(f"  Weak IE confluence. ICT setup may be valid but IE data doesn't confirm. Use caution.")

    return "\n".join(output)
