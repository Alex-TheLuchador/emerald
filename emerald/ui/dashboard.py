"""
Streamlit Dashboard (Decoupled Architecture)

Clean UI that consumes the core library, not embedded business logic
"""
import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from ..data.hyperliquid_client import HyperliquidClient
from ..metrics import registry as metric_registry
from ..strategies import ConvergenceStrategy
from ..common.models import OISnapshot
from ..common.config import get_config


# ============================================================================
# PLAIN ENGLISH TRANSLATIONS
# ============================================================================

METRIC_TRANSLATIONS = {
    "order_book_imbalance": {
        "beginner_name": "Buy vs Sell Orders",
        "beginner_desc": "Compares number of buy orders vs sell orders waiting on the exchange",
        "advanced_name": "Order Book Imbalance"
    },
    "trade_flow": {
        "beginner_name": "Buying/Selling Pressure",
        "beginner_desc": "Shows whether recent trades are mostly buys or sells",
        "advanced_name": "Trade Flow"
    },
    "vwap_deviation": {
        "beginner_name": "Price vs Average",
        "beginner_desc": "How far current price is from typical trading price",
        "advanced_name": "VWAP Deviation"
    },
    "funding_rate": {
        "beginner_name": "Trader Sentiment",
        "beginner_desc": "Shows if most traders are betting price goes UP or DOWN",
        "advanced_name": "Funding Rate"
    },
    "oi_divergence": {
        "beginner_name": "New Money Flow",
        "beginner_desc": "Tracks if new money is entering or leaving the market",
        "advanced_name": "OI Divergence"
    },
    "basis_spread": {
        "beginner_name": "Spot vs Futures Gap",
        "beginner_desc": "Price difference between spot and futures markets",
        "advanced_name": "Basis Spread"
    }
}

def translate_metric_value(metric_name: str, value: float, metadata: dict, is_beginner: bool) -> str:
    """Translate metric value to plain English"""
    if metric_name == "order_book_imbalance":
        if value > 0.3:
            return "MANY MORE BUYERS" if is_beginner else f"Strong Bullish ({value:.2f})"
        elif value > 0.1:
            return "More buyers" if is_beginner else f"Bullish ({value:.2f})"
        elif value < -0.3:
            return "MANY MORE SELLERS" if is_beginner else f"Strong Bearish ({value:.2f})"
        elif value < -0.1:
            return "More sellers" if is_beginner else f"Bearish ({value:.2f})"
        else:
            return "Balanced" if is_beginner else f"Neutral ({value:.2f})"

    elif metric_name == "trade_flow":
        if value > 1000:
            return "STRONG BUYING" if is_beginner else f"Strong Buying Flow ({value:.0f})"
        elif value > 100:
            return "Buying pressure" if is_beginner else f"Buying Flow ({value:.0f})"
        elif value < -1000:
            return "STRONG SELLING" if is_beginner else f"Strong Selling Flow ({value:.0f})"
        elif value < -100:
            return "Selling pressure" if is_beginner else f"Selling Flow ({value:.0f})"
        else:
            return "Neutral" if is_beginner else f"Neutral ({value:.0f})"

    elif metric_name == "vwap_deviation":
        z_score = metadata.get("z_score", 0)
        if z_score < -2:
            return "DEEPLY UNDERVALUED" if is_beginner else f"Oversold ({z_score:.2f}σ)"
        elif z_score < -1:
            return "Below average" if is_beginner else f"Below VWAP ({z_score:.2f}σ)"
        elif z_score > 2:
            return "DEEPLY OVERVALUED" if is_beginner else f"Overbought ({z_score:.2f}σ)"
        elif z_score > 1:
            return "Above average" if is_beginner else f"Above VWAP ({z_score:.2f}σ)"
        else:
            return "Fair value" if is_beginner else f"Near VWAP ({z_score:.2f}σ)"

    elif metric_name == "funding_rate":
        if abs(value) > 30:
            sentiment = "OVERCROWDED LONGS" if value > 0 else "OVERCROWDED SHORTS"
            return sentiment if is_beginner else f"Extreme ({value:.1f}%)"
        elif abs(value) > 15:
            sentiment = "Many betting UP" if value > 0 else "Many betting DOWN"
            return sentiment if is_beginner else f"Elevated ({value:.1f}%)"
        else:
            return "Balanced sentiment" if is_beginner else f"Normal ({value:.1f}%)"

    elif metric_name == "oi_divergence":
        div_type = metadata.get("divergence_type", "neutral")
        oi_change = metadata.get("oi_change_pct", 0)

        if div_type == "strong_bullish":
            return "NEW MONEY BUYING" if is_beginner else f"Strong Bullish Div ({oi_change:.1f}%)"
        elif div_type == "strong_bearish":
            return "NEW MONEY SELLING" if is_beginner else f"Strong Bearish Div ({oi_change:.1f}%)"
        elif div_type == "weak_bullish":
            return "Light buying" if is_beginner else f"Weak Bullish ({oi_change:.1f}%)"
        elif div_type == "weak_bearish":
            return "Light selling" if is_beginner else f"Weak Bearish ({oi_change:.1f}%)"
        else:
            return "No clear trend" if is_beginner else f"Neutral ({oi_change:.1f}%)"

    else:
        return f"{value:.4f}"


