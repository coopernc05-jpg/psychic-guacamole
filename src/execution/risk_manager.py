"""Risk management system."""

from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger

from ..config import Config
from ..market.market_data import Position, Market


class RiskManager:
    """Manages risk across all trading positions."""
    
    def __init__(self, config: Config):
        """Initialize risk manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.total_capital = config.initial_capital
        self.current_exposure = 0.0
    
    def can_open_position(self, position_size: float) -> tuple[bool, str]:
        """Check if a new position can be opened.
        
        Args:
            position_size: Size of proposed position
            
        Returns:
            Tuple of (allowed, reason)
        """
        # Check per-trade limit
        if position_size > self.config.max_position_size:
            return False, f"Position size ${position_size:.2f} exceeds max ${self.config.max_position_size:.2f}"
        
        # Check total exposure limit
        if self.current_exposure + position_size > self.config.max_total_exposure:
            return False, f"Would exceed max exposure ${self.config.max_total_exposure:.2f}"
        
        # Check available capital
        if position_size > self.total_capital:
            return False, f"Insufficient capital (need ${position_size:.2f}, have ${self.total_capital:.2f})"
        
        return True, "OK"
    
    def add_position(self, position: Position):
        """Add a position to risk tracking.
        
        Args:
            position: Position to track
        """
        self.positions[position.position_id] = position
        self.current_exposure += position.entry_price * position.size
        logger.info(
            f"Added position {position.position_id}: {position.outcome} @ {position.entry_price:.3f}, "
            f"Current exposure: ${self.current_exposure:.2f}"
        )
    
    def remove_position(self, position_id: str):
        """Remove a position from risk tracking.
        
        Args:
            position_id: Position ID to remove
        """
        if position_id in self.positions:
            position = self.positions[position_id]
            self.current_exposure -= position.entry_price * position.size
            
            # Update capital with realized P&L
            if position.realized_pnl:
                self.total_capital += position.realized_pnl
            
            del self.positions[position_id]
            logger.info(f"Removed position {position_id}, Current exposure: ${self.current_exposure:.2f}")
    
    def update_position_prices(self, market_prices: Dict[str, Market]):
        """Update current prices for all positions.
        
        Args:
            market_prices: Dictionary mapping market_id to Market object
        """
        for position in self.positions.values():
            if position.market_id in market_prices:
                market = market_prices[position.market_id]
                if position.outcome == "YES":
                    position.current_price = market.yes_price
                else:
                    position.current_price = market.no_price
    
    def check_stop_losses(self) -> list[str]:
        """Check if any positions should be stopped out.
        
        Returns:
            List of position IDs that should be closed
        """
        to_close = []
        
        for position_id, position in self.positions.items():
            # Calculate loss percentage
            if position.current_price > 0:
                loss_pct = (position.entry_price - position.current_price) / position.entry_price
                
                if loss_pct > self.config.stop_loss_percentage:
                    logger.warning(
                        f"Stop loss triggered for {position_id}: "
                        f"loss {loss_pct*100:.2f}% > {self.config.stop_loss_percentage*100:.2f}%"
                    )
                    to_close.append(position_id)
        
        return to_close
    
    def check_position_age(self) -> list[str]:
        """Check if any positions are too old and should be closed.
        
        Returns:
            List of position IDs that should be closed
        """
        to_close = []
        max_age = timedelta(hours=self.config.max_position_age_hours)
        now = datetime.now()
        
        for position_id, position in self.positions.items():
            age = now - position.entry_time
            
            if age > max_age:
                logger.warning(
                    f"Position {position_id} exceeded max age: "
                    f"{age.total_seconds()/3600:.1f}h > {self.config.max_position_age_hours}h"
                )
                to_close.append(position_id)
        
        return to_close
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Calculate current risk metrics.
        
        Returns:
            Dictionary of risk metrics
        """
        total_unrealized_pnl = sum(
            p.unrealized_pnl for p in self.positions.values()
        )
        
        exposure_pct = (self.current_exposure / self.total_capital * 100) if self.total_capital > 0 else 0
        
        return {
            "total_capital": self.total_capital,
            "current_exposure": self.current_exposure,
            "exposure_percentage": exposure_pct,
            "open_positions": len(self.positions),
            "total_unrealized_pnl": total_unrealized_pnl,
            "available_capital": self.total_capital - self.current_exposure
        }
    
    def get_diversification_score(self) -> float:
        """Calculate diversification score across positions.
        
        Returns:
            Diversification score (0-100, higher is better)
        """
        if not self.positions:
            return 100.0
        
        # Count unique markets
        unique_markets = len(set(p.market_id for p in self.positions.values()))
        
        # More markets = better diversification
        score = min(unique_markets / 10 * 100, 100)
        
        return score
