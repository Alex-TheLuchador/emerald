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
from ..storage.signal_history import SignalHistory


# ============================================================================
# PLAIN ENGLISH TRANSLATIONS
# ============================================================================

# Detailed metric tooltips
METRIC_TOOLTIPS = {
    "order_book_imbalance": {
        "title": "Buy vs Sell Orders",
        "explanation": "This compares the total amount of buy orders vs sell orders waiting on the exchange.",
        "interpretation": {
            "positive": "More buy orders = bullish (buyers outnumber sellers)",
            "negative": "More sell orders = bearish (sellers outnumber buyers)",
            "neutral": "Balanced orders = no clear pressure"
        },
        "example": "If value is +0.45, there are 45% more buy orders than sell orders"
    },
    "trade_flow": {
        "title": "Buying/Selling Pressure",
        "explanation": "Analyzes recent trades to see if buying or selling is dominant.",
        "interpretation": {
            "positive": "Positive flow = more aggressive buying",
            "negative": "Negative flow = more aggressive selling",
            "neutral": "Neutral = balanced buy/sell activity"
        },
        "example": "Large positive value means strong buying pressure in recent trades"
    },
    "vwap_deviation": {
        "title": "Price vs Average",
        "explanation": "Compares current price to the volume-weighted average price (VWAP).",
        "interpretation": {
            "positive": "Above VWAP = price is higher than average (possible overvaluation)",
            "negative": "Below VWAP = price is lower than average (possible undervaluation)",
            "neutral": "Near VWAP = price at fair value"
        },
        "example": "Z-score of -2.0 means price is 2 standard deviations below average (deeply undervalued)"
    },
    "funding_rate": {
        "title": "Trader Sentiment",
        "explanation": "Shows what traders are paying to hold long or short positions.",
        "interpretation": {
            "positive": "High positive = longs pay shorts (too many people betting UP)",
            "negative": "High negative = shorts pay longs (too many people betting DOWN)",
            "neutral": "Near zero = balanced sentiment"
        },
        "example": "35% annual funding means longs are overcrowded, often precedes reversal"
    },
    "oi_divergence": {
        "title": "New Money Flow",
        "explanation": "Tracks whether new money is entering or leaving the market.",
        "interpretation": {
            "positive": "Rising OI + rising price = new money buying (bullish)",
            "negative": "Rising OI + falling price = new money selling (bearish)",
            "neutral": "No clear divergence = normal market activity"
        },
        "example": "Strong bullish divergence = new traders opening long positions"
    },
    "basis_spread": {
        "title": "Spot vs Futures Gap",
        "explanation": "Price difference between spot (immediate) and futures (contract) markets.",
        "interpretation": {
            "positive": "Positive spread = futures trading above spot (bullish)",
            "negative": "Negative spread = futures trading below spot (bearish)",
            "neutral": "Small spread = markets in sync"
        },
        "example": "Large positive spread indicates traders willing to pay premium for futures"
    }
}

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


def render_metric_tooltip(metric_name: str):
    """Render expandable tooltip for a metric"""
    tooltip = METRIC_TOOLTIPS.get(metric_name)
    if not tooltip:
        return

    with st.expander(f"ℹ️ Learn about {tooltip['title']}"):
        st.markdown(f"**What it measures:**")
        st.write(tooltip['explanation'])

        st.markdown(f"**How to read it:**")
        for key, text in tooltip['interpretation'].items():
            st.write(f"• {text}")

        st.markdown(f"**Example:**")
        st.info(tooltip['example'])


