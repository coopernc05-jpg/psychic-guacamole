"""Order book spread trading (market making) strategy."""

from dataclasses import dataclass
from typing import List
from loguru import logger

from ...market.market_data import Market


@dataclass
class OrderBookSpreadOpportunity:
    """Order book spread trading opportunity."""

    market: Market
    outcome: str  # YES or NO
    bid_price: float
    ask_price: float
    spread_pct: float
    mid_price: float
    liquidity: float
    expected_profit: float

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Order Book Spread: {self.outcome} on {self.market.question[:50]}... | "
            f"Bid: {self.bid_price:.3f}, Ask: {self.ask_price:.3f} | "
            f"Spread: {self.spread_pct:.2f}% | Profit: ${self.expected_profit:.2f}"
        )


class OrderBookSpreadStrategy:
    """Analyze bid-ask spreads and place limit orders to capture spreads.

    This strategy acts as a market maker by:
    1. Identifying markets with wide bid-ask spreads
    2. Placing limit orders between the bid and ask
    3. Profiting from providing liquidity

    Target: 2%+ spreads, 0.5% minimum profit per trade
    """

    def __init__(self, min_spread_pct: float = 2.0, min_profit_pct: float = 0.5):
        """Initialize strategy.

        Args:
            min_spread_pct: Minimum spread percentage to consider (default 2%)
            min_profit_pct: Minimum profit percentage after costs (default 0.5%)
        """
        self.min_spread_pct = min_spread_pct
        self.min_profit_pct = min_profit_pct
        logger.info(
            f"Initialized OrderBookSpreadStrategy: "
            f"min_spread={min_spread_pct}%, min_profit={min_profit_pct}%"
        )

    def detect(self, markets: List[Market]) -> List[OrderBookSpreadOpportunity]:
        """Detect order book spread opportunities.

        Args:
            markets: List of markets to analyze

        Returns:
            List of opportunities found
        """
        opportunities = []

        for market in markets:
            # Check YES outcome spread
            yes_spread_pct = self._calculate_spread_pct(market.yes_bid, market.yes_ask)
            if yes_spread_pct >= self.min_spread_pct:
                mid_price = (market.yes_bid + market.yes_ask) / 2
                # Estimate profit by capturing half the spread
                expected_profit = self._estimate_profit(
                    market.yes_bid, market.yes_ask, market.liquidity
                )

                # Check if profit meets minimum threshold
                profit_pct = (expected_profit / (mid_price * 100)) * 100
                if profit_pct >= self.min_profit_pct:
                    opportunities.append(
                        OrderBookSpreadOpportunity(
                            market=market,
                            outcome="YES",
                            bid_price=market.yes_bid,
                            ask_price=market.yes_ask,
                            spread_pct=yes_spread_pct,
                            mid_price=mid_price,
                            liquidity=market.liquidity,
                            expected_profit=expected_profit,
                        )
                    )

            # Check NO outcome spread
            no_spread_pct = self._calculate_spread_pct(market.no_bid, market.no_ask)
            if no_spread_pct >= self.min_spread_pct:
                mid_price = (market.no_bid + market.no_ask) / 2
                expected_profit = self._estimate_profit(
                    market.no_bid, market.no_ask, market.liquidity
                )

                profit_pct = (expected_profit / (mid_price * 100)) * 100
                if profit_pct >= self.min_profit_pct:
                    opportunities.append(
                        OrderBookSpreadOpportunity(
                            market=market,
                            outcome="NO",
                            bid_price=market.no_bid,
                            ask_price=market.no_ask,
                            spread_pct=no_spread_pct,
                            mid_price=mid_price,
                            liquidity=market.liquidity,
                            expected_profit=expected_profit,
                        )
                    )

        if opportunities:
            logger.info(
                f"OrderBookSpreadStrategy detected {len(opportunities)} opportunities"
            )

        return opportunities

    def _calculate_spread_pct(self, bid: float, ask: float) -> float:
        """Calculate spread as a percentage of mid price.

        Args:
            bid: Bid price
            ask: Ask price

        Returns:
            Spread percentage
        """
        if bid <= 0 or ask <= 0 or ask <= bid:
            return 0.0

        mid_price = (bid + ask) / 2
        spread = ask - bid
        spread_pct = (spread / mid_price) * 100

        return spread_pct

    def _estimate_profit(self, bid: float, ask: float, liquidity: float) -> float:
        """Estimate expected profit from market making.

        Args:
            bid: Bid price
            ask: Ask price
            liquidity: Market liquidity in USD

        Returns:
            Expected profit in USD
        """
        # Estimate position size based on liquidity
        # Use conservative 10% of liquidity to avoid market impact
        position_size_usd = min(liquidity * 0.1, 100.0)

        # Calculate profit per unit
        mid_price = (bid + ask) / 2
        units = position_size_usd / mid_price

        # Profit is half the spread (we capture the middle)
        spread = ask - bid
        profit_per_unit = spread / 2

        expected_profit = units * profit_per_unit

        return expected_profit
