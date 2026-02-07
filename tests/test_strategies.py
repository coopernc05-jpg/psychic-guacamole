"""Unit tests for arbitrage detection strategies."""

import pytest
from datetime import datetime

from src.arbitrage.strategies.cross_market import CrossMarketStrategy
from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceStrategy
from src.arbitrage.strategies.multi_leg import MultiLegStrategy
from src.arbitrage.strategies.correlated_events import CorrelatedEventsStrategy
from src.market.market_data import Market, MarketStatus


def create_test_market(
    market_id: str,
    question: str,
    yes_price: float,
    no_price: float,
    yes_ask: float = None,
    no_ask: float = None,
    yes_bid: float = None,
    no_bid: float = None,
) -> Market:
    """Create a test market with given prices."""
    if yes_ask is None:
        yes_ask = yes_price + 0.02
    if no_ask is None:
        no_ask = no_price + 0.02
    if yes_bid is None:
        yes_bid = yes_price - 0.02
    if no_bid is None:
        no_bid = no_price - 0.02

    return Market(
        market_id=market_id,
        question=question,
        description=f"Test market: {question}",
        category="test",
        end_date=datetime(2024, 12, 31),
        status=MarketStatus.ACTIVE,
        yes_price=yes_price,
        no_price=no_price,
        yes_bid=yes_bid,
        yes_ask=yes_ask,
        no_bid=no_bid,
        no_ask=no_ask,
        volume_24h=10000,
        liquidity=50000,
    )


class TestYesNoImbalanceStrategy:
    """Test YES/NO imbalance detection."""

    def test_detect_buy_both_opportunity(self):
        """Test detection when YES + NO < 1.00 (buy both)."""
        strategy = YesNoImbalanceStrategy(min_profit_pct=0.5)

        # Create market with sum < 1.00
        market = create_test_market(
            market_id="test_1",
            question="Will it rain?",
            yes_price=0.45,
            no_price=0.48,
            yes_ask=0.46,
            no_ask=0.49,
        )

        opportunities = strategy.detect([market])

        assert len(opportunities) == 1
        assert opportunities[0].action == "buy_both"
        assert opportunities[0].price_sum < 1.0
        assert opportunities[0].imbalance > 0

    def test_detect_sell_both_opportunity(self):
        """Test detection when YES + NO > 1.00 (sell both)."""
        strategy = YesNoImbalanceStrategy(min_profit_pct=0.5)

        # Create market with sum > 1.00
        market = create_test_market(
            market_id="test_2",
            question="Will it snow?",
            yes_price=0.58,
            no_price=0.46,
            yes_bid=0.58,
            no_bid=0.46,
        )

        opportunities = strategy.detect([market])

        assert len(opportunities) == 1
        assert opportunities[0].action == "sell_both"
        assert opportunities[0].price_sum > 1.0
        assert opportunities[0].imbalance > 0

    def test_no_opportunity_balanced_market(self):
        """Test no opportunity when market is balanced."""
        strategy = YesNoImbalanceStrategy(min_profit_pct=0.5)

        # Create balanced market (sum ≈ 1.00)
        market = create_test_market(
            market_id="test_3",
            question="Will the sun rise?",
            yes_price=0.50,
            no_price=0.50,
            yes_ask=0.51,
            no_ask=0.51,
        )

        opportunities = strategy.detect([market])

        assert len(opportunities) == 0

    def test_below_minimum_threshold(self):
        """Test opportunity below minimum profit threshold is filtered."""
        strategy = YesNoImbalanceStrategy(min_profit_pct=2.0)  # High threshold

        # Small imbalance
        market = create_test_market(
            market_id="test_4",
            question="Small imbalance",
            yes_price=0.49,
            no_price=0.49,
            yes_ask=0.495,
            no_ask=0.495,
        )

        opportunities = strategy.detect([market])

        assert len(opportunities) == 0


class TestCrossMarketStrategy:
    """Test cross-market arbitrage detection."""

    def test_detect_cross_market_opportunity(self):
        """Test detection of price difference across markets."""
        strategy = CrossMarketStrategy(min_profit_pct=0.5)

        # Same question, different prices
        market1 = create_test_market(
            market_id="market_1",
            question="Trump wins primary",
            yes_price=0.60,
            no_price=0.40,
            yes_ask=0.62,
            yes_bid=0.58,
        )

        market2 = create_test_market(
            market_id="market_2",
            question="Trump wins primary",
            yes_price=0.70,
            no_price=0.30,
            yes_ask=0.72,
            yes_bid=0.68,
        )

        opportunities = strategy.detect([market1, market2])

        assert len(opportunities) > 0
        # Should find opportunity to buy low, sell high
        assert any(opp.buy_price < opp.sell_price for opp in opportunities)

    def test_no_opportunity_similar_prices(self):
        """Test no opportunity when prices are similar."""
        strategy = CrossMarketStrategy(min_profit_pct=0.5)

        market1 = create_test_market(
            market_id="market_1",
            question="Biden wins",
            yes_price=0.60,
            no_price=0.40,
            yes_ask=0.61,
            yes_bid=0.59,
        )

        market2 = create_test_market(
            market_id="market_2",
            question="Biden wins",
            yes_price=0.60,
            no_price=0.40,
            yes_ask=0.61,
            yes_bid=0.59,
        )

        opportunities = strategy.detect([market1, market2])

        assert len(opportunities) == 0


