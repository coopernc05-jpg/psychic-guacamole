"""Logging system for opportunities and executions."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from ..arbitrage.scorer import ScoredOpportunity
from ..market.market_data import Trade, Position


class OpportunityLogger:
    """Logs all detected arbitrage opportunities."""

    def __init__(self, log_dir: str = "data/opportunities"):
        """Initialize opportunity logger.

        Args:
            log_dir: Directory to store opportunity logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.opportunities: list[Dict[str, Any]] = []

    def log_opportunity(self, scored_opportunity: ScoredOpportunity):
        """Log a detected opportunity.

        Args:
            scored_opportunity: Scored opportunity to log
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "opportunity_type": scored_opportunity.opportunity.__class__.__name__,
            "details": str(scored_opportunity.opportunity),
            "score": scored_opportunity.score,
            "profit_score": scored_opportunity.profit_score,
            "capital_efficiency": scored_opportunity.capital_efficiency_score,
            "confidence": scored_opportunity.confidence_score,
            "risk": scored_opportunity.risk_score,
            "execution_difficulty": scored_opportunity.execution_difficulty,
        }

        self.opportunities.append(entry)

        # Write to daily log file
        log_file = (
            self.log_dir / f"opportunities_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about logged opportunities.

        Returns:
            Dictionary of statistics
        """
        if not self.opportunities:
            return {
                "total_opportunities": 0,
                "by_type": {},
                "avg_score": 0,
                "avg_profit_score": 0,
            }

        # Count by type
        by_type = {}
        for opp in self.opportunities:
            opp_type = opp["opportunity_type"]
            by_type[opp_type] = by_type.get(opp_type, 0) + 1

        # Calculate averages
        avg_score = sum(opp["score"] for opp in self.opportunities) / len(
            self.opportunities
        )
        avg_profit = sum(opp["profit_score"] for opp in self.opportunities) / len(
            self.opportunities
        )

        return {
            "total_opportunities": len(self.opportunities),
            "by_type": by_type,
            "avg_score": avg_score,
            "avg_profit_score": avg_profit,
        }


class ExecutionLogger:
    """Logs all executed trades and positions."""

    def __init__(self, log_dir: str = "data/executions"):
        """Initialize execution logger.

        Args:
            log_dir: Directory to store execution logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.trades: list[Dict[str, Any]] = []
        self.positions: list[Dict[str, Any]] = []

    def log_trade(self, trade: Trade):
        """Log an executed trade.

        Args:
            trade: Trade to log
        """
        entry = {
            "timestamp": trade.timestamp.isoformat(),
            "trade_id": trade.trade_id,
            "market_id": trade.market_id,
            "outcome": trade.outcome,
            "side": trade.side.value,
            "price": trade.price,
            "size": trade.size,
            "gas_cost": trade.gas_cost,
            "total_cost": trade.total_cost,
        }

        self.trades.append(entry)

        # Write to daily log file
        log_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_position_close(self, position: Position):
        """Log a closed position.

        Args:
            position: Closed position to log
        """
        entry = {
            "position_id": position.position_id,
            "market_id": position.market_id,
            "outcome": position.outcome,
            "size": position.size,
            "entry_price": position.entry_price,
            "entry_time": position.entry_time.isoformat(),
            "exit_price": position.exit_price,
            "exit_time": position.exit_time.isoformat() if position.exit_time else None,
            "realized_pnl": position.realized_pnl,
            "return_pct": position.return_pct,
            "gas_costs": position.gas_costs,
            "hold_duration_hours": (
                (position.exit_time - position.entry_time).total_seconds() / 3600
                if position.exit_time
                else None
            ),
        }

        self.positions.append(entry)

        # Write to daily log file
        log_file = self.log_dir / f"positions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_trade_statistics(self) -> Dict[str, Any]:
        """Get statistics about executed trades.

        Returns:
            Dictionary of statistics
        """
        if not self.trades:
            return {"total_trades": 0, "total_volume": 0, "total_gas_costs": 0}

        return {
            "total_trades": len(self.trades),
            "total_volume": sum(t["size"] for t in self.trades),
            "total_gas_costs": sum(t["gas_cost"] for t in self.trades),
            "avg_trade_size": sum(t["size"] for t in self.trades) / len(self.trades),
        }

    def get_position_statistics(self) -> Dict[str, Any]:
        """Get statistics about closed positions.

        Returns:
            Dictionary of statistics
        """
        if not self.positions:
            return {
                "total_positions": 0,
                "winning_positions": 0,
                "losing_positions": 0,
                "total_pnl": 0,
                "win_rate": 0,
            }

        winning = [p for p in self.positions if p.get("realized_pnl", 0) > 0]
        losing = [p for p in self.positions if p.get("realized_pnl", 0) < 0]

        return {
            "total_positions": len(self.positions),
            "winning_positions": len(winning),
            "losing_positions": len(losing),
            "total_pnl": sum(p.get("realized_pnl", 0) for p in self.positions),
            "win_rate": (
                len(winning) / len(self.positions) * 100 if self.positions else 0
            ),
            "avg_return_pct": (
                sum(p.get("return_pct", 0) for p in self.positions)
                / len(self.positions)
                if self.positions
                else 0
            ),
        }
