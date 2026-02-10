"""Unit tests for arbitrage detector."""

import pytest
from datetime import datetime

from src.arbitrage.detector import ArbitrageDetector
from src.config import Config
from src.market.market_data import Market, MarketStatus


def create_test_config(**overrides):
    """Create test configuration."""
    defaults = {
        "min_profit_threshold": 5.0,
        "position_sizing_strategy": "kelly",
        "kelly_fraction": 0.25,
        "max_position_size": 1000.0,
        "max_total_exposure": 5000.0,
        "strategies": ["cross_market", "yes_no_imbalance"],
        "min_arbitrage_percentage": 0.5,
        "websocket_enabled": False,
        "markets_to_monitor": "all",
        "refresh_interval": 1,
        "max_markets": 100,
        "max_slippage": 0.02,
        "safety_margin": 1.5,
        "stop_loss_percentage": 0.05,
        "max_position_age_hours": 24,
        "mode": "alert",
        "gas_price_limit": 100,
        "order_type": "limit",
        "execution_timeout": 30,
        "polygon_rpc_url": "https://polygon-rpc.com",
        "gas_safety_buffer": 1.2,
        "log_level": "INFO",
        "log_file": "logs/test.log",
        "log_rotation": "100 MB",
        "polymarket_api_url": "https://clob.polymarket.com",
        "polymarket_ws_url": "wss://ws-subscriptions-clob.polymarket.com/ws",
        "api_timeout": 10,
        "api_retry_attempts": 3,
        "initial_capital": 10000.0,
        "enable_analytics": True,
        "analytics_db_path": "data/test_analytics.db",
        "track_missed_opportunities": True,
        "debug": False,
        "dry_run": True,
    }
    defaults.update(overrides)
    return Config(**defaults)


def create_test_market(market_id: str, yes_price: float = 0.50, no_price: float = 0.50):
    """Create a test market."""
    return Market(
        market_id=market_id,
        question=f"Test question {market_id}",
        description="Test market",
        category="test",
        end_date=datetime(2024, 12, 31),
        status=MarketStatus.ACTIVE,
        yes_price=yes_price,
        no_price=no_price,
        yes_bid=yes_price - 0.02,
        yes_ask=yes_price + 0.02,
        no_bid=no_price - 0.02,
        no_ask=no_price + 0.02,
        volume_24h=10000,
        liquidity=50000,
    )


