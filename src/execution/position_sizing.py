"""Position sizing using Kelly Criterion and other strategies."""

import numpy as np
from typing import Optional
from loguru import logger

from ..config import Config


def kelly_criterion(
    win_probability: float, win_return: float, loss_return: float = -1.0
) -> float:
    """Calculate optimal position size using Kelly Criterion.

    Kelly Formula: f* = (bp - q) / b
    where:
    - f* = fraction of capital to bet
    - b = odds received on the bet (win_return)
    - p = probability of winning (win_probability)
    - q = probability of losing (1 - p)

    Args:
        win_probability: Probability of winning (0-1)
        win_return: Return if win (e.g., 1.0 = 100% return)
        loss_return: Return if loss (typically -1.0 = 100% loss)

    Returns:
        Optimal fraction of capital to bet (0-1)
    """
    if win_probability <= 0 or win_probability >= 1:
        return 0.0

    if win_return <= 0:
        return 0.0

    # Kelly formula
    loss_probability = 1 - win_probability
    kelly_fraction = (
        win_probability * win_return - loss_probability * abs(loss_return)
    ) / win_return

    # Kelly fraction should be between 0 and 1
    kelly_fraction = max(0.0, min(1.0, kelly_fraction))

    return kelly_fraction


class PositionSizer:
    """Calculate optimal position sizes for arbitrage opportunities."""

    def __init__(self, config: Config):
        """Initialize position sizer.

        Args:
            config: Configuration object
        """
        self.config = config
        self.strategy = config.position_sizing_strategy
        self.kelly_fraction = config.kelly_fraction

    def calculate_position_size(
        self,
        opportunity_profit_pct: float,
        opportunity_confidence: float,
        available_capital: float,
    ) -> float:
        """Calculate optimal position size for an opportunity.

        Args:
            opportunity_profit_pct: Expected profit percentage
            opportunity_confidence: Confidence in the opportunity (0-1)
            available_capital: Total available capital

        Returns:
            Position size in USD
        """
        if self.strategy == "kelly":
            size = self._kelly_sizing(
                opportunity_profit_pct, opportunity_confidence, available_capital
            )
        elif self.strategy == "fixed":
            size = self._fixed_sizing(available_capital)
        elif self.strategy == "percentage":
            size = self._percentage_sizing(available_capital)
        else:
            logger.warning(f"Unknown sizing strategy: {self.strategy}, using fixed")
            size = self._fixed_sizing(available_capital)

        # Apply max position size limit
        size = min(size, self.config.max_position_size)

        logger.debug(
            f"Position size: ${size:.2f} (strategy: {self.strategy}, "
            f"profit: {opportunity_profit_pct:.2f}%, confidence: {opportunity_confidence:.2f})"
        )

        return size

    def _kelly_sizing(
        self, profit_pct: float, confidence: float, capital: float
    ) -> float:
        """Calculate position size using Kelly Criterion.

        Args:
            profit_pct: Expected profit percentage
            confidence: Confidence in the opportunity (0-1)
            capital: Available capital

        Returns:
            Position size in USD
        """
        # Convert profit percentage to return multiplier
        win_return = profit_pct / 100

        # Use confidence as win probability
        win_probability = confidence

        # For arbitrage, assume downside risk is smaller than upside
        # Loss is typically from slippage, fees, not full position loss
        # Use 20% of the win_return as potential loss
        loss_return = -win_return * 0.2

        # Calculate Kelly fraction
        kelly_f = kelly_criterion(win_probability, win_return, loss_return)

        # Apply additional conservative factor for arbitrage (0.5)
        # This accounts for model uncertainty and execution risks
        kelly_f = kelly_f * 0.5

        # Apply fractional Kelly (more conservative)
        fractional_kelly = kelly_f * self.kelly_fraction

        # Calculate position size
        position_size = capital * fractional_kelly

        return position_size

    def _fixed_sizing(self, capital: float) -> float:
        """Use fixed position size.

        Args:
            capital: Available capital

        Returns:
            Fixed position size
        """
        return min(self.config.max_position_size, capital * 0.1)  # 10% of capital

    def _percentage_sizing(self, capital: float) -> float:
        """Use percentage-based position sizing.

        Args:
            capital: Available capital

        Returns:
            Position size as percentage of capital
        """
        percentage = 0.05  # 5% of capital per trade
        return capital * percentage


class CapitalAllocator:
    """Allocates capital across multiple opportunities."""

    def __init__(self, config: Config):
        """Initialize capital allocator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.position_sizer = PositionSizer(config)

    def allocate_capital(
        self, opportunities: list, total_capital: float, current_exposure: float
    ) -> dict:
        """Allocate capital across multiple opportunities.

        Args:
            opportunities: List of scored opportunities
            total_capital: Total available capital
            current_exposure: Current capital already allocated

        Returns:
            Dictionary mapping opportunity index to position size
        """
        allocation = {}
        remaining_capital = total_capital - current_exposure

        # Check total exposure limit
        if current_exposure >= self.config.max_total_exposure:
            logger.warning("Maximum total exposure reached, no new positions")
            return allocation

        # Allocate to opportunities in order of score
        for i, scored_opp in enumerate(opportunities):
            if remaining_capital <= 0:
                break

            # Get opportunity details
            profit_pct = scored_opp.profit_score
            confidence = scored_opp.confidence_score / 100

            # Calculate position size
            position_size = self.position_sizer.calculate_position_size(
                profit_pct, confidence, remaining_capital
            )

            # Don't exceed remaining capital or exposure limit
            max_allowed = min(
                remaining_capital, self.config.max_total_exposure - current_exposure
            )
            position_size = min(position_size, max_allowed)

            if position_size > 0:
                allocation[i] = position_size
                remaining_capital -= position_size
                current_exposure += position_size

        logger.info(
            f"Allocated capital to {len(allocation)} opportunities, "
            f"total allocated: ${sum(allocation.values()):.2f}"
        )

        return allocation
