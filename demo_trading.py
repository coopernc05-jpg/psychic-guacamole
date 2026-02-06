"""
Demo script to test automatic trade execution with mock data
This demonstrates the trading functionality in dry-run mode
"""
import asyncio
import logging
from datetime import datetime
from arbitrage_detector import ArbitrageDetector, ArbitrageOpportunity
from trade_executor import TradeExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_opportunities():
    """Create mock arbitrage opportunities for testing"""
    
    # Opportunity 1: YES/NO imbalance
    opp1 = ArbitrageOpportunity(
        type='yes_no_imbalance',
        markets=['market-1'],
        expected_profit=0.03,
        details={
            'event_name': 'Presidential Election - Candidate A Wins',
            'yes_ask': 0.48,
            'no_ask': 0.49,
            'total_cost': 0.97,
            'strategy': 'Buy both YES and NO'
        },
        timestamp=datetime.now().isoformat()
    )
    
    # Opportunity 2: Cross-market arbitrage
    opp2 = ArbitrageOpportunity(
        type='cross_market',
        markets=['market-2', 'market-3'],
        expected_profit=0.05,
        details={
            'event_name': 'Presidential Election',
            'market1_yes_ask': 0.46,
            'market2_yes_ask': 0.49,
            'total_cost': 0.95,
            'strategy': 'Buy YES on both markets'
        },
        timestamp=datetime.now().isoformat()
    )
    
    # Opportunity 3: Multi-leg arbitrage
    opp3 = ArbitrageOpportunity(
        type='multi_leg',
        markets=['market-4', 'market-5', 'market-6'],
        expected_profit=0.07,
        details={
            'event_name': 'Tournament Winner',
            'num_legs': 3,
            'total_cost': 0.93,
            'markets_info': {
                'market-4': {'outcome': 'Team A', 'yes_ask': 0.31},
                'market-5': {'outcome': 'Team B', 'yes_ask': 0.33},
                'market-6': {'outcome': 'Team C', 'yes_ask': 0.29}
            },
            'strategy': 'Buy YES on all markets'
        },
        timestamp=datetime.now().isoformat()
    )
    
    return [opp1, opp2, opp3]


async def main():
    """Run the demo"""
    logger.info("=" * 80)
    logger.info("Polymarket Trade Executor - Demo Mode")
    logger.info("=" * 80)
    logger.info("")
    
    # Create trade executor in dry-run mode
    executor = TradeExecutor(
        api_url="https://clob.polymarket.com",
        max_trade_size=100.0,
        dry_run=True  # Always use dry-run in demo!
    )
    
    logger.info("Configuration:")
    logger.info(f"  Mode: DRY-RUN (no real trades)")
    logger.info(f"  Max Trade Size: ${executor.max_trade_size:.2f}")
    logger.info("")
    
    # Generate mock opportunities
    logger.info("Generating mock arbitrage opportunities...")
    opportunities = create_mock_opportunities()
    logger.info(f"Created {len(opportunities)} mock opportunities")
    logger.info("")
    
    # Execute each opportunity
    async with executor:
        for i, opportunity in enumerate(opportunities, 1):
            logger.info("=" * 80)
            logger.info(f"OPPORTUNITY #{i}")
            logger.info("=" * 80)
            logger.info(f"Type: {opportunity.type.upper().replace('_', ' ')}")
            logger.info(f"Expected Profit: {opportunity.expected_profit:.2%}")
            logger.info(f"Markets: {', '.join(opportunity.markets)}")
            logger.info(f"Strategy: {opportunity.details.get('strategy', 'N/A')}")
            logger.info("")
            
            # Execute the trade
            logger.info("Executing trade...")
            result = await executor.execute_opportunity(opportunity)
            
            logger.info("")
            if result.success:
                logger.info("✅ TRADE EXECUTED SUCCESSFULLY")
                logger.info(f"   Orders Placed: {len(result.orders)}")
                logger.info(f"   Total Invested: ${result.total_invested:.2f}")
                logger.info(f"   Expected Return: ${result.expected_return:.2f}")
                logger.info(f"   Expected Profit: ${result.expected_return - result.total_invested:.2f} "
                          f"({opportunity.expected_profit:.2%})")
                
                logger.info("")
                logger.info("   Order Details:")
                for j, order in enumerate(result.orders, 1):
                    logger.info(f"     Order {j}: {order.side} on {order.market_id}")
                    logger.info(f"       Amount: ${order.amount:.2f}")
                    logger.info(f"       Price: {order.price:.3f}")
                    logger.info(f"       Status: {order.status}")
            else:
                logger.error("❌ TRADE EXECUTION FAILED")
                logger.error(f"   Error: {result.error_message}")
            
            logger.info("")
            
            # Small delay between trades
            await asyncio.sleep(0.5)
    
    # Print summary statistics
    logger.info("=" * 80)
    logger.info("EXECUTION SUMMARY")
    logger.info("=" * 80)
    
    stats = executor.get_execution_stats()
    logger.info(f"Total Executions: {stats['total_executions']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Success Rate: {stats['success_rate']:.1%}")
    logger.info("")
    logger.info(f"Total Invested: ${stats['total_invested']:.2f}")
    logger.info(f"Expected Returns: ${stats['expected_returns']:.2f}")
    logger.info(f"Expected Profit: ${stats['expected_profit']:.2f} "
               f"({stats['expected_profit']/stats['total_invested']:.2%})")
    logger.info("")
    logger.info("=" * 80)
    logger.info("Demo completed successfully!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