def render_strength_bar(score: int, max_score: int = 100) -> str:
    """Render visual strength bar (traffic light indicator)"""
    filled = int((score / max_score) * 5)
    empty = 5 - filled

    # Color coding
    if score >= 85:
        color = "🟢"
    elif score >= 70:
        color = "🟡"
    else:
        color = "🔴"

    bar = color * filled + "⚪" * empty
    return f"{bar} ({score}/{max_score})"


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


def render_signal_card(signal, is_beginner: bool = False):
    """Render signal card with plain English support"""
    action = signal.action.value
    score = signal.convergence_score
    confidence = signal.confidence.value
    aligned = signal.aligned_signals

    # Color coding
    if action == "LONG":
        color = "🟢"
        bg_color = "#1a4d2e"
        action_text = "BUY" if is_beginner else "LONG"
    elif action == "SHORT":
        color = "🔴"
        bg_color = "#4d1a1a"
        action_text = "SELL" if is_beginner else "SHORT"
    else:
        color = "⚪"
        bg_color = "#555555"
        action_text = "WAIT" if is_beginner else "SKIP"

    # Strength bar
    strength_bar = render_strength_bar(score)

    # Confidence explanation
    if is_beginner:
        conf_text = f"{confidence} ({aligned} out of 6 indicators agree)"
    else:
        conf_text = f"{confidence} ({aligned} signals)"

    st.markdown(f"""
    <div style='padding: 20px; background-color: {bg_color}; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='text-align: center; margin: 0;'>{color} {action_text}</h1>
        <h3 style='text-align: center; margin: 10px 0;'>
            {strength_bar}
        </h3>
        <p style='text-align: center; margin: 5px 0; opacity: 0.9;'>
            Confidence: {conf_text}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if action != "SKIP":
        cols = st.columns(3)
        with cols[0]:
            st.metric("Entry Price" if is_beginner else "Entry", f"${signal.entry_price:,.2f}")
        with cols[1]:
            st.metric("Stop Loss", f"${signal.stop_loss:,.2f}")
            if is_beginner and signal.entry_price:
                risk = abs(signal.entry_price - signal.stop_loss)
                st.caption(f"Risk: ${risk:,.2f}")
        with cols[2]:
            st.metric("Target Price" if is_beginner else "Target", f"${signal.take_profit:,.2f}")
            if is_beginner and signal.entry_price:
                reward = abs(signal.take_profit - signal.entry_price)
                st.caption(f"Reward: ${reward:,.2f}")


def render_metrics(metrics, is_beginner: bool = False):
    """Render metrics grid with beginner/advanced mode support"""
    st.subheader("📊 Live Metrics" if not is_beginner else "📊 What's Happening Right Now")

    # Filter metrics for beginner mode (show only core 4)
    if is_beginner:
        priority_metrics = ["order_book_imbalance", "trade_flow", "vwap_deviation", "funding_rate"]
        display_metrics = {k: v for k, v in metrics.items() if k in priority_metrics}
    else:
        display_metrics = metrics

    # Determine layout
    num_metrics = len(display_metrics)
    if num_metrics <= 3:
        cols = st.columns(num_metrics)
    else:
        cols = st.columns(3)

    col_idx = 0
    for metric_name, metric_obj in display_metrics.items():
        col = cols[col_idx % len(cols)]

        with col:
            # Get translation
            translation = METRIC_TRANSLATIONS.get(metric_name, {})
            display_name = translation.get("beginner_name" if is_beginner else "advanced_name", metric_name)
            description = translation.get("beginner_desc", "")

            # Get interpreted value
            interpreted = translate_metric_value(
                metric_name,
                metric_obj.value,
                metric_obj.metadata,
                is_beginner
            )

            # Display metric
            if is_beginner:
                st.markdown(f"**{display_name}**")
                st.info(interpreted)
                if description:
                    st.caption(description)
            else:
                st.metric(display_name, interpreted)

        col_idx += 1


async def fetch_raw_data(coin: str, data_type: str) -> Dict[str, Any]:
    """Fetch raw data from Hyperliquid for debugging/analysis"""
    async with HyperliquidClient() as client:
        if data_type == "Order Book":
            return await client.get_order_book(coin)
        elif data_type == "Perpetual Metadata":
            return await client.get_perp_metadata()
        elif data_type == "Spot Metadata":
            return await client.get_spot_metadata()
        elif data_type == "Candles (1m, 60min)":
            return await client.get_candles(coin, interval="1m", lookback_minutes=60)
        elif data_type == "Funding History (7d)":
            return await client.get_funding_history(coin, lookback_hours=168)
        else:
            return {"error": "Unknown data type"}


def render_raw_data_viewer(coin: str):
    """Render raw Hyperliquid data viewer"""
    with st.expander("🔍 View Raw Data from Hyperliquid"):
        st.markdown("**For advanced users:** View the raw JSON data fetched from Hyperliquid")

        data_type = st.selectbox(
            "Select data type:",
            [
                "Order Book",
                "Perpetual Metadata",
                "Spot Metadata",
                "Candles (1m, 60min)",
                "Funding History (7d)"
            ],
            key="raw_data_selector"
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            fetch_button = st.button("Fetch Data", type="primary")

        if fetch_button:
            with st.spinner(f"Fetching {data_type} for {coin}..."):
                try:
                    raw_data = asyncio.run(fetch_raw_data(coin, data_type))

                    # Display JSON
                    st.success(f"✅ Fetched {data_type}")
                    st.json(raw_data)

                    # Download button
                    json_str = json.dumps(raw_data, indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_str,
                        file_name=f"{coin}_{data_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

                except Exception as e:
                    st.error(f"Error fetching data: {e}")
                    st.exception(e)


def main():
    """Main dashboard"""
    st.title("💎 Emerald Trading Dashboard v2.0")

    config = get_config()

    # Initialize session state for beginner mode
    if "is_beginner_mode" not in st.session_state:
        st.session_state.is_beginner_mode = True  # Default to beginner mode

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Beginner/Advanced Mode Toggle
        st.markdown("### 🎯 Display Mode")
        mode = st.radio(
            "Choose your experience level:",
            ["🎓 Beginner Mode", "⚙️ Advanced Mode"],
            index=0 if st.session_state.is_beginner_mode else 1,
            help="Beginner mode uses plain English and shows core metrics. Advanced mode shows technical details."
        )
        st.session_state.is_beginner_mode = (mode == "🎓 Beginner Mode")

        if st.session_state.is_beginner_mode:
            st.info("📚 Beginner mode shows simplified metrics with plain language explanations")
        else:
            st.info("🔧 Advanced mode shows all technical metrics and details")

        st.markdown("---")

        # Coin selector
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
    is_beginner = st.session_state.is_beginner_mode
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
            render_signal_card(result["signal"], is_beginner=is_beginner)

        # Render metrics
        with metrics_container:
            render_metrics(result["metrics"], is_beginner=is_beginner)

        # Score breakdown (advanced mode only)
        if not is_beginner:
            with st.expander("📊 Score Breakdown"):
                for metric, points in result["signal"].score_breakdown.items():
                    st.write(f"**{metric}**: {points} points")

        # Signal breakdown
        expander_title = "🔍 How We Got This Signal" if is_beginner else "🔍 Signal Details"
        with st.expander(expander_title):
            for metric, detail in result["signal"].signal_breakdown.items():
                # Get friendly name for beginner mode
                if is_beginner:
                    translation = METRIC_TRANSLATIONS.get(metric, {})
                    friendly_name = translation.get("beginner_name", metric)
                    st.write(f"**{friendly_name}**: {detail}")
                else:
                    st.write(f"**{metric}**: {detail}")

        # Raw data viewer (advanced mode only)
        if not is_beginner:
            render_raw_data_viewer(coin)

    except Exception as e:
        status.error(f"Error: {e}")
        st.exception(e)

    # Auto-refresh
    import time
    time.sleep(config.ui.refresh_interval_seconds)
    st.rerun()


if __name__ == "__main__":
    main()