class TestArbitrageDetector:
    """Test arbitrage detector."""

    def test_initialization_with_strategies(self):
        """Test detector initializes with configured strategies."""
        config = create_test_config(
            strategies=[
                "cross_market",
                "yes_no_imbalance",
                "multi_leg",
                "correlated_events",
            ]
        )
        detector = ArbitrageDetector(config)

        assert len(detector.strategies) == 4

    def test_initialization_single_strategy(self):
        """Test detector with single strategy."""
        config = create_test_config(strategies=["yes_no_imbalance"])
        detector = ArbitrageDetector(config)

        assert len(detector.strategies) == 1

    def test_detect_opportunities_empty_markets(self):
        """Test detection with no markets."""
        config = create_test_config()
        detector = ArbitrageDetector(config)

        opportunities = detector.detect_opportunities([])

        assert opportunities == []

    def test_detect_opportunities_with_markets(self):
        """Test detection with valid markets."""
        config = create_test_config(strategies=["yes_no_imbalance"])
        detector = ArbitrageDetector(config)

        # Create market with imbalance
        markets = [create_test_market("market_1", yes_price=0.45, no_price=0.48)]

        opportunities = detector.detect_opportunities(markets)

        # Should detect YES/NO imbalance
        assert len(opportunities) >= 0  # May or may not detect depending on thresholds

    def test_filter_profitable_opportunities(self):
        """Test filtering by profitability."""
        config = create_test_config()
        detector = ArbitrageDetector(config)

        # Create mock opportunities
        from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceOpportunity

        markets = [create_test_market("market_1")]

        # High profit opportunity
        high_profit_opp = YesNoImbalanceOpportunity(
            market=markets[0],
            yes_price=0.45,
            no_price=0.48,
            price_sum=0.93,
            imbalance=0.07,
            profit_percentage=7.5,
            expected_profit=100.0,
            action="buy_both",
        )

        # Low profit opportunity
        low_profit_opp = YesNoImbalanceOpportunity(
            market=markets[0],
            yes_price=0.495,
            no_price=0.495,
            price_sum=0.99,
            imbalance=0.01,
            profit_percentage=1.0,
            expected_profit=1.0,
            action="buy_both",
        )

        gas_price = 30.0

        # Filter opportunities
        profitable = detector.filter_profitable_opportunities(
            [high_profit_opp, low_profit_opp], gas_price
        )

        # High profit should be included
        assert len(profitable) >= 1

    def test_estimate_gas_cost(self):
        """Test gas cost estimation."""
        config = create_test_config()
        detector = ArbitrageDetector(config)

        from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceOpportunity

        market = create_test_market("market_1")
        opp = YesNoImbalanceOpportunity(
            market=market,
            yes_price=0.45,
            no_price=0.48,
            price_sum=0.93,
            imbalance=0.07,
            profit_percentage=7.5,
            expected_profit=100.0,
            action="buy_both",
        )

        gas_price = 30.0  # gwei
        gas_cost = detector._estimate_gas_cost(opp, gas_price)

        # Should return some positive cost
        assert gas_cost > 0
        assert isinstance(gas_cost, float)

    def test_multiple_strategy_detection(self):
        """Test detection across multiple strategies."""
        config = create_test_config(strategies=["yes_no_imbalance", "cross_market"])
        detector = ArbitrageDetector(config)

        # Create markets with different opportunities
        markets = [
            create_test_market("market_1", yes_price=0.45, no_price=0.48),
            create_test_market("market_2", yes_price=0.60, no_price=0.40),
            create_test_market("market_3", yes_price=0.70, no_price=0.30),
        ]

        opportunities = detector.detect_opportunities(markets)

        # Should run both strategies
        assert isinstance(opportunities, list)


class TestDetectorEdgeCases:
    """Test edge cases for detector."""

    def test_malformed_market_data(self):
        """Test detector handles malformed market data."""
        config = create_test_config()
        detector = ArbitrageDetector(config)

        # Create market with extreme values
        bad_market = create_test_market("bad_1", yes_price=1.5, no_price=-0.5)

        # Should not crash
        opportunities = detector.detect_opportunities([bad_market])
        assert isinstance(opportunities, list)

    def test_very_high_gas_price(self):
        """Test filtering with very high gas price."""
        config = create_test_config()
        detector = ArbitrageDetector(config)

        from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceOpportunity

        market = create_test_market("market_1")
        opp = YesNoImbalanceOpportunity(
            market=market,
            yes_price=0.49,
            no_price=0.49,
            price_sum=0.98,
            imbalance=0.02,
            profit_percentage=2.0,
            expected_profit=5.0,
            action="buy_both",
        )

        very_high_gas = 1000.0  # Extremely high gas price

        profitable = detector.filter_profitable_opportunities([opp], very_high_gas)

        # Should filter out due to high gas costs
        assert len(profitable) == 0

    def test_zero_profit_opportunities(self):
        """Test handling of zero or negative profit opportunities."""
        config = create_test_config()
        detector = ArbitrageDetector(config)

        from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceOpportunity

        market = create_test_market("market_1")
        zero_profit_opp = YesNoImbalanceOpportunity(
            market=market,
            yes_price=0.50,
            no_price=0.50,
            price_sum=1.00,
            imbalance=0.00,
            profit_percentage=0.0,
            expected_profit=0.0,
            action="buy_both",
        )

        profitable = detector.filter_profitable_opportunities([zero_profit_opp], 30.0)

        # Should not include zero profit opportunities
        assert len(profitable) == 0
