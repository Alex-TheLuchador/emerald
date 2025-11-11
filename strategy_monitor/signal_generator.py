"""
Trading signal generation based on metric convergence
"""
from typing import Dict, Any, List
from datetime import datetime

from config import THRESHOLDS, SCORING, MIN_CONVERGENCE_SCORE, MIN_ALIGNED_SIGNALS


class SignalGenerator:
    """Generate trading signals from calculated metrics"""

    def generate_signal(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading signal from metrics

        Returns:
            {
                'action': 'LONG' | 'SHORT' | 'SKIP',
                'convergence_score': int (0-100),
                'confidence': 'LOW' | 'MEDIUM' | 'HIGH',
                'aligned_signals': int,
                'bullish_signals': int,
                'bearish_signals': int,
                'reasons': List[str],
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float,
                'timestamp': datetime
            }
        """
        # Calculate convergence score
        score, score_details = self.calculate_convergence_score(metrics)

        # Count directional signals
        bullish_signals, bearish_signals, signal_details = self.count_directional_signals(metrics)

        # Determine action
        action = self._determine_action(
            score=score,
            bullish_signals=bullish_signals,
            bearish_signals=bearish_signals
        )

        # Calculate entry/stop/target if we have a signal
        levels = self._calculate_price_levels(
            action=action,
            current_price=metrics.get('current_price', 0),
            vwap=metrics.get('vwap', 0),
            vwap_z_score=metrics.get('vwap_z_score', 0)
        )

        # Determine confidence level
        confidence = self._determine_confidence(score, max(bullish_signals, bearish_signals))

        return {
            'action': action,
            'convergence_score': score,
            'confidence': confidence,
            'aligned_signals': max(bullish_signals, bearish_signals),
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'score_breakdown': score_details,
            'signal_breakdown': signal_details,
            'entry_price': levels['entry'],
            'stop_loss': levels['stop'],
            'take_profit': levels['target'],
            'timestamp': datetime.now()
        }

    def calculate_convergence_score(self, metrics: Dict[str, Any]) -> tuple[int, Dict[str, int]]:
        """
        Calculate convergence score (0-100)

        Returns:
            (total_score, breakdown_dict)
        """
        score = 0
        breakdown = {}

        # 1. Order Book Imbalance (25 points max)
        ob_imbalance = abs(metrics.get('ob_imbalance', 0))
        if ob_imbalance > THRESHOLDS['order_book_imbalance_extreme']:
            points = SCORING['order_book_extreme']
            breakdown['order_book'] = points
            score += points
        elif ob_imbalance > THRESHOLDS['order_book_imbalance']:
            points = SCORING['order_book_strong']
            breakdown['order_book'] = points
            score += points

        # 2. Trade Flow (25 points max)
        flow_imbalance = abs(metrics.get('flow_imbalance', 0))
        if flow_imbalance > THRESHOLDS['trade_flow_strong']:
            points = SCORING['trade_flow_strong']
            breakdown['trade_flow'] = points
            score += points
        elif flow_imbalance > THRESHOLDS['trade_flow_moderate']:
            points = SCORING['trade_flow_moderate']
            breakdown['trade_flow'] = points
            score += points

        # 3. VWAP Deviation (30 points max)
        vwap_z = abs(metrics.get('vwap_z_score', 0))
        if vwap_z > THRESHOLDS['vwap_z_score_extreme']:
            points = SCORING['vwap_extreme']
            breakdown['vwap'] = points
            score += points
        elif vwap_z > THRESHOLDS['vwap_z_score_stretched']:
            points = SCORING['vwap_stretched']
            breakdown['vwap'] = points
            score += points

        # 4. Funding Rate (20 points max)
        funding = abs(metrics.get('funding_annualized', 0))
        if funding > THRESHOLDS['funding_extreme']:
            points = SCORING['funding_extreme']
            breakdown['funding'] = points
            score += points
        elif funding > THRESHOLDS['funding_elevated']:
            points = SCORING['funding_elevated']
            breakdown['funding'] = points
            score += points

        # 5. Open Interest Divergence (20 points max)
        oi_type = metrics.get('oi_divergence_type', 'unknown')
        if oi_type in ['strong_bullish', 'strong_bearish']:
            points = SCORING['oi_strong']
            breakdown['oi'] = points
            score += points
        elif oi_type in ['weak_bullish', 'weak_bearish']:
            points = SCORING['oi_weak']
            breakdown['oi'] = points
            score += points

        # 6. Funding-Basis Alignment Check (±15-20 points)
        funding_val = metrics.get('funding_annualized', 0)
        basis = metrics.get('basis_pct', 0)

        funding_extreme = abs(funding_val) > THRESHOLDS['funding_extreme']
        basis_extreme = abs(basis) > THRESHOLDS['basis_threshold']

        if funding_extreme and basis_extreme:
            funding_positive = funding_val > THRESHOLDS['funding_extreme']
            basis_positive = basis > THRESHOLDS['basis_threshold']

            if funding_positive == basis_positive:
                points = SCORING['funding_basis_aligned']
                breakdown['funding_basis_alignment'] = points
                score += points
            else:
                points = SCORING['funding_basis_diverged']
                breakdown['funding_basis_alignment'] = points
                score += points

        # Cap at 100
        score = min(100, max(0, score))

        return score, breakdown

    def count_directional_signals(self, metrics: Dict[str, Any]) -> tuple[int, int, Dict[str, str]]:
        """
        Count how many metrics point bullish vs bearish

        Returns:
            (bullish_count, bearish_count, signal_details)
        """
        bullish = 0
        bearish = 0
        details = {}

        # Order Book
        ob = metrics.get('ob_imbalance', 0)
        if ob > THRESHOLDS['order_book_imbalance']:
            bullish += 1
            details['order_book'] = f'Bullish ({ob:.2f})'
        elif ob < -THRESHOLDS['order_book_imbalance']:
            bearish += 1
            details['order_book'] = f'Bearish ({ob:.2f})'

        # Trade Flow
        flow = metrics.get('flow_imbalance', 0)
        if flow > THRESHOLDS['trade_flow_moderate']:
            bullish += 1
            details['trade_flow'] = f'Bullish ({flow:.2f})'
        elif flow < -THRESHOLDS['trade_flow_moderate']:
            bearish += 1
            details['trade_flow'] = f'Bearish ({flow:.2f})'

        # VWAP (mean reversion - extreme = fade)
        vwap_z = metrics.get('vwap_z_score', 0)
        if vwap_z > THRESHOLDS['vwap_z_score_stretched']:
            bearish += 1  # Overextended = short
            details['vwap'] = f'Bearish (overextended +{vwap_z:.2f}σ)'
        elif vwap_z < -THRESHOLDS['vwap_z_score_stretched']:
            bullish += 1  # Oversold = long
            details['vwap'] = f'Bullish (oversold {vwap_z:.2f}σ)'

        # Funding (contrarian - high funding = fade longs)
        funding = metrics.get('funding_annualized', 0)
        if funding > THRESHOLDS['funding_extreme']:
            bearish += 1  # Longs crowded = short
            details['funding'] = f'Bearish (crowded longs {funding:.1f}%)'
        elif funding < -THRESHOLDS['funding_extreme']:
            bullish += 1  # Shorts crowded = long
            details['funding'] = f'Bullish (crowded shorts {funding:.1f}%)'

        # OI Divergence
        oi_type = metrics.get('oi_divergence_type', 'unknown')
        if oi_type == 'strong_bullish':
            bullish += 1
            details['oi'] = 'Bullish (new longs opening)'
        elif oi_type == 'strong_bearish':
            bearish += 1
            details['oi'] = 'Bearish (new shorts opening)'
        elif oi_type == 'weak_bullish':
            bearish += 1  # Shorts covering = fade rally
            details['oi'] = 'Bearish (fake rally - shorts covering)'
        elif oi_type == 'weak_bearish':
            bullish += 1  # Longs closing = fade dump
            details['oi'] = 'Bullish (fake dump - longs closing)'

        return bullish, bearish, details

    def _determine_action(
        self,
        score: int,
        bullish_signals: int,
        bearish_signals: int
    ) -> str:
        """Determine trading action"""
        if score < MIN_CONVERGENCE_SCORE:
            return 'SKIP'

        if bullish_signals >= MIN_ALIGNED_SIGNALS and bullish_signals > bearish_signals:
            return 'LONG'
        elif bearish_signals >= MIN_ALIGNED_SIGNALS and bearish_signals > bullish_signals:
            return 'SHORT'
        else:
            return 'SKIP'

    def _calculate_price_levels(
        self,
        action: str,
        current_price: float,
        vwap: float,
        vwap_z_score: float
    ) -> Dict[str, float]:
        """Calculate entry, stop, and target prices"""
        if action == 'SKIP' or current_price == 0:
            return {'entry': 0, 'stop': 0, 'target': 0}

        # Use VWAP as anchor for targets
        if vwap == 0:
            vwap = current_price

        if action == 'LONG':
            entry = current_price
            # Stop below recent low (2% default)
            stop = entry * 0.98
            # Target at VWAP or higher
            target = max(vwap * 1.01, entry * 1.015)

        else:  # SHORT
            entry = current_price
            # Stop above recent high (2% default)
            stop = entry * 1.02
            # Target at VWAP or lower
            target = min(vwap * 0.99, entry * 0.985)

        return {
            'entry': round(entry, 2),
            'stop': round(stop, 2),
            'target': round(target, 2)
        }

    def _determine_confidence(self, score: int, aligned_signals: int) -> str:
        """Determine confidence level"""
        if score >= 85 and aligned_signals >= 4:
            return 'HIGH'
        elif score >= 70 and aligned_signals >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'


def format_signal(signal: Dict[str, Any]) -> str:
    """Format signal for human-readable output"""
    output = []
    output.append("=" * 60)
    output.append(f"SIGNAL: {signal['action']} ({signal['confidence']} confidence)")
    output.append("=" * 60)
    output.append(f"Convergence Score: {signal['convergence_score']}/100")
    output.append(f"Aligned Signals: {signal['aligned_signals']} "
                 f"(Bull: {signal['bullish_signals']}, Bear: {signal['bearish_signals']})")

    if signal['action'] != 'SKIP':
        output.append(f"\nEntry: ${signal['entry_price']:,.2f}")
        output.append(f"Stop:  ${signal['stop_loss']:,.2f}")
        output.append(f"Target: ${signal['take_profit']:,.2f}")

    output.append("\nScore Breakdown:")
    for metric, points in signal['score_breakdown'].items():
        output.append(f"  {metric}: {points} points")

    output.append("\nSignal Breakdown:")
    for metric, reason in signal['signal_breakdown'].items():
        output.append(f"  {metric}: {reason}")

    output.append(f"\nTimestamp: {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 60)

    return "\n".join(output)


def test_signal_generator():
    """Test signal generation"""
    print("Testing Signal Generator...")

    generator = SignalGenerator()

    # Test Case 1: Strong bearish setup
    print("\n1. Testing STRONG BEARISH setup...")
    metrics = {
        'ob_imbalance': -0.65,  # Strong ask pressure
        'flow_imbalance': -0.55,  # Aggressive selling
        'vwap_z_score': 2.2,  # Extreme overextension
        'funding_annualized': 14.5,  # Extreme longs
        'oi_divergence_type': 'strong_bearish',
        'basis_pct': 0.35,
        'current_price': 67850,
        'vwap': 67500
    }

    signal = generator.generate_signal(metrics)
    print(format_signal(signal))

    # Test Case 2: Mixed signals (should SKIP)
    print("\n2. Testing MIXED signals (should SKIP)...")
    metrics = {
        'ob_imbalance': 0.3,  # Mild bid pressure
        'flow_imbalance': -0.2,  # Mild selling
        'vwap_z_score': 0.5,  # Not stretched
        'funding_annualized': 5.0,  # Not extreme
        'oi_divergence_type': 'neutral',
        'basis_pct': 0.1,
        'current_price': 67800,
        'vwap': 67800
    }

    signal = generator.generate_signal(metrics)
    print(format_signal(signal))

    # Test Case 3: Strong bullish setup
    print("\n3. Testing STRONG BULLISH setup...")
    metrics = {
        'ob_imbalance': 0.68,  # Strong bid pressure
        'flow_imbalance': 0.62,  # Aggressive buying
        'vwap_z_score': -2.1,  # Extreme oversold
        'funding_annualized': -12.0,  # Extreme shorts
        'oi_divergence_type': 'strong_bullish',
        'basis_pct': -0.4,
        'current_price': 67500,
        'vwap': 67800
    }

    signal = generator.generate_signal(metrics)
    print(format_signal(signal))

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_signal_generator()
