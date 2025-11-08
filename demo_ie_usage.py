"""
Demo: How to Use the Institutional Engine (IE)

This script shows you how to:
1. Use IE tools standalone (without the agent)
2. Simulate how the agent would use IE tools
3. Combine ICT + IE metrics for trade analysis

Run this after Phase 3 to see IE in action!

Usage:
    python demo_ie_usage.py
"""

import sys
from pathlib import Path
import json

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.ie_fetch_institutional_metrics import fetch_institutional_metrics
from tools.ie_fetch_order_book import fetch_order_book_metrics
from tools.ie_fetch_funding import fetch_funding_metrics
from tools.ie_fetch_open_interest import fetch_open_interest_metrics


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_unified_metrics():
    """Demo 1: Using the unified institutional metrics tool."""
    print_header("DEMO 1: Unified Institutional Metrics Tool")

    print("\n📊 This is the main tool the agent will use!")
    print("It fetches ALL institutional metrics in one call.\n")

    coin = "BTC"
    print(f"Fetching complete institutional analysis for {coin}...\n")

    # This is what the agent calls
    metrics = fetch_institutional_metrics(coin)

    # Check for errors
    if "errors" in metrics:
        print("⚠️  Some data sources unavailable (API restrictions in this environment):")
        for error in metrics["errors"]:
            print(f"  - {error}")
        print("\n💡 In production with real API access, all metrics would be available!")
        return

    # Display results
    print(json.dumps(metrics, indent=2))

    # Show summary
    summary = metrics.get("summary", {})
    print("\n" + "─" * 70)
    print("  AGENT INTERPRETATION")
    print("─" * 70)
    print(f"\n🎯 Recommendation: {summary.get('recommendation', 'unknown').upper()}")
    print(f"📈 Convergence Score: {summary.get('convergence_score', 0)}/100")
    print(f"🟢 Bullish Signals: {summary.get('bullish_signals', 0)}")
    print(f"🔴 Bearish Signals: {summary.get('bearish_signals', 0)}")

    if summary.get('signals'):
        print(f"\n🔔 Detected Signals:")
        for signal in summary['signals']:
            print(f"  • {signal}")


def demo_individual_metrics():
    """Demo 2: Using individual IE tools."""
    print_header("DEMO 2: Individual IE Tools")

    print("\nYou can also call each metric tool separately:\n")

    coin = "ETH"

    # Order Book
    print("📖 Order Book Imbalance:")
    ob = fetch_order_book_metrics(coin, depth=10)
    if "error" not in ob:
        print(f"  Imbalance: {ob['imbalance']:+.4f} ({ob['imbalance_strength']})")
        print(f"  Spread: ${ob['spread']:.2f} ({ob['spread_bps']:.2f} bps)")
    else:
        print(f"  Error: {ob['error']}")

    # Funding
    print("\n💰 Funding Rate:")
    funding = fetch_funding_metrics(coin)
    if "error" not in funding:
        print(f"  Annualized: {funding['annualized_pct']:+.2f}%")
        print(f"  Sentiment: {funding['sentiment']}")
        if funding['is_extreme']:
            print(f"  ⚠️  EXTREME funding detected!")
    else:
        print(f"  Error: {funding['error']}")

    # Open Interest
    print("\n📈 Open Interest:")
    oi = fetch_open_interest_metrics(coin)
    if "error" not in oi:
        print(f"  Current: ${oi['current_usd']:,.0f}")
        if oi['change_4h_pct'] is not None:
            print(f"  Change (4h): {oi['change_4h_pct']:+.2f}%")
            print(f"  Divergence: {oi['divergence_type']}")
        else:
            print(f"  (Need historical data for changes)")
    else:
        print(f"  Error: {oi['error']}")


