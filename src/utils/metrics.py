"""Prometheus metrics export for monitoring."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any


# Define metrics
opportunities_detected = Counter(
    'arbitrage_opportunities_detected_total',
    'Total number of arbitrage opportunities detected',
    ['strategy_type']
)

trades_executed = Counter(
    'trades_executed_total',
    'Total number of trades executed',
    ['outcome', 'side']
)

trade_pnl = Histogram(
    'trade_pnl_dollars',
    'Profit/loss per trade in USD',
    buckets=[-100, -50, -10, -5, -1, 0, 1, 5, 10, 50, 100]
)

portfolio_value = Gauge(
    'portfolio_value_usd',
    'Current portfolio value in USD'
)

win_rate = Gauge(
    'win_rate_percentage',
    'Current win rate percentage'
)

active_positions = Gauge(
    'active_positions_count',
    'Number of currently active positions'
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint']
)

api_errors = Counter(
    'api_errors_total',
    'Total API errors',
    ['error_type']
)


class MetricsExporter:
    """Export metrics in Prometheus format."""
    
    @staticmethod
    def update_from_performance(metrics: Dict[str, Any]):
        """Update metrics from performance tracker.
        
        Args:
            metrics: Performance metrics dictionary
        """
        portfolio_value.set(metrics.get('current_capital', 0))
        win_rate.set(metrics.get('win_rate', 0))
    
    @staticmethod
    def record_opportunity(strategy_type: str):
        """Record detected opportunity.
        
        Args:
            strategy_type: Type of arbitrage strategy
        """
        opportunities_detected.labels(strategy_type=strategy_type).inc()
    
    @staticmethod
    def record_trade(outcome: str, side: str, pnl: float = 0):
        """Record executed trade.
        
        Args:
            outcome: Trade outcome (YES/NO)
            side: Trade side (BUY/SELL)
            pnl: Profit/loss amount
        """
        trades_executed.labels(outcome=outcome, side=side).inc()
        if pnl != 0:
            trade_pnl.observe(pnl)
    
    @staticmethod
    def set_active_positions(count: int):
        """Set number of active positions.
        
        Args:
            count: Number of active positions
        """
        active_positions.set(count)
    
    @staticmethod
    def record_api_call(endpoint: str, duration: float, error: str = None):
        """Record API call metrics.
        
        Args:
            endpoint: API endpoint called
            duration: Request duration in seconds
            error: Error type if request failed
        """
        api_request_duration.labels(endpoint=endpoint).observe(duration)
        if error:
            api_errors.labels(error_type=error).inc()
    
    @staticmethod
    def export_metrics() -> bytes:
        """Export metrics in Prometheus format.
        
        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest()
    
    @staticmethod
    def get_content_type() -> str:
        """Get metrics content type.
        
        Returns:
            Content type string
        """
        return CONTENT_TYPE_LATEST


# Global metrics exporter
metrics_exporter = MetricsExporter()
