"""
Strategy Monitor Dashboard - Phase 2
Displays institutional positioning and liquidity signals in real-time
"""
import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional

from api_client import HyperliquidClient
from storage import MultiTimeframeStorage
from metrics.positioning import InstitutionalPositioning
from metrics.liquidity import InstitutionalLiquidity
from whale_loader import load_whale_addresses

# Page config
st.set_page_config(
    page_title="Strategy Monitor - Phase 2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def get_components():
    """Initialize components (cached)"""
    return {
        'storage': MultiTimeframeStorage(
            oi_retention_hours=168,
            funding_retention_hours=168,
            orderbook_retention_hours=1,
            snapshot_interval_minutes=15
        ),
        'positioning': InstitutionalPositioning(),
        'liquidity': InstitutionalLiquidity(),
        'whale_addresses': load_whale_addresses()
    }


async def fetch_live_data(coin: str) -> Optional[Dict[str, Any]]:
    """Fetch live data from Hyperliquid"""
    try:
        async with HyperliquidClient() as client:
            data = await client.get_all_data(coin, include_whale_data=False)
            return data
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None


def display_positioning_signal(signal, coin: str):
    """Display institutional positioning signal"""
    st.subheader(f"📈 Signal 1: Institutional Positioning ({coin})")

    # Main signal display
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if signal.direction == "BULLISH":
            st.metric("Direction", "🟢 BULLISH", signal.regime)
        elif signal.direction == "BEARISH":
            st.metric("Direction", "🔴 BEARISH", signal.regime)
        else:
            st.metric("Direction", "⚪ NEUTRAL", signal.regime)

    with col2:
        st.metric("Strength", f"{signal.strength:.1f}/10", f"{signal.confidence} confidence")

    with col3:
        st.metric("Funding Velocity", f"{signal.velocity_4h:+.2f}%", "4h change")

    with col4:
        st.metric("Acceleration", f"{signal.acceleration:+.3f}", "2nd derivative")

    # Details
    with st.expander("📊 Signal Details"):
        st.write(f"**Regime**: {signal.regime}")
        st.write(f"**Description**: {signal.details.get('regime_description', 'N/A')}")
        st.write(f"**Current Funding**: {signal.details.get('current_funding', 0):.2f}%")
        st.write(f"**Volume Context**: {signal.details.get('volume_context', 'N/A')}")
        st.write(f"**Volume Ratio**: {signal.volume_ratio:.2f}x average")


def display_liquidity_signal(signal, coin: str):
    """Display institutional liquidity signal"""
    st.subheader(f"💰 Signal 2: Institutional Liquidity ({coin})")

    # Main signal display
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if signal.direction == "BULLISH":
            st.metric("Direction", "🟢 BULLISH", signal.quality + " quality")
        elif signal.direction == "BEARISH":
            st.metric("Direction", "🔴 BEARISH", signal.quality + " quality")
        else:
            st.metric("Direction", "⚪ NEUTRAL", signal.quality + " quality")

    with col2:
        st.metric("Strength", f"{signal.strength:.1f}/10", f"Quality: {signal.details['quality_score']:.3f}")

    with col3:
        st.metric("Order Book Imbalance", f"{signal.size_imbalance:+.3f}",
                  "BID" if signal.size_imbalance > 0 else "ASK")

    with col4:
        if signal.velocity is not None:
            st.metric("Liquidity Velocity", f"{signal.velocity:+.4f}", "repositioning speed")
        else:
            st.metric("Liquidity Velocity", "N/A", "need more data")

    # Details
    with st.expander("📊 Signal Details"):
        st.write(f"**Bid Concentration**: {signal.concentration['bid']:.3f}")
        st.write(f"**Ask Concentration**: {signal.concentration['ask']:.3f}")
        if signal.details.get('concentration_warning'):
            st.warning("⚠️ High concentration detected - possible fake wall")
        st.write(f"**Quote Stuffing Detected**: {'Yes ⚠️' if signal.is_manipulated else 'No ✅'}")
        st.write(f"**Dominant Side**: {signal.details.get('dominant_side', 'N/A')}")


def display_summary(positioning_signal, liquidity_signal, coin: str):
    """Display combined signal summary"""
    st.markdown("---")
    st.header(f"🎯 Signal Convergence: {coin}")

    # Count aligned signals
    signals_bullish = 0
    signals_bearish = 0

    if positioning_signal.direction == "BULLISH":
        signals_bullish += 1
    elif positioning_signal.direction == "BEARISH":
        signals_bearish += 1

    if liquidity_signal.direction == "BULLISH":
        signals_bullish += 1
    elif liquidity_signal.direction == "BEARISH":
        signals_bearish += 1

    total_aligned = max(signals_bullish, signals_bearish)

    # Determine overall direction
    if signals_bullish >= 2:
        overall_direction = "BULLISH"
        overall_color = "🟢"
    elif signals_bearish >= 2:
        overall_direction = "BEARISH"
        overall_color = "🔴"
    else:
        overall_direction = "NEUTRAL (CONFLICTED)"
        overall_color = "⚪"

    # Display
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Overall Direction", f"{overall_color} {overall_direction}")

    with col2:
        st.metric("Aligned Signals", f"{total_aligned}/2",
                  f"({signals_bullish} bullish, {signals_bearish} bearish)")

    with col3:
        avg_strength = (positioning_signal.strength + liquidity_signal.strength) / 2
        st.metric("Average Strength", f"{avg_strength:.1f}/10")

    # Trading recommendation
    if total_aligned >= 2:
        if overall_direction == "BULLISH":
            st.success(f"✅ **LONG Setup**: Both signals aligned bullish. Average strength: {avg_strength:.1f}/10")
        else:
            st.error(f"✅ **SHORT Setup**: Both signals aligned bearish. Average strength: {avg_strength:.1f}/10")
    else:
        st.warning("⚠️ **SKIP**: Signals not aligned. Wait for convergence.")


def main():
    """Main dashboard"""
    st.title("📊 Strategy Monitor - Phase 2 Dashboard")
    st.markdown("**Institutional Positioning & Liquidity Signals**")

    # Get components
    components = get_components()
    storage = components['storage']
    positioning_analyzer = components['positioning']
    liquidity_analyzer = components['liquidity']
    whale_addresses = components['whale_addresses']

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Coin selection
        coin = st.selectbox("Select Coin", ["BTC", "ETH", "SOL"], index=0)

        # Refresh interval
        refresh_interval = st.slider("Refresh Interval (seconds)", 10, 300, 60)

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh", value=True)

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.rerun()

        st.markdown("---")
        st.markdown(f"**Whale Addresses Loaded**: {len(whale_addresses)}")
        st.markdown(f"**Storage Stats**:")
        stats = storage.get_stats()
        st.markdown(f"- OI coins: {stats.get('oi_coins', 0)}")
        st.markdown(f"- Funding coins: {stats.get('funding_coins', 0)}")

    # Fetch live data
    with st.spinner(f"Fetching live data for {coin}..."):
        data = asyncio.run(fetch_live_data(coin))

    if not data:
        st.error("Failed to fetch data from Hyperliquid API")
        return

    # Extract data
    order_book = data.get('order_book', {})
    perp_data = data.get('perp_data', {})
    candles = data.get('candles', [])

    # Display data freshness
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Store current snapshot
    current_oi = float(perp_data.get('openInterest', 0))
    current_funding = float(perp_data.get('funding', 0)) * 100  # Convert to %
    current_price = float(perp_data.get('markPx', 0))

    if current_oi > 0 and current_price > 0:
        storage.add_oi_snapshot(coin, current_oi, current_price)
        storage.add_funding_snapshot(coin, current_funding)

    # Calculate volume metrics
    volume_24h = float(perp_data.get('dayNtlVlm', 0))
    # Estimate current hourly volume from recent candles
    if candles and len(candles) >= 60:
        recent_volume = sum(float(c.get('v', 0)) for c in candles[-60:])  # Last 60 min
        avg_hourly_volume = volume_24h / 24 if volume_24h > 0 else 1
        volume_ratio = recent_volume / avg_hourly_volume if avg_hourly_volume > 0 else 1.0
    else:
        volume_ratio = 1.0

    # Signal 1: Institutional Positioning
    funding_dynamics = storage.get_funding_dynamics(coin)

    if funding_dynamics:
        volume_data = {
            'current': recent_volume if candles and len(candles) >= 60 else volume_24h / 24,
            'avg_24h': volume_24h / 24
        }

        positioning_signal = positioning_analyzer.analyze(funding_dynamics, volume_data)
        display_positioning_signal(positioning_signal, coin)
    else:
        st.warning(f"⚠️ Insufficient funding history for {coin}. Need at least 8 hours of data.")
        st.info("The system will automatically collect funding snapshots. Check back in a few hours.")
        positioning_signal = None

    st.markdown("---")

    # Signal 2: Institutional Liquidity
    if order_book and order_book.get('levels'):
        # Get previous snapshots for velocity
        previous_snapshots = None  # TODO: Implement snapshot history

        liquidity_signal = liquidity_analyzer.analyze(order_book, previous_snapshots)
        display_liquidity_signal(liquidity_signal, coin)
    else:
        st.warning(f"⚠️ No order book data available for {coin}")
        liquidity_signal = None

    # Combined summary
    if positioning_signal and liquidity_signal:
        display_summary(positioning_signal, liquidity_signal, coin)

    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