def generate_natural_summary(signal, metrics: dict, is_beginner: bool = True) -> str:
    """Generate plain English summary of the signal"""
    action = signal.action.value
    score = signal.convergence_score

    # Determine market state from metrics
    summary_parts = []

    # Price position
    if "vwap_deviation" in metrics:
        z_score = metrics["vwap_deviation"].metadata.get("z_score", 0)
        if z_score < -2:
            summary_parts.append("trading well below its average price")
        elif z_score < -1:
            summary_parts.append("trading below its average price")
        elif z_score > 2:
            summary_parts.append("trading well above its average price")
        elif z_score > 1:
            summary_parts.append("trading above its average price")
        else:
            summary_parts.append("trading near its average price")

    # Buying/selling pressure
    if "trade_flow" in metrics:
        flow = metrics["trade_flow"].value
        if flow > 1000:
            summary_parts.append("showing strong buying pressure")
        elif flow > 100:
            summary_parts.append("showing moderate buying pressure")
        elif flow < -1000:
            summary_parts.append("showing strong selling pressure")
        elif flow < -100:
            summary_parts.append("showing moderate selling pressure")

    # Order book state
    if "order_book_imbalance" in metrics:
        ob = metrics["order_book_imbalance"].value
        if ob > 0.3:
            summary_parts.append("with many more buyers than sellers in the order book")
        elif ob < -0.3:
            summary_parts.append("with many more sellers than buyers in the order book")

    # Trader sentiment
    if "funding_rate" in metrics:
        funding = metrics["funding_rate"].value
        if abs(funding) > 30:
            if funding > 0:
                summary_parts.append("Most traders are heavily betting on price going UP, which often signals a reversal")
            else:
                summary_parts.append("Most traders are heavily betting on price going DOWN, which often signals a reversal")
        elif abs(funding) > 15:
            if funding > 0:
                summary_parts.append("Many traders are betting on price going UP")
            else:
                summary_parts.append("Many traders are betting on price going DOWN")

    # Open interest
    if "oi_divergence" in metrics:
        div_type = metrics["oi_divergence"].metadata.get("divergence_type", "neutral")
        if div_type == "strong_bullish":
            summary_parts.append("New money is entering the market on the buy side")
        elif div_type == "strong_bearish":
            summary_parts.append("New money is entering the market on the sell side")

    # Construct final summary
    if summary_parts:
        coin_text = f"The asset is {', '.join(summary_parts[:3])}."
        if len(summary_parts) > 3:
            coin_text += f" {' '.join(summary_parts[3:])}."
    else:
        coin_text = "Market conditions are being analyzed."

    # Add action recommendation
    if action == "LONG":
        action_text = "This is a **BUY signal**" if is_beginner else "This is a **LONG signal**"
        strength = "strong" if score >= 85 else "moderate" if score >= 70 else "weak"
        recommendation = f"{action_text} with {strength} conviction ({score}/100)."
    elif action == "SHORT":
        action_text = "This is a **SELL signal**" if is_beginner else "This is a **SHORT signal**"
        strength = "strong" if score >= 85 else "moderate" if score >= 70 else "weak"
        recommendation = f"{action_text} with {strength} conviction ({score}/100)."
    else:
        recommendation = f"**No clear signal** - waiting for better setup ({score}/100)."

    return f"{coin_text}\n\n{recommendation}"


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
                # Add tooltip in beginner mode
                render_metric_tooltip(metric_name)
            else:
                st.metric(display_name, interpreted)

        col_idx += 1


