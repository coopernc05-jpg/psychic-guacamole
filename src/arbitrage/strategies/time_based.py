"""Time-based arbitrage strategy."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger

from ...market.market_data import Market


@dataclass
class TimeBasedOpportunity:
    """Time-based arbitrage opportunity."""

    market: Market
    outcome: str  # YES or NO
    current_price: float
    historical_avg: float
    price_change_pct: float
    time_to_resolution: float  # Hours
    volatility_score: float
    opportunity_type: (
        str  # "panic_selling", "last_minute_mispricing", "volatility_spike"
    )
    expected_profit: float
    confidence: float

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Time-Based Arb ({self.opportunity_type}): "
            f"{self.outcome} on {self.market.question[:50]}... | "
            f"Price: {self.current_price:.3f} vs Avg: {self.historical_avg:.3f} | "
            f"Change: {self.price_change_pct:+.2f}% | "
            f"Resolution in {self.time_to_resolution:.1f}h | "
            f"Profit: ${self.expected_profit:.2f}"
        )


class TimeBasedStrategy:
    """Monitor price changes near event resolution and detect mispricing.

    This strategy identifies:
    1. Panic selling before resolution
    2. Last-minute mispricing as events conclude
    3. Sudden volatility spikes that create opportunities

    Requires quick execution as opportunities may disappear rapidly.
    """

    def __init__(
        self,
        min_profit_pct: float = 0.6,
        time_window_hours: float = 24.0,
        volatility_threshold: float = 2.0,
    ):
        """Initialize strategy.

        Args:
            min_profit_pct: Minimum profit percentage threshold (default 0.6%)
            time_window_hours: Time window before resolution to monitor (default 24h)
            volatility_threshold: Minimum volatility score to flag (default 2.0)
        """
        self.min_profit_pct = min_profit_pct
        self.time_window_hours = time_window_hours
        self.volatility_threshold = volatility_threshold

        # Store historical prices for comparison
        self._price_history: Dict[str, List[tuple[datetime, float, float]]] = {}

        logger.info(
            f"Initialized TimeBasedStrategy: "
            f"min_profit={min_profit_pct}%, window={time_window_hours}h"
        )

    def detect(self, markets: List[Market]) -> List[TimeBasedOpportunity]:
        """Detect time-based arbitrage opportunities.

        Args:
            markets: List of markets to analyze

        Returns:
            List of opportunities found
        """
        opportunities = []
        now = datetime.now()

        for market in markets:
            # Calculate hours to resolution
            time_to_resolution = (market.end_date - now).total_seconds() / 3600

            # Only analyze markets within the time window
            if time_to_resolution > self.time_window_hours or time_to_resolution < 0:
                continue

            # Update price history
            self._update_price_history(market, now)

            # Check YES outcome
            yes_opp = self._analyze_outcome(
                market, "YES", market.yes_price, time_to_resolution, now
            )
            if yes_opp:
                opportunities.append(yes_opp)

            # Check NO outcome
            no_opp = self._analyze_outcome(
                market, "NO", market.no_price, time_to_resolution, now
            )
            if no_opp:
                opportunities.append(no_opp)

        if opportunities:
            logger.info(
                f"TimeBasedStrategy detected {len(opportunities)} opportunities"
            )

        return opportunities

    def _update_price_history(self, market: Market, timestamp: datetime):
        """Update price history for a market.

        Args:
            market: Market to update
            timestamp: Current timestamp
        """
        market_id = market.market_id

        if market_id not in self._price_history:
            self._price_history[market_id] = []

        # Add current prices
        self._price_history[market_id].append(
            (timestamp, market.yes_price, market.no_price)
        )

        # Keep only last 24 hours of data
        cutoff = timestamp - timedelta(hours=24)
        self._price_history[market_id] = [
            (ts, yes_p, no_p)
            for ts, yes_p, no_p in self._price_history[market_id]
            if ts >= cutoff
        ]

    def _analyze_outcome(
        self,
        market: Market,
        outcome: str,
        current_price: float,
        time_to_resolution: float,
        now: datetime,
    ) -> Optional[TimeBasedOpportunity]:
        """Analyze a specific outcome for opportunities.

        Args:
            market: Market to analyze
            outcome: "YES" or "NO"
            current_price: Current price
            time_to_resolution: Hours to resolution
            now: Current timestamp

        Returns:
            Opportunity if found, None otherwise
        """
        market_id = market.market_id

        # Need at least some price history
        if (
            market_id not in self._price_history
            or len(self._price_history[market_id]) < 3
        ):
            return None

        # Calculate historical average
        price_idx = 1 if outcome == "YES" else 2
        prices = [
            p[price_idx] for p in self._price_history[market_id] if p[price_idx] > 0
        ]

        if not prices or len(prices) < 3:
            return None

        historical_avg = sum(prices) / len(prices)

        # Calculate price change percentage
        price_change_pct = ((current_price - historical_avg) / historical_avg) * 100

        # Calculate volatility (standard deviation / mean)
        mean = historical_avg
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        std_dev = variance**0.5
        volatility_score = (std_dev / mean) if mean > 0 else 0

        # Detect opportunity types
        opportunity_type = None
        confidence = 0.0

        # 1. Panic selling: Price drops significantly near resolution
        if (
            price_change_pct < -5.0
            and time_to_resolution < 12
            and volatility_score > self.volatility_threshold
        ):
            opportunity_type = "panic_selling"
            confidence = min(0.85, 0.65 + (abs(price_change_pct) / 100))

        # 2. Last-minute mispricing: Large deviation very close to resolution
        elif (
            abs(price_change_pct) > 10.0
            and time_to_resolution < 6
            and volatility_score > self.volatility_threshold * 1.5
        ):
            opportunity_type = "last_minute_mispricing"
            confidence = min(0.90, 0.70 + (abs(price_change_pct) / 200))

        # 3. Volatility spike: Sudden price movement
        elif (
            volatility_score > self.volatility_threshold * 2
            and abs(price_change_pct) > 8.0
        ):
            opportunity_type = "volatility_spike"
            confidence = min(0.80, 0.60 + (volatility_score / 20))

        if opportunity_type is None:
            return None

        # Estimate expected profit
        # Assumes price will revert towards historical average
        expected_price_reversion = historical_avg
        price_reversion_pct = (
            (expected_price_reversion - current_price) / current_price
        ) * 100

        # Position size estimation (conservative $100)
        position_size = 100.0
        expected_profit = position_size * (abs(price_reversion_pct) / 100)

        # Check profit threshold
        if expected_profit < (position_size * self.min_profit_pct / 100):
            return None

        return TimeBasedOpportunity(
            market=market,
            outcome=outcome,
            current_price=current_price,
            historical_avg=historical_avg,
            price_change_pct=price_change_pct,
            time_to_resolution=time_to_resolution,
            volatility_score=volatility_score,
            opportunity_type=opportunity_type,
            expected_profit=expected_profit,
            confidence=confidence,
        )

    def reset_history(self):
        """Reset price history (useful for testing)."""
        self._price_history.clear()

    def get_price_history(self, market_id: str) -> List[tuple[datetime, float, float]]:
        """Get price history for a market.

        Args:
            market_id: Market ID

        Returns:
            List of (timestamp, yes_price, no_price) tuples
        """
        return self._price_history.get(market_id, [])
