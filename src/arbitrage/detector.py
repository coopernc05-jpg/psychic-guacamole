"""Main arbitrage detection engine."""

from typing import List, Union
from loguru import logger

from ..config import Config
from ..market.market_data import Market
from .strategies import (
    CrossMarketStrategy,
    YesNoImbalanceStrategy,
    MultiLegStrategy,
    CorrelatedEventsStrategy,
    OrderBookSpreadStrategy,
    TimeBasedStrategy,
    CrossMarketOpportunity,
    YesNoImbalanceOpportunity,
    MultiLegOpportunity,
    CorrelatedEventsOpportunity,
    OrderBookSpreadOpportunity,
    TimeBasedOpportunity,
)

# Type alias for all opportunity types
Opportunity = Union[
    CrossMarketOpportunity,
    YesNoImbalanceOpportunity,
    MultiLegOpportunity,
    CorrelatedEventsOpportunity,
    OrderBookSpreadOpportunity,
    TimeBasedOpportunity,
]


class ArbitrageDetector:
    """Main arbitrage detection engine that coordinates all strategies."""

    def __init__(self, config: Config):
        """Initialize the arbitrage detector.

        Args:
            config: Configuration object
        """
        self.config = config
        self.strategies = []

        # Initialize enabled strategies
        if "cross_market" in config.strategies:
            self.strategies.append(
                CrossMarketStrategy(min_profit_pct=config.min_arbitrage_percentage)
            )

        if "yes_no_imbalance" in config.strategies:
            self.strategies.append(
                YesNoImbalanceStrategy(min_profit_pct=config.min_arbitrage_percentage)
            )

        if "multi_leg" in config.strategies:
            self.strategies.append(
                MultiLegStrategy(min_profit_pct=config.min_arbitrage_percentage * 2)
            )

        if "correlated_events" in config.strategies:
            self.strategies.append(
                CorrelatedEventsStrategy(min_profit_pct=config.min_arbitrage_percentage)
            )

        if "order_book_spread" in config.strategies:
            self.strategies.append(
                OrderBookSpreadStrategy(
                    min_spread_pct=2.0, min_profit_pct=config.min_arbitrage_percentage
                )
            )

        if "time_based" in config.strategies:
            self.strategies.append(
                TimeBasedStrategy(
                    min_profit_pct=config.min_arbitrage_percentage,
                    time_window_hours=24.0,
                )
            )

        logger.info(f"Initialized {len(self.strategies)} arbitrage strategies")

    def detect_opportunities(self, markets: List[Market]) -> List[Opportunity]:
        """Detect all arbitrage opportunities across enabled strategies.

        Args:
            markets: List of markets to analyze

        Returns:
            List of all detected opportunities
        """
        all_opportunities = []

        for strategy in self.strategies:
            try:
                opportunities = strategy.detect(markets)
                all_opportunities.extend(opportunities)

                strategy_name = strategy.__class__.__name__
                logger.debug(
                    f"{strategy_name} found {len(opportunities)} opportunities"
                )

            except Exception as e:
                logger.error(f"Error in strategy {strategy.__class__.__name__}: {e}")

        logger.info(
            f"Total opportunities detected: {len(all_opportunities)} "
            f"from {len(markets)} markets"
        )

        return all_opportunities

    def filter_profitable_opportunities(
        self, opportunities: List[Opportunity], gas_price: float
    ) -> List[Opportunity]:
        """Filter opportunities to only those that are profitable after costs.

        Args:
            opportunities: List of detected opportunities
            gas_price: Current gas price in gwei

        Returns:
            Filtered list of profitable opportunities
        """
        profitable = []

        for opp in opportunities:
            # Estimate transaction costs
            gas_cost_usd = self._estimate_gas_cost(opp, gas_price)

            # Calculate net profit
            expected_profit = getattr(opp, "expected_profit", 0)
            net_profit = expected_profit - gas_cost_usd

            # Apply safety margin
            if (
                net_profit
                > self.config.min_profit_threshold * self.config.safety_margin
            ):
                profitable.append(opp)

        logger.info(
            f"Filtered to {len(profitable)} profitable opportunities "
            f"(from {len(opportunities)} total)"
        )

        return profitable

    def _estimate_gas_cost(self, opportunity: Opportunity, gas_price: float) -> float:
        """Estimate gas cost for executing an opportunity.

        Args:
            opportunity: Arbitrage opportunity
            gas_price: Gas price in gwei

        Returns:
            Estimated cost in USD
        """
        # Estimate gas units based on opportunity type
        if isinstance(opportunity, YesNoImbalanceOpportunity):
            gas_units = 200000  # Two transactions
        elif isinstance(opportunity, CrossMarketOpportunity):
            gas_units = 200000  # Buy and sell
        elif isinstance(opportunity, MultiLegOpportunity):
            gas_units = 100000 * len(opportunity.legs)
        elif isinstance(opportunity, CorrelatedEventsOpportunity):
            gas_units = 200000  # Two related transactions
        elif isinstance(opportunity, OrderBookSpreadOpportunity):
            gas_units = 100000  # Single limit order
        elif isinstance(opportunity, TimeBasedOpportunity):
            gas_units = 150000  # Quick market order
        else:
            gas_units = 150000  # Default

        # Apply safety buffer
        gas_units *= self.config.gas_safety_buffer

        # Convert to USD (approximate)
        # MATIC price ~$0.80, gas in gwei
        matic_price = 0.80
        gas_cost_matic = (gas_units * gas_price) / 1e9
        gas_cost_usd = gas_cost_matic * matic_price

        return gas_cost_usd
