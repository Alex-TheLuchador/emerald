"""
Streamlit UI for the Strategy Monitor
"""
import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional

from api_client import HyperliquidClient
from metrics import MetricsCalculator
from signal_generator import SignalGenerator
from storage import OIHistoryStorage
from config import COINS, REFRESH_INTERVAL_SECONDS, OI_LOOKBACK_HOURS


# Page config
st.set_page_config(
    page_title="Strategy Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def get_components():
    """Initialize components (cached)"""
    return {
        'calculator': MetricsCalculator(),
        'generator': SignalGenerator(),
        'storage': OIHistoryStorage()
    }


async def fetch_data(coin: str) -> Optional[Dict[str, Any]]:
    """Fetch all data for a coin"""
    try:
        async with HyperliquidClient() as client:
            return await client.get_all_data(coin)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None


def get_historical_oi(storage: OIHistoryStorage, coin: str) -> Optional[Dict[str, float]]:
    """Get historical OI snapshot"""
    try:
        return storage.get_snapshot(coin, hours_ago=OI_LOOKBACK_HOURS)
    except Exception as e:
        st.warning(f"No historical OI data: {e}")
        return None


def save_current_oi(storage: OIHistoryStorage, coin: str, oi: float, price: float):
    """Save current OI snapshot"""
    try:
        storage.save_snapshot(coin, oi, price)
    except Exception as e:
        st.error(f"Error saving OI: {e}")


def render_signal_header(signal: Dict[str, Any]):
    """Render the main signal at the top"""
    action = signal['action']
    score = signal['convergence_score']
    confidence = signal['confidence']

    # Color coding
    if action == 'LONG':
        color = '🟢'
        bg_color = '#1a4d2e'
        action_text = 'LONG'
    elif action == 'SHORT':
        color = '🔴'
        bg_color = '#4d1a1a'
        action_text = 'SHORT'
    else:
        color = '⚪'
        bg_color = "#d3d3d3"
        action_text = 'SKIP (No Setup)'

    st.markdown(f"""
    <div style='padding: 20px; background-color: {bg_color}; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='text-align: center; margin: 0;'>{color} {action_text}</h1>
        <h3 style='text-align: center; margin: 10px 0;'>
            Score: {score}/100 | Confidence: {confidence} |
            Signals: {signal['aligned_signals']} aligned
        </h3>
    </div>
    """, unsafe_allow_html=True)

    # Explanation expander
    with st.expander("ℹ️ What does this mean?", expanded=False):
        if action == 'LONG':
            st.success("""
            **LONG Signal Detected**

            Multiple metrics are showing bullish convergence:
            - {bull} bullish signals vs {bear} bearish signals
            - Convergence score: {score}/100 (need ≥70)
            - Confidence: {conf}

            This suggests buying pressure is building. Consider entering a long position.
            """.format(bull=signal['bullish_signals'], bear=signal['bearish_signals'],
                      score=score, conf=confidence))
        elif action == 'SHORT':
            st.error("""
            **SHORT Signal Detected**

            Multiple metrics are showing bearish convergence:
            - {bear} bearish signals vs {bull} bullish signals
            - Convergence score: {score}/100 (need ≥70)
            - Confidence: {conf}

            This suggests selling pressure is building. Consider entering a short position.
            """.format(bull=signal['bullish_signals'], bear=signal['bearish_signals'],
                      score=score, conf=confidence))
        else:
            st.info("""
            **SKIP - No Clear Setup**

            Reasons to skip:
            - Not enough aligned signals ({aligned} signals, need 3+)
            - Score too low ({score}/100, need ≥70)
            - Metrics are conflicting ({bull} bullish vs {bear} bearish)

            Wait for clearer convergence before trading.
            """.format(aligned=signal['aligned_signals'], score=score,
                      bull=signal['bullish_signals'], bear=signal['bearish_signals']))

    if action != 'SKIP':
        st.markdown("### 🎯 Suggested Levels")
        cols = st.columns(3)
        with cols[0]:
            st.metric("Entry", f"${signal['entry_price']:,.2f}", help="Current market price to enter the trade")
        with cols[1]:
            risk_pct = abs((signal['stop_loss'] - signal['entry_price']) / signal['entry_price'] * 100)
            st.metric("Stop Loss", f"${signal['stop_loss']:,.2f}",
                     help=f"Exit if wrong ({risk_pct:.1f}% risk)")
        with cols[2]:
            reward_pct = abs((signal['take_profit'] - signal['entry_price']) / signal['entry_price'] * 100)
            st.metric("Target", f"${signal['take_profit']:,.2f}",
                     help=f"Take profit target ({reward_pct:.1f}% gain)")


def render_metrics_grid(metrics: Dict[str, Any]):
    """Render metrics in a grid"""
    st.subheader("📊 Live Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Order Book Imbalance** ℹ️")
        with st.expander("What is this?", expanded=False):
            st.markdown("""
            **Order Book Imbalance** measures the balance between buy and sell orders.

            - **Positive (+)**: More bid liquidity = bullish pressure
            - **Negative (-)**: More ask liquidity = bearish pressure
            - **Threshold**: ±0.4 is significant, ±0.6 is extreme

            *Why it matters:* Shows where "big money" is waiting. Large imbalances often precede price moves.
            """)
        ob = metrics.get('ob_imbalance', 0)
        direction = "Bullish 🟢" if ob > 0 else "Bearish 🔴" if ob < 0 else "Neutral ⚪"
        st.metric("Imbalance", f"{ob:.4f}", direction)

        st.markdown("---")

        st.markdown("**Funding Rate** ℹ️")
        with st.expander("What is this?", expanded=False):
            st.markdown("""
            **Funding Rate** is the fee longs pay to shorts (or vice versa) every 8 hours.

            - **High Positive (+10%+)**: Longs are crowded → Contrarian SHORT signal
            - **High Negative (-10%+)**: Shorts are crowded → Contrarian LONG signal
            - **Near Zero**: Balanced market

            *Why it matters:* Extreme funding = one side is overleveraged. Market often moves against crowded positions.
            """)
        funding = metrics.get('funding_annualized', 0)
        st.metric("Annualized", f"{funding:.2f}%",
                 "Extreme ⚠️" if abs(funding) > 10 else "Normal ✓")

    with col2:
        st.markdown("**VWAP Deviation** ℹ️")
        with st.expander("What is this?", expanded=False):
            st.markdown("""
            **VWAP** (Volume-Weighted Average Price) is the average price institutions paid over the last hour.

            - **Z-Score > +1.5**: Price is stretched ABOVE VWAP → Mean reversion SHORT
            - **Z-Score < -1.5**: Price is stretched BELOW VWAP → Mean reversion LONG
            - **±2.0+**: Extreme deviation

            *Why it matters:* Price tends to revert to VWAP. Extreme deviations = rubber band about to snap back.
            """)
        vwap = metrics.get('vwap', 0)
        z_score = metrics.get('vwap_z_score', 0)
        current_price = metrics.get('current_price', 0)
        st.metric("VWAP", f"${vwap:,.2f}")
        st.metric("Current Price", f"${current_price:,.2f}")
        st.metric("Z-Score", f"{z_score:.2f}σ",
                 "Stretched ⚠️" if abs(z_score) > 1.5 else "Normal ✓")

    with col3:
        st.markdown("**Trade Flow** ℹ️")
        with st.expander("What is this?", expanded=False):
            st.markdown("""
            **Trade Flow** detects who's being aggressive (market orders vs limit orders).

            - **Positive (+)**: Aggressive buying pressure
            - **Negative (-)**: Aggressive selling pressure
            - **Threshold**: ±0.3 moderate, ±0.5 strong

            *Why it matters:* Shows institutional urgency. High volume + strong flow = conviction move.
            """)
        flow = metrics.get('flow_imbalance', 0)
        direction = "Buying 🟢" if flow > 0 else "Selling 🔴" if flow < 0 else "Neutral ⚪"
        st.metric("Flow", f"{flow:.4f}", direction)

        st.markdown("---")

        st.markdown("**Open Interest Divergence** ℹ️")
        with st.expander("What is this?", expanded=False):
            st.markdown("""
            **Open Interest (OI)** is the total number of open futures contracts. Compares current OI vs 4 hours ago.

            - **Price ↑ + OI ↑**: Real bullish trend (new longs opening) ✅
            - **Price ↑ + OI ↓**: Fake rally (shorts covering) ❌ Fade it
            - **Price ↓ + OI ↑**: Real bearish trend (new shorts opening) ✅
            - **Price ↓ + OI ↓**: Fake dump (longs closing) ❌ Fade it

            *Why it matters:* Separates real trends from fake-outs. OI confirms if money is entering or exiting.
            """)
        oi_change = metrics.get('oi_change_pct', 0)
        price_change = metrics.get('price_change_pct', 0)
        oi_type = metrics.get('oi_divergence_type', 'unknown')

        # Color code the OI type
        oi_emoji = {
            'strong_bullish': '🟢 Real Bullish',
            'strong_bearish': '🔴 Real Bearish',
            'weak_bullish': '🟡 Fake Rally',
            'weak_bearish': '🟡 Fake Dump',
            'neutral': '⚪ Neutral',
            'unknown': '❓ Unknown'
        }
        st.metric("OI Change", f"{oi_change:.2f}%", oi_emoji.get(oi_type, oi_type))
        st.metric("Price Change (4h)", f"{price_change:.2f}%")

    # Basis at the bottom
    st.markdown("---")
    st.markdown("**Basis Spread (Perp vs Spot)** ℹ️")
    with st.expander("What is this?", expanded=False):
        st.markdown("""
        **Basis** is the price difference between perpetual futures and spot markets.

        - **Positive (+)**: Perps trading at premium → Bearish if extreme (>0.3%)
        - **Negative (-)**: Perps trading at discount → Bullish if extreme
        - **Should align with Funding Rate** when both are extreme

        *Why it matters:* Confirms funding signals. If funding and basis disagree, it reduces signal quality.
        """)
    basis = metrics.get('basis_pct', 0)
    st.metric("Basis", f"{basis:.4f}%",
             "Premium ⬆️" if basis > 0 else "Discount ⬇️" if basis < 0 else "Fair ✓")


def render_signal_breakdown(signal: Dict[str, Any]):
    """Render detailed signal breakdown"""
    st.subheader("🔍 Signal Breakdown")

    with st.expander("ℹ️ How to read this breakdown", expanded=False):
        st.markdown("""
        **Score Breakdown** shows how many points each metric contributed:
        - Maximum possible score: 100 points
        - Signal threshold: 70 points
        - Higher scores = stronger convergence

        **Signal Details** shows the directional bias of each metric:
        - 🟢 Bullish signals suggest upward movement
        - 🔴 Bearish signals suggest downward movement
        - Only triggers when 3+ signals align in same direction
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Score Breakdown**")
        for metric, points in signal['score_breakdown'].items():
            st.write(f"• {metric}: **{points}** points")

    with col2:
        st.markdown("**Signal Details**")
        for metric, detail in signal['signal_breakdown'].items():
            st.write(f"• {metric}: {detail}")


def render_sidebar():
    """Render sidebar with settings"""
    st.sidebar.title("⚙️ Settings")

    # Coin selector
    coin = st.sidebar.selectbox("Select Coin", COINS, index=0)

    st.sidebar.markdown("---")

    # How It Works section
    with st.sidebar.expander("📚 How It Works", expanded=False):
        st.markdown("""
        **Strategy Monitor** is a multi-signal convergence system that filters out noise and only alerts you to high-probability setups.

        **The 5 Signals:**
        1. **Order Book** - Where big money is waiting
        2. **Funding Rate** - Crowd sentiment (contrarian)
        3. **VWAP** - Mean reversion anchor
        4. **Trade Flow** - Who's being aggressive
        5. **Open Interest** - Real vs fake moves

        **Signal Generation:**
        - Each metric is scored (0-30 points)
        - Scores are added to get convergence score (max 100)
        - Signal fires when:
          - Score ≥ 70 AND
          - 3+ metrics point the same direction

        **Confidence Levels:**
        - **HIGH**: Score ≥85 + 4+ aligned signals
        - **MEDIUM**: Score ≥70 + 3+ aligned signals
        - **LOW**: Below thresholds
        """)

    with st.sidebar.expander("🎯 How to Use", expanded=False):
        st.markdown("""
        **GREEN (LONG)**: 3+ bullish signals + score ≥70
        - Wait for confirmation on lower timeframes
        - Enter at current price or pullback
        - Use suggested stop/target as guide

        **RED (SHORT)**: 3+ bearish signals + score ≥70
        - Wait for confirmation on lower timeframes
        - Enter at current price or bounce
        - Use suggested stop/target as guide

        **WHITE (SKIP)**: Not enough convergence
        - Less than 3 aligned signals OR
        - Score below 70
        - No edge, stay flat

        **⚠️ Risk Warning:**
        This is a signal generator, NOT financial advice.
        Always:
        - Backtest before live trading
        - Use proper position sizing
        - Never risk more than 1-2% per trade
        """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 System Info")
    st.sidebar.info(f"""
    - **Refresh**: Every {REFRESH_INTERVAL_SECONDS}s
    - **OI Lookback**: {OI_LOOKBACK_HOURS}h
    - **VWAP Period**: 60min
    - **Last Update**: {datetime.now().strftime('%H:%M:%S')}
    """)

    return coin


def main():
    """Main app"""
    st.title("📈 Hyperliquid Strategy Monitor")

    # Quick reference legend
    with st.expander("📖 Quick Reference - Signal Legend", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🟢 LONG Signal**")
            st.markdown("""
            - 3+ bullish metrics aligned
            - Score ≥70/100
            - Consider buying
            - Use suggested stop/target
            """)

        with col2:
            st.markdown("**🔴 SHORT Signal**")
            st.markdown("""
            - 3+ bearish metrics aligned
            - Score ≥70/100
            - Consider selling
            - Use suggested stop/target
            """)

        with col3:
            st.markdown("**⚪ SKIP (No Setup)**")
            st.markdown("""
            - Less than 3 aligned signals
            - Score <70/100
            - Conflicting metrics
            - Stay flat, no edge
            """)

        st.markdown("---")
        st.markdown("**📊 Metric Thresholds to Watch:**")
        thresholds_col1, thresholds_col2 = st.columns(2)

        with thresholds_col1:
            st.markdown("""
            - **Order Book**: ±0.4 significant, ±0.6 extreme
            - **Trade Flow**: ±0.3 moderate, ±0.5 strong
            - **VWAP Z-Score**: ±1.5 stretched, ±2.0 extreme
            """)

        with thresholds_col2:
            st.markdown("""
            - **Funding Rate**: ±7% elevated, ±10% extreme
            - **OI Change**: ±3% threshold (vs 4h ago)
            - **Basis**: ±0.3% threshold
            """)

    # Get components
    components = get_components()
    calculator = components['calculator']
    generator = components['generator']
    storage = components['storage']

    # Sidebar
    selected_coin = render_sidebar()

    # Placeholder for dynamic content
    status_placeholder = st.empty()
    signal_placeholder = st.empty()
    metrics_placeholder = st.empty()
    breakdown_placeholder = st.empty()

    # Fetch and display data
    status_placeholder.info(f"Fetching data for {selected_coin}...")

    try:
        # Fetch data (run async in sync context)
        data = asyncio.run(fetch_data(selected_coin))

        if not data:
            status_placeholder.error("Failed to fetch data")
            return

        status_placeholder.success(f"Data fetched at {data['timestamp'].strftime('%H:%M:%S')}")

        # Get historical OI
        historical_oi = get_historical_oi(storage, selected_coin)

        # Calculate metrics
        metrics = calculator.calculate_all_metrics(
            order_book=data['order_book'],
            perp_data=data['perp_data'],
            spot_data=data['spot_data'],
            candles=data['candles'],
            historical_oi=historical_oi
        )

        # Save current OI
        current_oi = float(data['perp_data'].get('openInterest', 0))
        current_price = metrics.get('current_price', 0)
        if current_oi > 0 and current_price > 0:
            save_current_oi(storage, selected_coin, current_oi, current_price)

        # Generate signal
        signal = generator.generate_signal(metrics)

        # Render UI
        with signal_placeholder.container():
            render_signal_header(signal)

        with metrics_placeholder.container():
            render_metrics_grid(metrics)

        with breakdown_placeholder.container():
            render_signal_breakdown(signal)

    except Exception as e:
        status_placeholder.error(f"Error: {e}")
        st.exception(e)

    # Auto-refresh
    time.sleep(REFRESH_INTERVAL_SECONDS)
    st.rerun()


if __name__ == "__main__":
    main()
