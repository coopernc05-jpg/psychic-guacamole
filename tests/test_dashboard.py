"""Tests for the web dashboard."""

import pytest
from unittest.mock import Mock, MagicMock
from src.analytics.dashboard import Dashboard, create_dashboard
from src.analytics.performance import PerformanceTracker
from src.analytics.logger import OpportunityLogger, ExecutionLogger


class TestDashboard:
    """Tests for Dashboard class."""
    
    @pytest.fixture
    def components(self):
        """Create mock components for testing."""
        performance_tracker = PerformanceTracker(initial_capital=1000)
        opportunity_logger = OpportunityLogger()
        execution_logger = ExecutionLogger()
        return performance_tracker, opportunity_logger, execution_logger
    
    def test_dashboard_initialization(self, components):
        """Test dashboard initializes correctly."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log,
            host="127.0.0.1",
            port=5001,
            debug=False
        )
        
        assert dashboard is not None
        assert dashboard.host == "127.0.0.1"
        assert dashboard.port == 5001
        assert dashboard.debug == False
    
    def test_dashboard_factory(self, components):
        """Test dashboard factory function."""
        perf, opp, exec_log = components
        
        dashboard = create_dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        assert dashboard is not None
        assert dashboard.host == "0.0.0.0"
        assert dashboard.port == 5000
    
    def test_dashboard_app_routes(self, components):
        """Test dashboard Flask app has correct routes."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        # Check that routes are registered
        route_rules = [rule.rule for rule in dashboard.app.url_map.iter_rules()]
        
        assert '/' in route_rules
        assert '/api/metrics' in route_rules
        assert '/api/opportunities' in route_rules
        assert '/api/trades' in route_rules
        assert '/api/equity-curve' in route_rules
        assert '/api/health' in route_rules
        assert '/api/config' in route_rules
    
    def test_metrics_endpoint(self, components):
        """Test metrics API endpoint."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        with dashboard.app.test_client() as client:
            response = client.get('/api/metrics')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'metrics' in data
            assert 'capital' in data
            assert data['capital']['initial'] == 1000
    
    def test_health_endpoint(self, components):
        """Test health check endpoint."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        with dashboard.app.test_client() as client:
            response = client.get('/api/health')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'status' in data
            assert data['status'] == 'healthy'
            assert 'timestamp' in data
            assert 'uptime_seconds' in data
    
    def test_opportunities_endpoint(self, components):
        """Test opportunities API endpoint."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        with dashboard.app.test_client() as client:
            response = client.get('/api/opportunities')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'statistics' in data
            assert 'recent' in data
    
    def test_trades_endpoint(self, components):
        """Test trades API endpoint."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        with dashboard.app.test_client() as client:
            response = client.get('/api/trades')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'trade_statistics' in data
            assert 'position_statistics' in data
            assert 'recent_trades' in data
    
    def test_equity_curve_endpoint(self, components):
        """Test equity curve API endpoint."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        with dashboard.app.test_client() as client:
            response = client.get('/api/equity-curve')
            assert response.status_code == 200
            
            data = response.get_json()
            assert isinstance(data, list)
            # Should have at least one data point (initial capital)
            assert len(data) >= 1
            if len(data) > 0:
                assert 'timestamp' in data[0]
                assert 'value' in data[0]
    
    def test_log_opportunity(self, components):
        """Test logging opportunity to dashboard."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        opp_data = {
            'opportunity_type': 'TestOpportunity',
            'score': 85.5,
            'profit_score': 78.2
        }
        
        dashboard.log_opportunity(opp_data)
        
        assert len(dashboard.recent_opportunities) == 1
        assert dashboard.recent_opportunities[0] == opp_data
    
    def test_log_trade(self, components):
        """Test logging trade to dashboard."""
        perf, opp, exec_log = components
        
        dashboard = Dashboard(
            performance_tracker=perf,
            opportunity_logger=opp,
            execution_logger=exec_log
        )
        
        trade_data = {
            'trade_id': '123',
            'side': 'BUY',
            'price': 0.55,
            'size': 100
        }
        
        dashboard.log_trade(trade_data)
        
        assert len(dashboard.recent_trades) == 1
        assert dashboard.recent_trades[0] == trade_data
