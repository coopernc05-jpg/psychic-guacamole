"""
Unit tests for arbitrage detection
Run with: python -m pytest test_arbitrage.py -v
or: python test_arbitrage.py
"""
import unittest
from datetime import datetime
from arbitrage_detector import ArbitrageDetector, ArbitrageOpportunity


class TestArbitrageDetector(unittest.TestCase):
    """Test cases for ArbitrageDetector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = ArbitrageDetector(min_profit_threshold=0.01)
    
    def test_yes_no_imbalance_buy_both(self):
        """Test YES/NO imbalance detection when buying is profitable"""
        market_data = {
            "market-1": {
                "market_id": "market-1",
                "yes_ask": 0.48,
                "no_ask": 0.48,
                "yes_bid": 0.45,
                "no_bid": 0.45,
                "event_name": "Test Event"
            }
        }
        
        opportunities = self.detector.detect_yes_no_imbalance(market_data)
        
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].type, 'yes_no_imbalance')
        self.assertAlmostEqual(opportunities[0].expected_profit, 0.04, places=2)
    
    def test_yes_no_imbalance_sell_both(self):
        """Test YES/NO imbalance detection when selling is profitable"""
        market_data = {
            "market-1": {
                "market_id": "market-1",
                "yes_bid": 0.52,
                "no_bid": 0.52,
                "yes_ask": 0.55,
                "no_ask": 0.55,
                "event_name": "Test Event"
            }
        }
        
        opportunities = self.detector.detect_yes_no_imbalance(market_data)
        
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].type, 'yes_no_imbalance')
        self.assertAlmostEqual(opportunities[0].expected_profit, 0.04, places=2)
    
    def test_cross_market_arbitrage(self):
        """Test cross-market arbitrage detection"""
        market_data = {
            "market-1": {
                "market_id": "market-1",
                "yes_ask": 0.45,
                "no_ask": 0.55,
                "yes_bid": 0.43,
                "no_bid": 0.53,
                "event_name": "Election",
                "outcome": "Candidate A"
            },
            "market-2": {
                "market_id": "market-2",
                "yes_ask": 0.50,
                "no_ask": 0.50,
                "yes_bid": 0.48,
                "no_bid": 0.48,
                "event_name": "Election",
                "outcome": "Candidate B"
            }
        }
        
        opportunities = self.detector.detect_cross_market_arbitrage(market_data)
        
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].type, 'cross_market')
        self.assertAlmostEqual(opportunities[0].expected_profit, 0.05, places=2)
    
    def test_multi_leg_arbitrage(self):
        """Test multi-leg arbitrage detection"""
        market_data = {
            "market-1": {
                "market_id": "market-1",
                "yes_ask": 0.30,
                "no_ask": 0.70,
                "yes_bid": 0.28,
                "no_bid": 0.68,
                "event_name": "Tournament",
                "outcome": "Team A"
            },
            "market-2": {
                "market_id": "market-2",
                "yes_ask": 0.30,
                "no_ask": 0.70,
                "yes_bid": 0.28,
                "no_bid": 0.68,
                "event_name": "Tournament",
                "outcome": "Team B"
            },
            "market-3": {
                "market_id": "market-3",
                "yes_ask": 0.30,
                "no_ask": 0.70,
                "yes_bid": 0.28,
                "no_bid": 0.68,
                "event_name": "Tournament",
                "outcome": "Team C"
            }
        }
        
        opportunities = self.detector.detect_multi_leg_arbitrage(market_data)
        
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].type, 'multi_leg')
        self.assertEqual(len(opportunities[0].markets), 3)
        self.assertAlmostEqual(opportunities[0].expected_profit, 0.10, places=2)
    
    def test_no_arbitrage_opportunity(self):
        """Test when no arbitrage exists (efficient pricing)"""
        market_data = {
            "market-1": {
                "market_id": "market-1",
                "yes_ask": 0.51,
                "no_ask": 0.51,
                "yes_bid": 0.49,
                "no_bid": 0.49,
                "event_name": "Test Event"
            }
        }
        
        opportunities = self.detector.detect_all_opportunities(market_data)
        
        self.assertEqual(len(opportunities), 0)
    
    def test_min_profit_threshold(self):
        """Test that minimum profit threshold is respected"""
        detector_high_threshold = ArbitrageDetector(min_profit_threshold=0.05)
        
        market_data = {
            "market-1": {
                "market_id": "market-1",
                "yes_ask": 0.48,
                "no_ask": 0.49,  # 3% profit, below 5% threshold
                "yes_bid": 0.45,
                "no_bid": 0.45,
                "event_name": "Test Event"
            }
        }
        
        opportunities = detector_high_threshold.detect_all_opportunities(market_data)
        
        self.assertEqual(len(opportunities), 0)
    
    def test_arbitrage_opportunity_string_representation(self):
        """Test string representation of ArbitrageOpportunity"""
        opp = ArbitrageOpportunity(
            type='yes_no_imbalance',
            markets=['market-1'],
            expected_profit=0.03,
            details={'test': 'data'},
            timestamp=datetime.now().isoformat()
        )
        
        str_repr = str(opp)
        self.assertIn('yes_no_imbalance', str_repr)
        self.assertIn('0.03', str_repr)
        self.assertIn('market-1', str_repr)


class TestArbitrageOpportunity(unittest.TestCase):
    """Test cases for ArbitrageOpportunity dataclass"""
    
    def test_create_opportunity(self):
        """Test creating an ArbitrageOpportunity"""
        opp = ArbitrageOpportunity(
            type='cross_market',
            markets=['market-1', 'market-2'],
            expected_profit=0.05,
            details={'key': 'value'},
            timestamp='2024-01-01T00:00:00'
        )
        
        self.assertEqual(opp.type, 'cross_market')
        self.assertEqual(len(opp.markets), 2)
        self.assertEqual(opp.expected_profit, 0.05)
        self.assertIsInstance(opp.details, dict)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
