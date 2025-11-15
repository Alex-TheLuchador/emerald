"""
Signal history storage and tracking

Simple JSON-based persistence for signal history and performance tracking
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class SignalHistory:
    """Track historical signals and their outcomes"""

    def __init__(self, storage_path: str = ".emerald_history.json"):
        """
        Initialize signal history tracker

        Args:
            storage_path: Path to JSON storage file
        """
        self.storage_path = Path(storage_path)
        self.signals: Dict[str, List[Dict[str, Any]]] = {}
        self._load()

    def _load(self):
        """Load history from disk"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.signals = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load signal history: {e}")
                self.signals = {}
        else:
            self.signals = {}

    def _save(self):
        """Save history to disk"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.signals, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save signal history: {e}")

    def add_signal(
        self,
        coin: str,
        action: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        convergence_score: int,
        confidence: str,
        aligned_signals: int
    ) -> str:
        """
        Add a new signal to history

        Args:
            coin: Coin symbol
            action: LONG, SHORT, or SKIP
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            convergence_score: Score 0-100
            confidence: HIGH, MEDIUM, LOW
            aligned_signals: Number of aligned signals

        Returns:
            signal_id: Unique ID for this signal
        """
        if coin not in self.signals:
            self.signals[coin] = []

        signal_id = f"{coin}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        signal_record = {
            "signal_id": signal_id,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "convergence_score": convergence_score,
            "confidence": confidence,
            "aligned_signals": aligned_signals,
            "status": "active",  # active, hit_tp, hit_sl, expired
            "exit_price": None,
            "pnl_percent": None,
            "exit_timestamp": None
        }

        self.signals[coin].append(signal_record)

        # Keep only last 100 signals per coin
        if len(self.signals[coin]) > 100:
            self.signals[coin] = self.signals[coin][-100:]

        self._save()
        return signal_id

    def update_signal(
        self,
        signal_id: str,
        exit_price: float,
        status: str
    ):
        """
        Update signal with exit information

        Args:
            signal_id: Signal ID to update
            exit_price: Exit price
            status: hit_tp, hit_sl, or expired
        """
        coin = signal_id.split('_')[0]

        if coin not in self.signals:
            return

        for signal in self.signals[coin]:
            if signal['signal_id'] == signal_id:
                signal['exit_price'] = exit_price
                signal['status'] = status
                signal['exit_timestamp'] = datetime.now().isoformat()

                # Calculate P&L
                entry = signal['entry_price']
                if signal['action'] == 'LONG':
                    signal['pnl_percent'] = ((exit_price - entry) / entry) * 100
                elif signal['action'] == 'SHORT':
                    signal['pnl_percent'] = ((entry - exit_price) / entry) * 100
                else:
                    signal['pnl_percent'] = 0

                self._save()
                break

    def get_recent_signals(self, coin: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent signals for a coin

        Args:
            coin: Coin symbol
            limit: Number of signals to return

        Returns:
            List of signal records (newest first)
        """
        if coin not in self.signals:
            return []

        return list(reversed(self.signals[coin][-limit:]))

    def get_performance_stats(self, coin: str) -> Dict[str, Any]:
        """
        Calculate performance statistics for a coin

        Args:
            coin: Coin symbol

        Returns:
            Performance statistics dictionary
        """
        if coin not in self.signals:
            return {
                "total_signals": 0,
                "profitable_signals": 0,
                "losing_signals": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0
            }

        closed_signals = [s for s in self.signals[coin] if s['status'] in ['hit_tp', 'hit_sl'] and s['pnl_percent'] is not None]

        if not closed_signals:
            return {
                "total_signals": len(self.signals[coin]),
                "profitable_signals": 0,
                "losing_signals": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0
            }

        pnls = [s['pnl_percent'] for s in closed_signals]
        profitable = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p < 0]

        return {
            "total_signals": len(self.signals[coin]),
            "closed_signals": len(closed_signals),
            "profitable_signals": len(profitable),
            "losing_signals": len(losing),
            "win_rate": (len(profitable) / len(closed_signals) * 100) if closed_signals else 0.0,
            "avg_pnl": sum(pnls) / len(pnls) if pnls else 0.0,
            "best_trade": max(pnls) if pnls else 0.0,
            "worst_trade": min(pnls) if pnls else 0.0
        }

    def get_all_coins_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance summary for all coins

        Returns:
            Dictionary mapping coin -> performance stats
        """
        return {
            coin: self.get_performance_stats(coin)
            for coin in self.signals.keys()
        }
