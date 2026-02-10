"""Performance tracking and analytics."""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..market.market_data import Trade, Position


@dataclass
class PerformanceMetrics:
    """Performance metrics summary."""

    total_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit_per_trade: float
    total_gas_costs: float
    net_pnl: float
    roi: float
    sharpe_ratio: float
    max_drawdown: float
    total_volume: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_pnl": round(self.total_pnl, 2),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(self.win_rate, 2),
            "avg_profit_per_trade": round(self.avg_profit_per_trade, 2),
            "total_gas_costs": round(self.total_gas_costs, 2),
            "net_pnl": round(self.net_pnl, 2),
            "roi": round(self.roi, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "total_volume": round(self.total_volume, 2),
        }


class PerformanceTracker:
    """Tracks and calculates performance metrics."""

    def __init__(self, initial_capital: float):
        """Initialize performance tracker.

        Args:
            initial_capital: Initial capital amount
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades: List[Trade] = []
        self.closed_positions: List[Position] = []
        self.daily_returns: List[float] = []
        self.equity_curve: List[tuple[datetime, float]] = [
            (datetime.now(), initial_capital)
        ]

    def add_trade(self, trade: Trade):
        """Add a trade to tracking.

        Args:
            trade: Trade to add
        """
        self.trades.append(trade)

    def add_closed_position(self, position: Position):
        """Add a closed position to tracking.

        Args:
            position: Closed position to add
        """
        if position.realized_pnl is not None:
            self.closed_positions.append(position)
            self.current_capital += position.realized_pnl
            self.equity_curve.append((datetime.now(), self.current_capital))

            # Calculate daily return
            if len(self.equity_curve) > 1:
                prev_capital = self.equity_curve[-2][1]
                daily_return = (self.current_capital - prev_capital) / prev_capital
                self.daily_returns.append(daily_return)

    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics.

        Returns:
            PerformanceMetrics object
        """
        # Trade statistics
        total_trades = len(self.closed_positions)
        if total_trades == 0:
            return PerformanceMetrics(
                total_pnl=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                avg_profit_per_trade=0,
                total_gas_costs=0,
                net_pnl=0,
                roi=0,
                sharpe_ratio=0,
                max_drawdown=0,
                total_volume=0,
            )

        # Winning/losing trades
        winning_trades = len([p for p in self.closed_positions if p.realized_pnl > 0])
        losing_trades = len([p for p in self.closed_positions if p.realized_pnl < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        # P&L
        total_pnl = sum(p.realized_pnl for p in self.closed_positions)
        total_gas_costs = sum(t.gas_cost for t in self.trades)
        net_pnl = total_pnl - total_gas_costs

        # Average profit per trade
        avg_profit = net_pnl / total_trades if total_trades > 0 else 0

        # ROI
        roi = (net_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0

        # Sharpe ratio
        sharpe = self._calculate_sharpe_ratio()

        # Max drawdown
        max_dd = self._calculate_max_drawdown()

        # Total volume
        total_volume = sum(t.price * t.size for t in self.trades)

        return PerformanceMetrics(
            total_pnl=total_pnl,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit_per_trade=avg_profit,
            total_gas_costs=total_gas_costs,
            net_pnl=net_pnl,
            roi=roi,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            total_volume=total_volume,
        )

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio.

        Args:
            risk_free_rate: Annual risk-free rate (default 2%)

        Returns:
            Sharpe ratio
        """
        if len(self.daily_returns) < 2:
            return 0.0

        returns = np.array(self.daily_returns)

        # Calculate daily risk-free rate
        daily_rf = risk_free_rate / 252  # Assuming 252 trading days

        # Excess returns
        excess_returns = returns - daily_rf

        # Sharpe ratio
        if np.std(excess_returns) == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / np.std(excess_returns)

        # Annualize (assuming daily returns)
        sharpe_annualized = sharpe * np.sqrt(252)

        return sharpe_annualized

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown.

        Returns:
            Maximum drawdown as percentage
        """
        if len(self.equity_curve) < 2:
            return 0.0

        equity_values = [eq[1] for eq in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0.0

        for value in equity_values:
            if value > peak:
                peak = value

            drawdown = (peak - value) / peak * 100
            max_dd = max(max_dd, drawdown)

        return max_dd

    def get_market_statistics(self) -> Dict[str, Any]:
        """Get statistics about market performance.

        Returns:
            Dictionary of market statistics
        """
        if not self.closed_positions:
            return {
                "most_profitable_market": None,
                "least_profitable_market": None,
                "markets_traded": 0,
            }

        # Group by market
        market_pnl = {}
        for position in self.closed_positions:
            market_id = position.market_id
            if market_id not in market_pnl:
                market_pnl[market_id] = 0
            market_pnl[market_id] += position.realized_pnl

        if not market_pnl:
            return {
                "most_profitable_market": None,
                "least_profitable_market": None,
                "markets_traded": 0,
            }

        most_profitable = max(market_pnl.items(), key=lambda x: x[1])
        least_profitable = min(market_pnl.items(), key=lambda x: x[1])

        return {
            "most_profitable_market": {
                "market_id": most_profitable[0],
                "pnl": most_profitable[1],
            },
            "least_profitable_market": {
                "market_id": least_profitable[0],
                "pnl": least_profitable[1],
            },
            "markets_traded": len(market_pnl),
        }

    def generate_report(self) -> str:
        """Generate a comprehensive performance report.

        Returns:
            Formatted report string
        """
        metrics = self.calculate_metrics()
        market_stats = self.get_market_statistics()

        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE REPORT")
        report.append("=" * 80)
        report.append("")
        report.append("Overall Performance:")
        report.append(f"  Initial Capital: ${self.initial_capital:,.2f}")
        report.append(f"  Current Capital: ${self.current_capital:,.2f}")
        report.append(f"  Net P&L: ${metrics.net_pnl:,.2f}")
        report.append(f"  ROI: {metrics.roi:.2f}%")
        report.append("")
        report.append("Trading Statistics:")
        report.append(f"  Total Trades: {metrics.total_trades}")
        report.append(f"  Winning Trades: {metrics.winning_trades}")
        report.append(f"  Losing Trades: {metrics.losing_trades}")
        report.append(f"  Win Rate: {metrics.win_rate:.2f}%")
        report.append(f"  Avg Profit/Trade: ${metrics.avg_profit_per_trade:.2f}")
        report.append(f"  Total Volume: ${metrics.total_volume:,.2f}")
        report.append("")
        report.append("Risk Metrics:")
        report.append(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        report.append(f"  Max Drawdown: {metrics.max_drawdown:.2f}%")
        report.append(f"  Total Gas Costs: ${metrics.total_gas_costs:.2f}")
        report.append("")
        report.append("Market Statistics:")
        report.append(f"  Markets Traded: {market_stats['markets_traded']}")
        report.append("=" * 80)

        return "\n".join(report)