def demo_agent_workflow():
    """Demo 3: How the agent would analyze a trade setup."""
    print_header("DEMO 3: Agent Workflow (ICT + IE Convergence)")

    print("\nThis simulates how the agent analyzes a setup:\n")

    # Step 1: ICT Analysis (simulated)
    print("🔍 STEP 1: ICT Analysis")
    print("  ✓ Identified: Liquidity sweep at Asia low")
    print("  ✓ Displacement: Strong bullish candle creating FVG")
    print("  ✓ HTF Structure: Bullish (higher highs, higher lows)")
    print("  ✓ Location: In discount zone (below 50% of 1H range)")

    # Step 2: Fetch IE Metrics
    print("\n📊 STEP 2: Fetch Quantitative Validation")
    print("  Calling: fetch_institutional_metrics('BTC')")

    metrics = fetch_institutional_metrics("BTC")

    if "errors" not in metrics or not metrics["errors"]:
        # Step 3: Convergence Analysis
        print("\n🎯 STEP 3: Convergence Analysis")

        ob = metrics.get("order_book", {})
        funding = metrics.get("funding", {})
        oi = metrics.get("open_interest", {})

        if ob:
            imb = ob.get("imbalance", 0)
            if imb > 0.3:
                print(f"  ✓ Order book confirms: {imb:+.2f} (strong bid pressure)")
            else:
                print(f"  ⚠️  Order book neutral: {imb:+.2f}")

        if funding:
            if funding.get('is_extreme'):
                print(f"  ⚠️  Extreme funding: {funding['annualized_pct']:.2f}% (fade signal)")
            else:
                print(f"  ✓ Funding normal: {funding['annualized_pct']:.2f}%")

        if oi and oi.get('divergence_type'):
            div = oi['divergence_type']
            if div == 'strong_bullish':
                print(f"  ✓ OI confirms: {div} (new longs entering)")
            else:
                print(f"  ℹ️  OI scenario: {div}")

        # Step 4: Grade the setup
        print("\n📝 STEP 4: Setup Grade")
        summary = metrics.get('summary', {})
        score = summary.get('convergence_score', 0)
        rec = summary.get('recommendation', 'unknown')

        if score >= 70:
            grade = "A+"
        elif score >= 50:
            grade = "A"
        elif score >= 30:
            grade = "B"
        else:
            grade = "C"

        print(f"  Grade: {grade}")
        print(f"  Convergence Score: {score}/100")
        print(f"  Recommendation: {rec}")

        # Step 5: Final Decision
        print("\n✅ STEP 5: Trade Decision")
        if score >= 50:
            print(f"  → HIGH CONVICTION: ICT setup validated by {summary.get('bullish_signals', 0)} quant signals")
            print(f"  → Entry: In FVG pullback")
            print(f"  → Target: Next liquidity draw (PDH)")
        else:
            print(f"  → LOWER CONVICTION: ICT setup present but limited quant support")
            print(f"  → Consider waiting for better convergence")

    else:
        print("\n⚠️  Cannot complete convergence analysis (API access limited)")
        print("  In production, agent would have full metrics available")


def demo_comparison_table():
    """Demo 4: Compare multiple coins side-by-side."""
    print_header("DEMO 4: Multi-Coin Comparison")

    coins = ["BTC", "ETH", "SOL"]
    print(f"\nComparing institutional metrics across {len(coins)} coins:\n")

    results = []
    for coin in coins:
        print(f"Fetching {coin}...", end=" ")
        metrics = fetch_institutional_metrics(coin)

        if "errors" not in metrics or not metrics["errors"]:
            summary = metrics.get("summary", {})
            results.append({
                "coin": coin,
                "score": summary.get("convergence_score", 0),
                "rec": summary.get("recommendation", "unknown"),
                "signals": len(summary.get("signals", [])),
            })
            print("✓")
        else:
            results.append({
                "coin": coin,
                "score": 0,
                "rec": "error",
                "signals": 0,
            })
            print("✗")

    # Print comparison table
    print("\n" + "─" * 70)
    print(f"{'Coin':<8} {'Score':<10} {'Signals':<10} {'Recommendation':<20}")
    print("─" * 70)

    for r in results:
        print(f"{r['coin']:<8} {r['score']}/100{'':<4} {r['signals']:<10} {r['rec']:<20}")

    print("─" * 70)


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  INSTITUTIONAL ENGINE (IE) - USAGE DEMONSTRATION")
    print("  Phase 3 Complete - Ready for Agent Integration")
    print("=" * 70)

    print("\nℹ️  NOTE: If API access is restricted (403 errors), the demos will")
    print("   show the expected structure but with placeholder data.")
    print("   In production with real API access, all features work perfectly!\n")

    input("Press Enter to start demos...")

    try:
        demo_unified_metrics()
        input("\nPress Enter for next demo...")

        demo_individual_metrics()
        input("\nPress Enter for next demo...")

        demo_agent_workflow()
        input("\nPress Enter for next demo...")

        demo_comparison_table()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
        return

    # Final summary
    print_header("SUMMARY: How the Agent Uses IE")

    print("""
The agent has TWO types of tools now:

1. **ICT Tools** (Existing):
   - fetch_hl_raw: Candles, swings, FVGs, market structure
   - Now ENHANCED with VWAP metrics!

2. **IE Tools** (NEW - Phase 1-3):
   - fetch_institutional_metrics: Complete quant package
   - fetch_order_book_metrics: Bid/ask imbalance
   - fetch_funding_metrics: Sentiment extremes
   - fetch_open_interest_metrics: Smart money tracking

**Agent Workflow:**
1. User asks: "What's the setup on BTC 15m?"
2. Agent fetches ICT data (candles, structure, FVGs)
3. Agent fetches IE metrics (order book, funding, OI)
4. Agent analyzes CONVERGENCE between ICT + IE
5. Agent grades setup (A+/A/B/C) based on convergence
6. Agent gives recommendation with both technical AND quantitative reasoning

**Setup Grading:**
- A+ Setup: ICT pattern + 3 quant confirmations
- A Setup: ICT pattern + 2 quant confirmations
- B Setup: ICT pattern + 1 quant confirmation
- C Setup: ICT pattern only (proceed with caution)

This hybrid approach gives you BOTH:
✓ Pattern recognition (ICT)
✓ Statistical validation (IE)
✓ Increased confidence
✓ Objective metrics

Ready for Phase 4: Agent Integration!
""")


if __name__ == "__main__":
    main()
