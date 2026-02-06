"""Unit tests for position sizing."""

import pytest
from src.execution.position_sizing import kelly_criterion, PositionSizer
from src.config import Config


def create_test_config(**overrides):
    """Create test configuration."""
    defaults = {
        "min_profit_threshold": 5.0,
        "position_sizing_strategy": "kelly",
        "kelly_fraction": 0.25,
        "max_position_size": 1000.0,
        "max_total_exposure": 5000.0,
        "strategies": ["yes_no_imbalance"],
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
        "dry_run": True
    }
    defaults.update(overrides)
    return Config(**defaults)


class TestKellyCriterion:
    """Test Kelly Criterion calculation."""
    
    def test_basic_kelly_calculation(self):
        """Test basic Kelly Criterion."""
        win_prob = 0.60
        win_return = 1.0  # 100% return
        
        kelly_f = kelly_criterion(win_prob, win_return)
        
        # Kelly = (p * b - q) / b = (0.6 * 1 - 0.4) / 1 = 0.2
        assert 0.15 < kelly_f < 0.25
    
    def test_high_probability_high_return(self):
        """Test with high probability and high return."""
        kelly_f = kelly_criterion(win_probability=0.80, win_return=2.0)
        
        # Should recommend significant position
        assert kelly_f > 0.3
    
    def test_low_probability(self):
        """Test with low win probability."""
        kelly_f = kelly_criterion(win_probability=0.40, win_return=1.0)
        
        # Should recommend small or no position
        assert kelly_f <= 0.2
    
    def test_zero_probability(self):
        """Test edge case: zero probability."""
        kelly_f = kelly_criterion(win_probability=0.0, win_return=1.0)
        
        assert kelly_f == 0.0
    
    def test_full_probability(self):
        """Test edge case: 100% probability."""
        kelly_f = kelly_criterion(win_probability=1.0, win_return=1.0)
        
        assert kelly_f == 0.0  # Edge case handling
    
    def test_negative_return(self):
        """Test with negative return (should return 0)."""
        kelly_f = kelly_criterion(win_probability=0.60, win_return=-0.5)
        
        assert kelly_f == 0.0


class TestPositionSizer:
    """Test Position Sizer class."""
    
    def test_kelly_sizing(self):
        """Test Kelly-based position sizing."""
        config = create_test_config(
            position_sizing_strategy="kelly",
            kelly_fraction=0.25
        )
        sizer = PositionSizer(config)
        
        position_size = sizer.calculate_position_size(
            opportunity_profit_pct=5.0,
            opportunity_confidence=0.80,
            available_capital=10000.0
        )
        
        # Should return reasonable position size
        assert 0 < position_size <= config.max_position_size
        assert position_size <= available_capital
    
    def test_fixed_sizing(self):
        """Test fixed position sizing."""
        config = create_test_config(
            position_sizing_strategy="fixed",
            max_position_size=500.0
        )
        sizer = PositionSizer(config)
        
        position_size = sizer.calculate_position_size(
            opportunity_profit_pct=5.0,
            opportunity_confidence=0.80,
            available_capital=10000.0
        )
        
        # Should use fixed sizing
        assert position_size > 0
        assert position_size <= 500.0
    
    def test_percentage_sizing(self):
        """Test percentage-based sizing."""
        config = create_test_config(
            position_sizing_strategy="percentage"
        )
        sizer = PositionSizer(config)
        
        capital = 10000.0
        position_size = sizer.calculate_position_size(
            opportunity_profit_pct=5.0,
            opportunity_confidence=0.80,
            available_capital=capital
        )
        
        # Should be percentage of capital
        assert position_size > 0
        assert position_size < capital * 0.1  # Less than 10%
    
    def test_respects_max_position_size(self):
        """Test that position size doesn't exceed maximum."""
        config = create_test_config(
            position_sizing_strategy="kelly",
            kelly_fraction=1.0,  # Full Kelly
            max_position_size=100.0
        )
        sizer = PositionSizer(config)
        
        position_size = sizer.calculate_position_size(
            opportunity_profit_pct=10.0,
            opportunity_confidence=0.90,
            available_capital=100000.0  # Large capital
        )
        
        # Should cap at max_position_size
        assert position_size <= 100.0
    
    def test_low_confidence_reduces_size(self):
        """Test that low confidence reduces position size."""
        config = create_test_config(
            position_sizing_strategy="kelly",
            kelly_fraction=0.25
        )
        sizer = PositionSizer(config)
        
        high_confidence_size = sizer.calculate_position_size(
            opportunity_profit_pct=5.0,
            opportunity_confidence=0.90,
            available_capital=10000.0
        )
        
        low_confidence_size = sizer.calculate_position_size(
            opportunity_profit_pct=5.0,
            opportunity_confidence=0.50,
            available_capital=10000.0
        )
        
        # Low confidence should result in smaller position
        assert low_confidence_size < high_confidence_size
    
    def test_insufficient_capital(self):
        """Test behavior with insufficient capital."""
        config = create_test_config()
        sizer = PositionSizer(config)
        
        position_size = sizer.calculate_position_size(
            opportunity_profit_pct=5.0,
            opportunity_confidence=0.80,
            available_capital=10.0  # Very low capital
        )
        
        # Should return small position or scale appropriately
        assert position_size <= 10.0


class TestPositionSizerEdgeCases:
    """Test edge cases for position sizing."""
    
    def test_zero_capital(self):
        """Test with zero available capital."""
        config = create_test_config()
        sizer = PositionSizer(config)
        
        position_size = sizer.calculate_position_size(
            opportunity_profit_pct=5.0,
            opportunity_confidence=0.80,
            available_capital=0.0
        )
        
        # Should return 0 or very small value
        assert position_size <= 1.0
    
    def test_negative_profit(self):
        """Test with negative profit percentage."""
        config = create_test_config()
        sizer = PositionSizer(config)
        
        position_size = sizer.calculate_position_size(
            opportunity_profit_pct=-5.0,
            opportunity_confidence=0.80,
            available_capital=10000.0
        )
        
        # Should return 0 or very small position
        assert position_size <= 1.0
    
    def test_very_high_profit(self):
        """Test with unrealistically high profit."""
        config = create_test_config()
        sizer = PositionSizer(config)
        
        position_size = sizer.calculate_position_size(
            opportunity_profit_pct=100.0,  # 100% profit!
            opportunity_confidence=0.90,
            available_capital=10000.0
        )
        
        # Should still respect max_position_size
        assert position_size <= config.max_position_size
    
    def test_fractional_kelly_reduces_risk(self):
        """Test that fractional Kelly is more conservative than full Kelly."""
        full_kelly_config = create_test_config(kelly_fraction=1.0)
        fractional_kelly_config = create_test_config(kelly_fraction=0.25)
        
        full_kelly_sizer = PositionSizer(full_kelly_config)
        fractional_kelly_sizer = PositionSizer(fractional_kelly_config)
        
        params = {
            "opportunity_profit_pct": 10.0,
            "opportunity_confidence": 0.80,
            "available_capital": 10000.0
        }
        
        full_size = full_kelly_sizer.calculate_position_size(**params)
        fractional_size = fractional_kelly_sizer.calculate_position_size(**params)
        
        # Fractional Kelly should be smaller (more conservative)
        assert fractional_size < full_size