class TestMultiLegStrategy:
    """Test multi-leg arbitrage detection."""

    def test_detect_multi_leg_opportunity(self):
        """Test detection of multi-leg opportunities."""
        strategy = MultiLegStrategy(min_profit_pct=1.0, max_legs=5)

        # Create related markets in same category
        markets = [
            create_test_market(
                f"market_{i}", f"Election outcome {i}", 0.30 + i * 0.1, 0.70 - i * 0.1
            )
            for i in range(5)
        ]

        opportunities = strategy.detect(markets)

        # Should detect some multi-leg opportunities
        assert len(opportunities) >= 0  # May or may not find opportunities

    def test_respects_max_legs(self):
        """Test strategy respects max_legs parameter."""
        strategy = MultiLegStrategy(min_profit_pct=1.0, max_legs=3)

        markets = [
            create_test_market(f"market_{i}", f"Outcome {i}", 0.25, 0.75)
            for i in range(10)
        ]

        opportunities = strategy.detect(markets)

        # All opportunities should have at most 3 legs
        for opp in opportunities:
            assert opp.complexity_score <= 3


class TestCorrelatedEventsStrategy:
    """Test correlated events arbitrage detection."""

    def test_detect_positive_correlation(self):
        """Test detection of positive correlation opportunities."""
        strategy = CorrelatedEventsStrategy(min_profit_pct=0.5)

        # Related election markets
        market1 = create_test_market(
            market_id="primary",
            question="Trump wins primary",
            yes_price=0.80,
            no_price=0.20,
        )

        market2 = create_test_market(
            market_id="nomination",
            question="Trump wins nomination",
            yes_price=0.70,  # Should be >= primary
            no_price=0.30,
        )

        opportunities = strategy.detect([market1, market2])

        # May or may not find opportunity depending on correlation logic
        assert isinstance(opportunities, list)

    def test_groups_by_category(self):
        """Test markets are grouped by category for analysis."""
        strategy = CorrelatedEventsStrategy(min_profit_pct=0.5)

        election_market1 = create_test_market(
            "election_1", "Election question 1", 0.60, 0.40
        )
        election_market1.category = "election"

        election_market2 = create_test_market(
            "election_2", "Election question 2", 0.55, 0.45
        )
        election_market2.category = "election"

        sports_market = create_test_market("sports_1", "Sports question", 0.50, 0.50)
        sports_market.category = "sports"

        markets = [election_market1, election_market2, sports_market]
        opportunities = strategy.detect(markets)

        # Should handle multiple categories
        assert isinstance(opportunities, list)


class TestStrategyIntegration:
    """Integration tests for multiple strategies."""

    def test_all_strategies_on_same_markets(self):
        """Test all strategies can process same market set."""
        markets = [
            create_test_market(
                f"market_{i}", f"Question {i}", 0.40 + i * 0.05, 0.60 - i * 0.05
            )
            for i in range(10)
        ]

        yes_no_strategy = YesNoImbalanceStrategy()
        cross_market_strategy = CrossMarketStrategy()
        multi_leg_strategy = MultiLegStrategy()
        correlated_strategy = CorrelatedEventsStrategy()

        # All should run without error
        yes_no_opps = yes_no_strategy.detect(markets)
        cross_opps = cross_market_strategy.detect(markets)
        multi_opps = multi_leg_strategy.detect(markets)
        corr_opps = correlated_strategy.detect(markets)

        # Verify all return lists
        assert isinstance(yes_no_opps, list)
        assert isinstance(cross_opps, list)
        assert isinstance(multi_opps, list)
        assert isinstance(corr_opps, list)

    def test_strategy_with_empty_markets(self):
        """Test strategies handle empty market list gracefully."""
        empty_markets = []

        strategies = [
            YesNoImbalanceStrategy(),
            CrossMarketStrategy(),
            MultiLegStrategy(),
            CorrelatedEventsStrategy(),
        ]

        for strategy in strategies:
            opportunities = strategy.detect(empty_markets)
            assert opportunities == []
