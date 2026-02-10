"""
Demo script to test arbitrage detection with mock data
This allows testing the arbitrage detection logic without requiring live WebSocket data
"""
import asyncio
import logging
from datetime import datetime
from arbitrage_detector import ArbitrageDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_market_data():
    """Create mock market data for testing"""
    
    # Scenario 1: YES/NO imbalance in a single market (profitable)
    market1 = {
        "market_id": "market-1",
        "yes_price": 0.48,
        "no_price": 0.47,
        "yes_bid": 0.47,
        "yes_ask": 0.49,
        "no_bid": 0.46,
        "no_ask": 0.48,
        "timestamp": datetime.now().isoformat(),
        "event_name": "Presidential Election - Candidate A Wins",
        "outcome": "YES"
    }
    
    # Scenario 2: Cross-market arbitrage (same event, different outcomes)
    market2 = {
        "market_id": "market-2",
        "yes_price": 0.45,
        "no_price": 0.55,
        "yes_bid": 0.44,
        "yes_ask": 0.46,
        "no_bid": 0.54,
        "no_ask": 0.56,
        "timestamp": datetime.now().isoformat(),
        "event_name": "Presidential Election",
        "outcome": "Candidate A"
    }
    
    market3 = {
        "market_id": "market-3",
        "yes_price": 0.48,
        "no_price": 0.52,
        "yes_bid": 0.47,
        "yes_ask": 0.49,
        "no_bid": 0.51,
        "no_ask": 0.53,
        "timestamp": datetime.now().isoformat(),
        "event_name": "Presidential Election",
        "outcome": "Candidate B"
    }
    
    # Scenario 3: Multi-leg arbitrage (3 mutually exclusive outcomes)
    market4 = {
        "market_id": "market-4",
        "yes_price": 0.30,
        "no_price": 0.70,
        "yes_bid": 0.29,
        "yes_ask": 0.31,
        "no_bid": 0.69,
        "no_ask": 0.71,
        "timestamp": datetime.now().isoformat(),
        "event_name": "Tournament Winner",
        "outcome": "Team A"
    }
    
    market5 = {
        "market_id": "market-5",
        "yes_price": 0.32,
        "no_price": 0.68,
        "yes_bid": 0.31,
        "yes_ask": 0.33,
        "no_bid": 0.67,
        "no_ask": 0.69,
        "timestamp": datetime.now().isoformat(),
        "event_name": "Tournament Winner",
        "outcome": "Team B"
    }
    
    market6 = {
        "market_id": "market-6",
        "yes_price": 0.28,
        "no_price": 0.72,
        "yes_bid": 0.27,
        "yes_ask": 0.29,
        "no_bid": 0.71,
        "no_ask": 0.73,
        "timestamp": datetime.now().isoformat(),
        "event_name": "Tournament Winner",
        "outcome": "Team C"
    }
    
    return {
        "market-1": market1,
        "market-2": market2,
        "market-3": market3,
        "market-4": market4,
        "market-5": market5,
        "market-6": market6
    }


def print_opportunity_details(opportunity):
    """Pretty print an arbitrage opportunity"""
    print("\n" + "=" * 80)
    print(f"🎯 ARBITRAGE OPPORTUNITY FOUND")
    print("=" * 80)
    print(f"Type: {opportunity.type.upper().replace('_', ' ')}")
    print(f"Expected Profit: {opportunity.expected_profit:.4%}")
    print(f"Markets Involved: {len(opportunity.markets)}")
    print(f"\nMarket IDs:")
    for market_id in opportunity.markets:
        print(f"  - {market_id}")
    print(f"\nStrategy Details:")
    for key, value in opportunity.details.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    print("=" * 80 + "\n")


def main():
    """Run the demo"""
    logger.info("=" * 80)
    logger.info("Polymarket Arbitrage Detector - Demo Mode")
    logger.info("=" * 80)
    logger.info("")
    
    # Create detector with 1% minimum profit threshold
    detector = ArbitrageDetector(min_profit_threshold=0.01)
    
    # Generate mock data
    logger.info("Generating mock market data...")
    market_data = create_mock_market_data()
    
    logger.info(f"Created {len(market_data)} mock markets")
    logger.info("")
    
    # Display market data
    logger.info("Market Data:")
    logger.info("-" * 80)
    for market_id, data in market_data.items():
        logger.info(f"\n{market_id}:")
        logger.info(f"  Event: {data['event_name']}")
        logger.info(f"  Outcome: {data.get('outcome', 'N/A')}")
        logger.info(f"  YES: bid={data['yes_bid']:.3f}, ask={data['yes_ask']:.3f}")
        logger.info(f"  NO:  bid={data['no_bid']:.3f}, ask={data['no_ask']:.3f}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Detecting Arbitrage Opportunities...")
    logger.info("=" * 80)
    
    # Detect all opportunities
    opportunities = detector.detect_all_opportunities(market_data)
    
    if not opportunities:
        logger.warning("No arbitrage opportunities found!")
        logger.info("Try adjusting the MIN_PROFIT_THRESHOLD or market data")
    else:
        logger.info(f"\n✅ Found {len(opportunities)} arbitrage opportunity(ies)!\n")
        
        # Print each opportunity
        for i, opp in enumerate(opportunities, 1):
            print(f"\nOpportunity #{i}:")
            print_opportunity_details(opp)
        
        # Summary
        total_profit = sum(opp.expected_profit for opp in opportunities)
        logger.info("=" * 80)
        logger.info(f"SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Opportunities: {len(opportunities)}")
        logger.info(f"Total Potential Profit: {total_profit:.4%}")
        
        # Breakdown by type
        by_type = {}
        for opp in opportunities:
            by_type[opp.type] = by_type.get(opp.type, 0) + 1
        
        logger.info("\nOpportunities by Type:")
        for opp_type, count in by_type.items():
            logger.info(f"  {opp_type}: {count}")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
