"""
Streamlit Dashboard (Decoupled Architecture)

Clean UI that consumes the core library, not embedded business logic
"""
import streamlit as st
import asyncio
from datetime import datetime
from typing import Dict, Any

from ..data.hyperliquid_client import HyperliquidClient
from ..metrics import registry as metric_registry
from ..strategies import ConvergenceStrategy
from ..common.models import OISnapshot
from ..common.config import get_config


# Page config
st.set_page_config(
    page_title="Emerald Trading Dashboard",
    page_icon="💎",
    layout="wide"
)


@st.cache_resource
def get_strategy():
    """Get strategy instance (cached)"""
    return ConvergenceStrategy()


# In-memory OI storage (simple)
if "oi_storage" not in st.session_state:
    st.session_state.oi_storage = {}


async def fetch_and_analyze(coin: str) -> Dict[str, Any]:
    """Fetch data and generate signal"""
    config = get_config()

    # Fetch market data
    async with HyperliquidClient() as client:
        market_data = await client.get_market_data(coin)

    # Get historical OI
    historical_oi = None
    if coin in st.session_state.oi_storage:
        lookback_hours = config.calculation.oi_lookback_hours
        target_time = market_data.timestamp.timestamp() - (lookback_hours * 3600)

        snapshots = st.session_state.oi_storage[coin]
        closest = min(snapshots, key=lambda s: abs(s.timestamp - target_time), default=None)
        if closest and abs(closest.timestamp - target_time) < 1800:
            historical_oi = closest

    # Calculate metrics
    metrics = metric_registry.calculate_all(market_data, historical_oi)

    # Save current OI
    current_oi = market_data.perp_data.open_interest
    current_price = market_data.candles[-1].close if market_data.candles else 0

    if current_oi > 0:
        if coin not in st.session_state.oi_storage:
            st.session_state.oi_storage[coin] = []

        snapshot = OISnapshot(
            oi=current_oi,
            price=current_price,
            timestamp=market_data.timestamp.timestamp()
        )
        st.session_state.oi_storage[coin].append(snapshot)

        if len(st.session_state.oi_storage[coin]) > 1000:
            st.session_state.oi_storage[coin] = st.session_state.oi_storage[coin][-1000:]

    # Generate signal
    strategy = get_strategy()
    signal = strategy.generate_signal(market_data, metrics)

    return {
        "market_data": market_data,
        "metrics": metrics,
        "signal": signal
    }


def render_signal_card(signal):
    """Render signal card"""
    action = signal.action.value
    score = signal.convergence_score
    confidence = signal.confidence.value

    # Color coding
    if action == "LONG":
        color = "🟢"
        bg_color = "#1a4d2e"
    elif action == "SHORT":
        color = "🔴"
        bg_color = "#4d1a1a"
    else:
        color = "⚪"
        bg_color = "#555555"

    st.markdown(f"""
    <div style='padding: 20px; background-color: {bg_color}; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='text-align: center; margin: 0;'>{color} {action}</h1>
        <h3 style='text-align: center; margin: 10px 0;'>
            Score: {score}/100 | Confidence: {confidence}
        </h3>
    </div>
    """, unsafe_allow_html=True)

    if action != "SKIP":
        cols = st.columns(3)
        with cols[0]:
            st.metric("Entry", f"${signal.entry_price:,.2f}")
        with cols[1]:
            st.metric("Stop Loss", f"${signal.stop_loss:,.2f}")
        with cols[2]:
            st.metric("Target", f"${signal.take_profit:,.2f}")


def render_metrics(metrics):
    """Render metrics grid"""
    st.subheader("📊 Live Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "order_book_imbalance" in metrics:
            ob = metrics["order_book_imbalance"].value
            st.metric("Order Book Imbalance", f"{ob:.4f}",
                     "Bullish" if ob > 0 else "Bearish" if ob < 0 else "Neutral")

        if "trade_flow" in metrics:
            flow = metrics["trade_flow"].value
            st.metric("Trade Flow", f"{flow:.4f}",
                     "Buying" if flow > 0 else "Selling" if flow < 0 else "Neutral")

    with col2:
        if "vwap_deviation" in metrics:
            vwap_metric = metrics["vwap_deviation"]
            vwap = vwap_metric.metadata.get("vwap", 0)
            z_score = vwap_metric.value
            st.metric("VWAP", f"${vwap:,.2f}")
            st.metric("Z-Score", f"{z_score:.2f}σ",
                     "Stretched" if abs(z_score) > 1.5 else "Normal")

    with col3:
        if "funding_rate" in metrics:
            funding = metrics["funding_rate"].value
            st.metric("Funding (Annual)", f"{funding:.2f}%",
                     "Extreme" if abs(funding) > 10 else "Normal")

        if "oi_divergence" in metrics:
            oi_metric = metrics["oi_divergence"]
            oi_type = oi_metric.metadata.get("divergence_type", "unknown")
            oi_change = oi_metric.metadata.get("oi_change_pct", 0)
            st.metric("OI Change", f"{oi_change:.2f}%", oi_type)


def main():
    """Main dashboard"""
    st.title("💎 Emerald Trading Dashboard v2.0")
    st.markdown("**Decoupled Architecture** - Clean separation of concerns")

    config = get_config()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        coin = st.selectbox("Select Coin", config.ui.coins)

        st.markdown("---")
        st.markdown("### 📈 Strategy")
        st.info(f"""
        **Convergence Strategy**

        - Min Score: {config.signal.min_convergence_score}
        - Min Signals: {config.signal.min_aligned_signals}
        - Metrics: {len(metric_registry.list_metrics())}
        """)

        st.markdown("---")
        if st.button("🔄 Refresh"):
            st.rerun()

    # Main content
    status = st.empty()
    signal_container = st.container()
    metrics_container = st.container()

    try:
        status.info(f"Fetching data for {coin}...")

        # Fetch and analyze
        result = asyncio.run(fetch_and_analyze(coin))

        status.success(f"✅ Data updated at {datetime.now().strftime('%H:%M:%S')}")

        # Render signal
        with signal_container:
            render_signal_card(result["signal"])

        # Render metrics
        with metrics_container:
            render_metrics(result["metrics"])

        # Score breakdown
        with st.expander("📊 Score Breakdown"):
            for metric, points in result["signal"].score_breakdown.items():
                st.write(f"**{metric}**: {points} points")

        # Signal breakdown
        with st.expander("🔍 Signal Details"):
            for metric, detail in result["signal"].signal_breakdown.items():
                st.write(f"**{metric}**: {detail}")

    except Exception as e:
        status.error(f"Error: {e}")
        st.exception(e)

    # Auto-refresh
    import time
    time.sleep(config.ui.refresh_interval_seconds)
    st.rerun()


if __name__ == "__main__":
    main()
