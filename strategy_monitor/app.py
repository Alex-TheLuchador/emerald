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
    elif action == 'SHORT':
        color = '🔴'
        bg_color = '#4d1a1a'
    else:
        color = '⚪'
        bg_color = "#d3d3d3"

    st.markdown(f"""
    <div style='padding: 20px; background-color: {bg_color}; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='text-align: center; margin: 0;'>{color} {action}</h1>
        <h3 style='text-align: center; margin: 10px 0;'>
            Score: {score}/100 | Confidence: {confidence} |
            Signals: {signal['aligned_signals']} aligned
        </h3>
    </div>
    """, unsafe_allow_html=True)

    if action != 'SKIP':
        cols = st.columns(3)
        with cols[0]:
            st.metric("Entry", f"${signal['entry_price']:,.2f}")
        with cols[1]:
            st.metric("Stop Loss", f"${signal['stop_loss']:,.2f}")
        with cols[2]:
            st.metric("Target", f"${signal['take_profit']:,.2f}")


def render_metrics_grid(metrics: Dict[str, Any]):
    """Render metrics in a grid"""
    st.subheader("📊 Live Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Order Book**")
        ob = metrics.get('ob_imbalance', 0)
        direction = "Bullish" if ob > 0 else "Bearish" if ob < 0 else "Neutral"
        st.metric("Imbalance", f"{ob:.4f}", direction)

        st.markdown("**Funding Rate**")
        funding = metrics.get('funding_annualized', 0)
        st.metric("Annualized", f"{funding:.2f}%",
                 "Extreme" if abs(funding) > 10 else "Normal")

    with col2:
        st.markdown("**VWAP**")
        vwap = metrics.get('vwap', 0)
        z_score = metrics.get('vwap_z_score', 0)
        st.metric("VWAP", f"${vwap:,.2f}")
        st.metric("Z-Score", f"{z_score:.2f}σ",
                 "Stretched" if abs(z_score) > 1.5 else "Normal")

    with col3:
        st.markdown("**Trade Flow**")
        flow = metrics.get('flow_imbalance', 0)
        direction = "Buying" if flow > 0 else "Selling" if flow < 0 else "Neutral"
        st.metric("Flow", f"{flow:.4f}", direction)

        st.markdown("**Open Interest**")
        oi_change = metrics.get('oi_change_pct', 0)
        oi_type = metrics.get('oi_divergence_type', 'unknown')
        st.metric("Change", f"{oi_change:.2f}%", oi_type)

    # Basis at the bottom
    st.markdown("**Basis Spread (Perp vs Spot)**")
    basis = metrics.get('basis_pct', 0)
    st.metric("Basis", f"{basis:.4f}%",
             "Premium" if basis > 0 else "Discount" if basis < 0 else "Fair")


def render_signal_breakdown(signal: Dict[str, Any]):
    """Render detailed signal breakdown"""
    st.subheader("🔍 Signal Breakdown")

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
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    **Strategy Monitor** analyzes 5 key metrics:
    - Order Book Imbalance
    - Funding Rate
    - VWAP Deviation
    - Trade Flow
    - Open Interest

    Generates signals when 3+ metrics align and score ≥70.
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"Auto-refresh: {REFRESH_INTERVAL_SECONDS}s")
    st.sidebar.markdown(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

    return coin


def main():
    """Main app"""
    st.title("📈 Hyperliquid Strategy Monitor")

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