def render_score_breakdown_visual(score_breakdown: dict):
    """Render visual score breakdown with bars"""
    st.markdown("### 📊 Score Contribution")

    # Sort by absolute value
    sorted_breakdown = sorted(score_breakdown.items(), key=lambda x: abs(x[1]), reverse=True)

    for metric, points in sorted_breakdown:
        # Get friendly name
        translation = METRIC_TRANSLATIONS.get(metric, {})
        display_name = translation.get("advanced_name", metric)

        # Determine color
        if points > 0:
            color = "#4CAF50"  # Green
            emoji = "🟢"
        elif points < 0:
            color = "#F44336"  # Red
            emoji = "🔴"
        else:
            color = "#9E9E9E"  # Gray
            emoji = "⚪"

        # Calculate bar width (percentage)
        max_points = 30  # Max possible points per metric
        bar_width = min(abs(points) / max_points * 100, 100)

        # Render
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"{emoji} **{display_name}**")
            st.markdown(f'<div style="background-color: {color}; width: {bar_width}%; height: 20px; border-radius: 5px;"></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{points:+d}** pts")


def render_signal_confidence_breakdown(signal, metrics):
    """Render detailed confidence breakdown showing which metrics agree"""
    st.markdown("### 🎯 Signal Confidence Breakdown")

    aligned = signal.aligned_signals
    total = len(metrics)

    st.write(f"**{aligned} out of {total} indicators agree** with this signal")

    # Show each metric's contribution
    for metric_name, detail in signal.signal_breakdown.items():
        translation = METRIC_TRANSLATIONS.get(metric_name, {})
        display_name = translation.get("advanced_name", metric_name)

        # Determine if it supports the signal
        detail_lower = detail.lower()
        supports = False
        if signal.action.value == "LONG" and "bullish" in detail_lower:
            supports = True
        elif signal.action.value == "SHORT" and "bearish" in detail_lower:
            supports = True

        emoji = "✅" if supports else "❌"
        st.write(f"{emoji} **{display_name}**: {detail}")


def render_historical_signals(history: SignalHistory, coin: str, limit: int = 10):
    """Render historical signal performance table"""
    st.markdown("### 📊 Recent Signal Performance")

    recent = history.get_recent_signals(coin, limit)

    if not recent:
        st.info("No historical signals yet. Signals will appear here after they are generated.")
        return

    # Performance stats
    stats = history.get_performance_stats(coin)

    # Show summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Signals", stats['total_signals'])
    with col2:
        if stats['closed_signals'] > 0:
            st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
        else:
            st.metric("Win Rate", "N/A")
    with col3:
        if stats['avg_pnl'] != 0:
            st.metric("Avg P&L", f"{stats['avg_pnl']:+.2f}%")
        else:
            st.metric("Avg P&L", "N/A")
    with col4:
        if stats['best_trade'] != 0:
            st.metric("Best Trade", f"{stats['best_trade']:+.2f}%")
        else:
            st.metric("Best Trade", "N/A")

    # Show table
    st.markdown("#### Recent Signals")

    for sig in recent[:10]:  # Show last 10
        timestamp = datetime.fromisoformat(sig['timestamp']).strftime('%Y-%m-%d %H:%M')

        # Determine status emoji
        if sig['status'] == 'hit_tp':
            status_emoji = "✅"
            status_text = "Hit Target"
        elif sig['status'] == 'hit_sl':
            status_emoji = "❌"
            status_text = "Hit Stop"
        elif sig['status'] == 'expired':
            status_emoji = "⏱️"
            status_text = "Expired"
        else:
            status_emoji = "🔵"
            status_text = "Active"

        # Action emoji
        if sig['action'] == 'LONG':
            action_emoji = "🟢"
        elif sig['action'] == 'SHORT':
            action_emoji = "🔴"
        else:
            action_emoji = "⚪"

        # Build display
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

            with col1:
                st.write(f"{action_emoji} **{sig['action']}** @ ${sig['entry_price']:,.2f}")
                st.caption(timestamp)

            with col2:
                st.write(f"Score: {sig['convergence_score']}/100")
                st.caption(f"{sig['confidence']} ({sig['aligned_signals']} signals)")

            with col3:
                st.write(f"{status_emoji} {status_text}")
                if sig['exit_price']:
                    st.caption(f"Exit: ${sig['exit_price']:,.2f}")

            with col4:
                if sig['pnl_percent'] is not None:
                    color = "green" if sig['pnl_percent'] > 0 else "red"
                    st.markdown(f"<span style='color: {color}; font-weight: bold; font-size: 16px;'>{sig['pnl_percent']:+.2f}%</span>", unsafe_allow_html=True)
                else:
                    st.write("Pending")

            st.markdown("---")


def render_cross_coin_comparison(coins: list, current_coin: str):
    """Render comparison of signals across all coins"""
    st.markdown("### 📈 Cross-Coin Comparison")

    # Fetch signals for all coins in parallel
    async def fetch_all_signals():
        tasks = []
        async with HyperliquidClient() as client:
            for coin in coins:
                tasks.append(fetch_and_analyze(coin))
            return await asyncio.gather(*tasks, return_exceptions=True)

    try:
        results = asyncio.run(fetch_all_signals())

        # Build comparison data
        comparison_data = []
        for i, coin in enumerate(coins):
            result = results[i]
            if isinstance(result, Exception):
                continue

            signal = result['signal']
            comparison_data.append({
                'coin': coin,
                'action': signal.action.value,
                'score': signal.convergence_score,
                'confidence': signal.confidence.value,
                'aligned': signal.aligned_signals
            })

        # Sort by score
        comparison_data.sort(key=lambda x: x['score'], reverse=True)

        # Display
        for data in comparison_data:
            is_current = data['coin'] == current_coin

            # Action emoji
            if data['action'] == 'LONG':
                emoji = "🟢"
            elif data['action'] == 'SHORT':
                emoji = "🔴"
            else:
                emoji = "⚪"

            # Strength bar
            strength_bar = render_strength_bar(data['score'])

            # Highlight current coin
            if is_current:
                st.info(f"**{emoji} {data['coin']}** - {data['action']} | {strength_bar} | {data['confidence']}")
            else:
                st.write(f"{emoji} **{data['coin']}** - {data['action']} | {strength_bar} | {data['confidence']}")

        # Show strongest setup
        if comparison_data:
            strongest = comparison_data[0]
            st.success(f"💪 **Strongest setup:** {strongest['coin']} with {strongest['score']}/100 score")

    except Exception as e:
        st.error(f"Could not fetch cross-coin comparison: {e}")


def render_risk_reward_visual(signal, is_beginner: bool = False):
    """Render visual risk-reward display"""
    if signal.action.value == "SKIP":
        return

    st.markdown("### 📊 Risk vs Reward")

    entry = signal.entry_price
    stop = signal.stop_loss
    target = signal.take_profit

    risk = abs(entry - stop)
    reward = abs(target - entry)
    rr_ratio = reward / risk if risk > 0 else 0

    # Visual display
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Risk" if not is_beginner else "How much you could lose", f"${risk:,.2f}")
        pct_risk = (risk / entry * 100)
        st.caption(f"{pct_risk:.2f}% of entry")

    with col2:
        st.metric("Reward" if not is_beginner else "How much you could gain", f"${reward:,.2f}")
        pct_reward = (reward / entry * 100)
        st.caption(f"{pct_reward:.2f}% of entry")

    with col3:
        st.metric("R:R Ratio" if not is_beginner else "Risk/Reward Ratio", f"{rr_ratio:.2f}")
        if rr_ratio >= 2:
            st.caption("✅ Good ratio (>2:1)")
        elif rr_ratio >= 1.5:
            st.caption("⚠️ Acceptable ratio")
        else:
            st.caption("❌ Low ratio (<1.5:1)")

    # Simple visual bar
    total_range = risk + reward
    risk_pct = (risk / total_range * 100) if total_range > 0 else 50
    reward_pct = (reward / total_range * 100) if total_range > 0 else 50

    st.markdown(f"""
    <div style='display: flex; width: 100%; height: 40px; border-radius: 5px; overflow: hidden; margin-top: 10px;'>
        <div style='background-color: #F44336; width: {risk_pct}%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;'>
            Risk
        </div>
        <div style='background-color: #4CAF50; width: {reward_pct}%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;'>
            Reward
        </div>
    </div>
    """, unsafe_allow_html=True)

    if is_beginner:
        st.caption("📚 A good trade has at least 2x more potential reward than risk")


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

    # Initialize signal history
    if "signal_history" not in st.session_state:
        st.session_state.signal_history = SignalHistory()

    history = st.session_state.signal_history

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

        # PHASE 2: Natural Language Summary (Beginner mode only)
        if is_beginner:
            st.markdown("## 🤖 What's Happening?")
            summary = generate_natural_summary(result["signal"], result["metrics"], is_beginner=True)
            st.info(summary)
            st.markdown("---")

        # Render signal
        with signal_container:
            render_signal_card(result["signal"], is_beginner=is_beginner)

        # PHASE 3: Risk-Reward Visualization
        if result["signal"].action.value != "SKIP":
            with st.expander("📊 Risk vs Reward Analysis", expanded=is_beginner):
                render_risk_reward_visual(result["signal"], is_beginner=is_beginner)

        # Render metrics
        with metrics_container:
            render_metrics(result["metrics"], is_beginner=is_beginner)

        # PHASE 2: Enhanced Score Breakdown with Visual Bars (Advanced mode)
        if not is_beginner:
            with st.expander("📊 Score Breakdown (Visual)"):
                render_score_breakdown_visual(result["signal"].score_breakdown)

        # PHASE 2: Enhanced Signal Confidence Breakdown
        expander_title = "🔍 How We Got This Signal" if is_beginner else "🔍 Signal Confidence Breakdown"
        expanded_default = is_beginner  # Expanded by default in beginner mode
        with st.expander(expander_title, expanded=expanded_default):
            render_signal_confidence_breakdown(result["signal"], result["metrics"])

        # PHASE 3: Historical Signal Performance
        with st.expander("📈 Signal History & Performance"):
            render_historical_signals(history, coin, limit=10)

            # Auto-save signal to history (only for non-SKIP signals)
            if result["signal"].action.value != "SKIP":
                # Check if this exact signal already exists (by timestamp)
                recent = history.get_recent_signals(coin, limit=1)
                should_save = True
                if recent:
                    last_sig = recent[0]
                    last_time = datetime.fromisoformat(last_sig['timestamp'])
                    time_diff = (datetime.now() - last_time).total_seconds()
                    # Only save if last signal was more than 5 minutes ago
                    if time_diff < 300:
                        should_save = False

                if should_save:
                    history.add_signal(
                        coin=coin,
                        action=result["signal"].action.value,
                        entry_price=result["signal"].entry_price,
                        stop_loss=result["signal"].stop_loss,
                        take_profit=result["signal"].take_profit,
                        convergence_score=result["signal"].convergence_score,
                        confidence=result["signal"].confidence.value,
                        aligned_signals=result["signal"].aligned_signals
                    )

        # PHASE 3: Cross-Coin Comparison (Advanced mode only)
        if not is_beginner and len(config.ui.coins) > 1:
            with st.expander("📊 Compare All Coins"):
                render_cross_coin_comparison(config.ui.coins, coin)

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
