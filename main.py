"""
Polymarket Arbitrage Bot - Main Application
Real-time monitoring and arbitrage detection for Polymarket
"""
import asyncio
import logging
import os
from typing import List
from dotenv import load_dotenv

from polymarket_client import PolymarketWSClient
from arbitrage_detector import ArbitrageDetector, ArbitrageOpportunity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PolymarketArbitrageBot:
    """Main bot for monitoring Polymarket and detecting arbitrage opportunities"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.ws_url = os.getenv('POLYMARKET_WS_URL', 'wss://ws-subscriptions-clob.polymarket.com/ws/market')
        self.min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.01'))
        
        # Initialize components
        self.ws_client = PolymarketWSClient(self.ws_url)
        self.arbitrage_detector = ArbitrageDetector(
            min_profit_threshold=self.min_profit_threshold
        )
        
        # Add price callback
        self.ws_client.add_price_callback(self.on_price_update)
        
        # Track opportunities
        self.detected_opportunities: List[ArbitrageOpportunity] = []
        
    async def on_price_update(self, price_data: dict):
        """Callback for when price data is updated"""
        market_id = price_data.get('market_id')
        logger.debug(f"Price update for market {market_id}: "
                    f"YES={price_data.get('yes_price')}, "
                    f"NO={price_data.get('no_price')}")
        
        # Periodically check for arbitrage opportunities
        # (In practice, you might want to do this less frequently)
        await self.check_for_arbitrage()
    
    async def check_for_arbitrage(self):
        """Check all markets for arbitrage opportunities"""
        market_data = self.ws_client.get_all_markets()
        
        if len(market_data) < 2:
            return  # Need at least 2 markets to detect arbitrage
        
        opportunities = self.arbitrage_detector.detect_all_opportunities(market_data)
        
        # Alert on new opportunities
        for opp in opportunities:
            # Check if this is a new opportunity (simple deduplication)
            if not self._is_duplicate_opportunity(opp):
                self.detected_opportunities.append(opp)
                self.alert_opportunity(opp)
    
    def _is_duplicate_opportunity(self, opp: ArbitrageOpportunity) -> bool:
        """Check if opportunity is similar to recently detected ones"""
        # Simple deduplication: check last 10 opportunities
        recent = self.detected_opportunities[-10:]
        for recent_opp in recent:
            if (recent_opp.type == opp.type and 
                set(recent_opp.markets) == set(opp.markets) and
                abs(recent_opp.expected_profit - opp.expected_profit) < 0.001):
                return True
        return False
    
    def alert_opportunity(self, opportunity: ArbitrageOpportunity):
        """Alert when an arbitrage opportunity is detected"""
        logger.info("=" * 80)
        logger.info(f"🚨 ARBITRAGE OPPORTUNITY DETECTED!")
        logger.info(f"Type: {opportunity.type}")
        logger.info(f"Expected Profit: {opportunity.expected_profit:.4%}")
        logger.info(f"Markets Involved: {len(opportunity.markets)}")
        logger.info(f"Details: {opportunity.details}")
        logger.info("=" * 80)
    
    async def subscribe_to_markets(self, market_ids: List[str]):
        """Subscribe to a list of market IDs"""
        logger.info(f"Subscribing to {len(market_ids)} markets...")
        await self.ws_client.subscribe_to_markets(market_ids)
    
    async def start(self, market_ids: List[str] = None):
        """Start the arbitrage bot"""
        logger.info("Starting Polymarket Arbitrage Bot...")
        
        try:
            # Connect to WebSocket
            await self.ws_client.connect()
            
            # Subscribe to markets
            if market_ids:
                await self.subscribe_to_markets(market_ids)
            else:
                logger.warning("No market IDs provided. Bot will not monitor any markets.")
                logger.warning("Use bot.subscribe_to_markets(market_ids) to add markets.")
            
            # Start listening for price updates
            logger.info("Bot is now monitoring for arbitrage opportunities...")
            await self.ws_client.listen()
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot and cleanup"""
        logger.info("Stopping bot...")
        await self.ws_client.close()
        
        # Print summary
        logger.info(f"Total opportunities detected: {len(self.detected_opportunities)}")
        if self.detected_opportunities:
            total_profit = sum(opp.expected_profit for opp in self.detected_opportunities)
            logger.info(f"Total potential profit: {total_profit:.4%}")
    
    def get_opportunities(self) -> List[ArbitrageOpportunity]:
        """Get all detected opportunities"""
        return self.detected_opportunities.copy()


async def main():
    """Main entry point"""
    bot = PolymarketArbitrageBot()
    
    # Example market IDs (replace with actual Polymarket market IDs)
    # In production, you would fetch these from the Polymarket API
    example_market_ids = [
        "market-1",
        "market-2", 
        "market-3"
    ]
    
    logger.info("=" * 80)
    logger.info("Polymarket Multi-Market Arbitrage Detection Bot")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Features:")
    logger.info("  ✓ Cross-market arbitrage detection")
    logger.info("  ✓ YES/NO imbalance arbitrage detection")
    logger.info("  ✓ Multi-leg arbitrage detection")
    logger.info("  ✓ Real-time WebSocket monitoring")
    logger.info("")
    logger.info("=" * 80)
    
    await bot.start(example_market_ids)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
