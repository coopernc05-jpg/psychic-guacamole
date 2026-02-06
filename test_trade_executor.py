"""
Unit tests for trade execution
Run with: python -m pytest test_trade_executor.py -v
or: python test_trade_executor.py
"""
import unittest
import asyncio
from datetime import datetime
from trade_executor import TradeExecutor, TradeOrder, ExecutionResult
from arbitrage_detector import ArbitrageOpportunity


class TestTradeExecutor(unittest.TestCase):
    """Test cases for TradeExecutor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.executor = TradeExecutor(
            api_url="https://test.polymarket.com",
            max_trade_size=100.0,
            dry_run=True
        )
    
    def test_initialize_executor(self):
        """Test executor initialization"""
        self.assertEqual(self.executor.api_url, "https://test.polymarket.com")
        self.assertEqual(self.executor.max_trade_size, 100.0)
        self.assertTrue(self.executor.dry_run)
        self.assertIsNone(self.executor.api_key)
    
    def test_trade_order_creation(self):
        """Test TradeOrder dataclass"""
        order = TradeOrder(
            market_id="market-1",
            side="YES",
            amount=50.0,
            price=0.5
        )
        
        self.assertEqual(order.market_id, "market-1")
        self.assertEqual(order.side, "YES")
        self.assertEqual(order.amount, 50.0)
        self.assertEqual(order.price, 0.5)
        self.assertEqual(order.status, "pending")
        self.assertIsNotNone(order.timestamp)
    
    def test_generate_orders_yes_no_imbalance(self):
        """Test order generation for YES/NO imbalance"""
        opportunity = ArbitrageOpportunity(
            type='yes_no_imbalance',
            markets=['market-1'],
            expected_profit=0.03,
            details={
                'yes_ask': 0.48,
                'no_ask': 0.48,
                'event_name': 'Test Event'
            },
            timestamp=datetime.now().isoformat()
        )
        
        orders = self.executor._generate_orders(opportunity)
        
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].side, 'YES')
        self.assertEqual(orders[1].side, 'NO')
        self.assertEqual(orders[0].market_id, 'market-1')
        self.assertEqual(orders[1].market_id, 'market-1')
    
    def test_generate_orders_cross_market(self):
        """Test order generation for cross-market arbitrage"""
        opportunity = ArbitrageOpportunity(
            type='cross_market',
            markets=['market-1', 'market-2'],
            expected_profit=0.05,
            details={
                'market1_yes_ask': 0.45,
                'market2_yes_ask': 0.50,
                'event_name': 'Test Event'
            },
            timestamp=datetime.now().isoformat()
        )
        
        orders = self.executor._generate_orders(opportunity)
        
        self.assertEqual(len(orders), 2)
        self.assertTrue(all(order.side == 'YES' for order in orders))
    
    def test_generate_orders_multi_leg(self):
        """Test order generation for multi-leg arbitrage"""
        opportunity = ArbitrageOpportunity(
            type='multi_leg',
            markets=['market-1', 'market-2', 'market-3'],
            expected_profit=0.07,
            details={
                'markets_info': {
                    'market-1': {'yes_ask': 0.30},
                    'market-2': {'yes_ask': 0.33},
                    'market-3': {'yes_ask': 0.29}
                }
            },
            timestamp=datetime.now().isoformat()
        )
        
        orders = self.executor._generate_orders(opportunity)
        
        self.assertEqual(len(orders), 3)
        self.assertTrue(all(order.side == 'YES' for order in orders))
    
    def test_max_trade_size_limit(self):
        """Test that trade size is limited to max_trade_size"""
        executor = TradeExecutor(
            api_url="https://test.polymarket.com",
            max_trade_size=50.0,
            dry_run=True
        )
        
        opportunity = ArbitrageOpportunity(
            type='yes_no_imbalance',
            markets=['market-1'],
            expected_profit=0.03,
            details={
                'yes_ask': 0.48,
                'no_ask': 0.48,
            },
            timestamp=datetime.now().isoformat()
        )
        
        # Run execution in async context
        async def run_test():
            async with executor:
                result = await executor.execute_opportunity(opportunity)
                return result
        
        result = asyncio.run(run_test())
        
        self.assertTrue(result.success)
        self.assertLessEqual(result.total_invested, 50.0)
    
    def test_dry_run_execution(self):
        """Test dry-run execution"""
        opportunity = ArbitrageOpportunity(
            type='yes_no_imbalance',
            markets=['market-1'],
            expected_profit=0.03,
            details={
                'yes_ask': 0.48,
                'no_ask': 0.48,
            },
            timestamp=datetime.now().isoformat()
        )
        
        async def run_test():
            async with self.executor:
                result = await self.executor.execute_opportunity(opportunity)
                return result
        
        result = asyncio.run(run_test())
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.total_invested)
        self.assertIsNotNone(result.expected_return)
        self.assertEqual(len(result.orders), 2)
        
        # In dry-run, all orders should be marked as filled
        for order in result.orders:
            self.assertEqual(order.status, 'filled')
    
    def test_execution_history(self):
        """Test execution history tracking"""
        opportunity = ArbitrageOpportunity(
            type='yes_no_imbalance',
            markets=['market-1'],
            expected_profit=0.03,
            details={
                'yes_ask': 0.48,
                'no_ask': 0.48,
            },
            timestamp=datetime.now().isoformat()
        )
        
        async def run_test():
            async with self.executor:
                await self.executor.execute_opportunity(opportunity)
                history = self.executor.get_execution_history()
                return history
        
        history = asyncio.run(run_test())
        
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0].success)
    
    def test_execution_stats(self):
        """Test execution statistics"""
        opportunity = ArbitrageOpportunity(
            type='yes_no_imbalance',
            markets=['market-1'],
            expected_profit=0.03,
            details={
                'yes_ask': 0.48,
                'no_ask': 0.48,
            },
            timestamp=datetime.now().isoformat()
        )
        
        async def run_test():
            async with self.executor:
                await self.executor.execute_opportunity(opportunity)
                await self.executor.execute_opportunity(opportunity)
                stats = self.executor.get_execution_stats()
                return stats
        
        stats = asyncio.run(run_test())
        
        self.assertEqual(stats['total_executions'], 2)
        self.assertEqual(stats['successful'], 2)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['success_rate'], 1.0)
        self.assertGreater(stats['total_invested'], 0)
        self.assertGreater(stats['expected_returns'], stats['total_invested'])


class TestExecutionResult(unittest.TestCase):
    """Test cases for ExecutionResult dataclass"""
    
    def test_create_execution_result(self):
        """Test creating an ExecutionResult"""
        opportunity = ArbitrageOpportunity(
            type='yes_no_imbalance',
            markets=['market-1'],
            expected_profit=0.03,
            details={},
            timestamp=datetime.now().isoformat()
        )
        
        result = ExecutionResult(
            success=True,
            opportunity=opportunity,
            orders=[],
            total_invested=100.0,
            expected_return=103.0
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.total_invested, 100.0)
        self.assertEqual(result.expected_return, 103.0)
        self.assertIsNotNone(result.timestamp)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
