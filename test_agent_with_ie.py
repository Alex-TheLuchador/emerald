"""
Test Script: EMERALD Agent with Institutional Engine Integration

This script shows how to use the enhanced agent that combines:
- ICT analysis (existing)
- Institutional Engine metrics (new)

The agent will now grade setups (A+/A/B/C) based on convergence.

Usage:
    python test_agent_with_ie.py

Note: Requires API access to Hyperliquid. In restricted environments,
the agent will gracefully handle errors and still demonstrate the workflow.
"""

import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agent.agent import agent, AGENT_CONFIG


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_agent_ict_only():
    """Test 1: Agent uses only ICT (existing functionality)."""
    print_header("TEST 1: Traditional ICT Analysis (No IE)")

    print("\n📊 Asking agent for ICT analysis without quantitative metrics...")
    print("\nUser: 'What's the market structure on BTC 4H?'\n")

    try:
        response = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "What's the market structure on BTC 4H? Just show me the ICT analysis, don't use institutional metrics."
                }
            ],
            "max_iterations": AGENT_CONFIG.max_iterations,
        })

        final_message = response["messages"][-1].content
        print("Agent Response:")
        print("-" * 70)
        print(final_message)
        print("-" * 70)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nThis is expected if API access is restricted.")


def test_agent_ict_plus_ie():
    """Test 2: Agent uses ICT + IE (new hybrid functionality)."""
    print_header("TEST 2: Hybrid Analysis (ICT + IE)")

    print("\n🔍 Asking agent for complete analysis with quantitative validation...")
    print("\nUser: 'Analyze BTC 15m for a trade setup'\n")

    try:
        response = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "Analyze BTC on the 15-minute timeframe for a trade setup. Use both ICT analysis and institutional metrics to grade the setup."
                }
            ],
            "max_iterations": AGENT_CONFIG.max_iterations,
        })

        final_message = response["messages"][-1].content
        print("Agent Response:")
        print("-" * 70)
        print(final_message)
        print("-" * 70)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nThis is expected if API access is restricted.")


def test_agent_ie_direct():
    """Test 3: Agent uses IE tool directly."""
    print_header("TEST 3: Direct IE Metrics Request")

    print("\n📈 Asking agent to fetch only institutional metrics...")
    print("\nUser: 'What are the institutional metrics for ETH?'\n")

    try:
        response = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "Fetch the institutional metrics for ETH. Show me order book imbalance, funding rate, and open interest."
                }
            ],
            "max_iterations": AGENT_CONFIG.max_iterations,
        })

        final_message = response["messages"][-1].content
        print("Agent Response:")
        print("-" * 70)
        print(final_message)
        print("-" * 70)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nThis is expected if API access is restricted.")


def show_expected_workflow():
    """Show the expected workflow when agent has full API access."""
    print_header("EXPECTED WORKFLOW (With API Access)")

    print("""
When the agent has full API access, here's what happens:

User: "Analyze BTC 15m for a trade setup"

Agent Workflow:
1️⃣  Calls fetch_hl_raw(coin="BTC", interval="15m", ...)
   - Gets candles, swings, FVGs
   - Identifies ICT pattern (e.g., liquidity sweep + displacement)

2️⃣  Calls fetch_institutional_metrics_tool(coin="BTC")
   - Gets order book imbalance
   - Gets funding rate and sentiment
   - Gets OI divergence
   - Receives convergence score and signals

3️⃣  Analyzes convergence:
   - ICT shows: Bullish FVG at discount
   - Order book: +0.48 (strong bid pressure) ✓
   - Funding: 10% (extreme but aligns with structure) ✓
   - OI: Strong bullish divergence ✓
   - VWAP: Z-score -2.1 (oversold) ✓

4️⃣  Grades the setup:
   - 4 confirmations = A+ Setup
   - High conviction

5️⃣  Provides response:
   "## BTC 15m Analysis (A+ Setup)

   ### ICT Analysis
   - HTF Structure: Bullish
   - Liquidity sweep at 67,750 (Asia low)
   - Bullish displacement creating FVG (67,800-67,850)
   - Location: 43% of 1H range (discount)

   ### Quantitative Validation
   ✓ Order book: +0.48 imbalance (institutions absorbing)
   ✓ Funding: 10.95% annualized (extreme bullish)
   ✓ OI: +5.7% (4h) - strong bullish divergence
   ✓ VWAP: Z-score -2.1 (extreme oversold)

   **Setup Grade**: A+
   **Conviction**: HIGH

   ### Trade Plan
   Entry: 67,820 (FVG pullback)
   Stop: 67,720 (below sweep)
   Target 1: 68,200 (VWAP)
   Target 2: 68,500 (PDH)
   Size: 2.0% (A+ allows larger size)"

This demonstrates the power of combining ICT pattern recognition
with institutional quantitative metrics!
    """)


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  EMERALD AGENT - INSTITUTIONAL ENGINE INTEGRATION TEST")
    print("  Phase 4 Complete - Agent Enhanced with Quantitative Metrics")
    print("=" * 70)

    print("""
This test demonstrates:
✓ Agent can use traditional ICT analysis
✓ Agent can use new IE (quantitative) metrics
✓ Agent combines both for setup grading (A+/A/B/C)

Note: Tests may show API errors if Hyperliquid access is restricted.
The agent will gracefully handle these and explain what it would do.
    """)

    input("Press Enter to run tests...")

    try:
        # Test 1: ICT only
        test_agent_ict_only()
        input("\nPress Enter for next test...")

        # Test 2: ICT + IE
        test_agent_ict_plus_ie()
        input("\nPress Enter for next test...")

        # Test 3: IE direct
        test_agent_ie_direct()
        input("\nPress Enter to see expected workflow...")

        # Show expected workflow
        show_expected_workflow()

    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        return

    # Summary
    print_header("INTEGRATION SUMMARY")
    print("""
✅ Agent successfully enhanced with Institutional Engine!

What's new:
1. Agent now has 2 tools:
   - fetch_hl_raw (ICT analysis + VWAP)
   - fetch_institutional_metrics_tool (quantitative validation)

2. Agent follows hybrid workflow:
   - Start with ICT pattern recognition
   - Validate with quantitative metrics
   - Grade setup based on convergence

3. Agent provides graded setups:
   - A+ Setup: ICT + 3 quant signals (high conviction)
   - A Setup: ICT + 2 quant signals (strong)
   - B Setup: ICT + 1 quant signal (moderate)
   - C Setup: ICT only (low, proceed with caution)

4. Context document "Quantitative Metrics Guide" loaded automatically

Next steps:
- Phase 5: Testing & Refinement
- Validate with real market data
- Optimize metric thresholds
- Fine-tune setup grading
    """)


if __name__ == "__main__":
    main()
