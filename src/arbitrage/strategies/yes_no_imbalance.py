"""YES/NO imbalance arbitrage strategy."""

from dataclasses import dataclass
from typing import List
from loguru import logger

from ...market.market_data import Market


@dataclass
class YesNoImbalanceOpportunity:
    """YES/NO imbalance arbitrage opportunity."""

    market: Market
    yes_price: float
    no_price: float
    price_sum: float
    imbalance: float
    profit_percentage: float
    expected_profit: float
    action: str  # "buy_both" or "sell_both"

    def __str__(self) -> str:
        """String representation."""
        return (
            f"YES/NO Imbalance: {self.market.question[:50]}... | "
            f"YES: {self.yes_price:.3f}, NO: {self.no_price:.3f}, "
            f"Sum: {self.price_sum:.3f} | Action: {self.action} | "
            f"Profit: {self.profit_percentage:.2f}%"
        )


class YesNoImbalanceStrategy:
    """Detect opportunities where YES + NO prices ≠ 1.00."""

    def __init__(self, min_profit_pct: float = 0.5, imbalance_threshold: float = 0.02):
        """Initialize strategy.

        Args:
            min_profit_pct: Minimum profit percentage threshold
            imbalance_threshold: Minimum imbalance to trigger opportunity
        """
        self.min_profit_pct = min_profit_pct
        self.imbalance_threshold = imbalance_threshold

    def detect(self, markets: List[Market]) -> List[YesNoImbalanceOpportunity]:
        """Detect YES/NO imbalance arbitrage opportunities.

        In efficient markets, YES + NO should equal 1.00. When the sum deviates:
        - If sum < 1.00: Buy both YES and NO (guaranteed profit when market resolves)
        - If sum > 1.00: Sell both YES and NO (profit from immediate arbitrage)

        Args:
            markets: List of markets to analyze

        Returns:
            List of detected opportunities
        """
        opportunities = []

        for market in markets:
            # Use ask prices when buying (what we pay)
            buy_sum = market.yes_ask + market.no_ask
            buy_imbalance = 1.0 - buy_sum

            # If sum < 1.0, we can buy both and profit
            if buy_imbalance > self.imbalance_threshold:
                profit_pct = (buy_imbalance / buy_sum) * 100

                if profit_pct >= self.min_profit_pct:
                    # Calculate expected profit for $100 position
                    position_size = 100
                    expected_profit = buy_imbalance * position_size

                    opportunity = YesNoImbalanceOpportunity(
                        market=market,
                        yes_price=market.yes_ask,
                        no_price=market.no_ask,
                        price_sum=buy_sum,
                        imbalance=buy_imbalance,
                        profit_percentage=profit_pct,
                        expected_profit=expected_profit,
                        action="buy_both",
                    )
                    opportunities.append(opportunity)

            # Use bid prices when selling (what we receive)
            sell_sum = market.yes_bid + market.no_bid
            sell_imbalance = sell_sum - 1.0

            # If sum > 1.0, we can sell both and profit
            if sell_imbalance > self.imbalance_threshold:
                profit_pct = (sell_imbalance / 1.0) * 100

                if profit_pct >= self.min_profit_pct:
                    # Calculate expected profit for $100 position
                    position_size = 100
                    expected_profit = sell_imbalance * position_size

                    opportunity = YesNoImbalanceOpportunity(
                        market=market,
                        yes_price=market.yes_bid,
                        no_price=market.no_bid,
                        price_sum=sell_sum,
                        imbalance=sell_imbalance,
                        profit_percentage=profit_pct,
                        expected_profit=expected_profit,
                        action="sell_both",
                    )
                    opportunities.append(opportunity)

        logger.debug(
            f"YES/NO imbalance strategy found {len(opportunities)} opportunities"
        )
        return opportunities
