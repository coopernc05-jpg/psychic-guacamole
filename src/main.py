"""Main entry point for Polymarket Arbitrage Bot."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

from .config import load_config
from .market.polymarket_api import PolymarketAPIClient
from .market.websocket_client import WebSocketClient
from .arbitrage.detector import ArbitrageDetector
from .arbitrage.scorer import OpportunityScorer
from .execution.position_sizing import CapitalAllocator
from .execution.executor import TradeExecutor
from .execution.risk_manager import RiskManager
from .analytics.logger import OpportunityLogger, ExecutionLogger
from .analytics.performance import PerformanceTracker
from .notifications.discord import DiscordNotifier
from .notifications.telegram import TelegramNotifier


class PolymarketArbitrageBot:
    """Main orchestrator for the arbitrage bot."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the bot.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)

        # Setup logging
        self._setup_logging()

        # Initialize components
        self.api_client = PolymarketAPIClient(self.config)
        self.ws_client = (
            WebSocketClient(self.config) if self.config.websocket_enabled else None
        )
        self.detector = ArbitrageDetector(self.config)
        self.scorer = OpportunityScorer(self.config)
        self.allocator = CapitalAllocator(self.config)
        self.executor = TradeExecutor(self.config)
        self.risk_manager = RiskManager(self.config)

        # Analytics and logging
        self.opp_logger = OpportunityLogger()
        self.exec_logger = ExecutionLogger()
        self.performance_tracker = PerformanceTracker(self.config.initial_capital)

        # Notifications
        self.discord = DiscordNotifier(self.config)
        self.telegram = TelegramNotifier(self.config)

        # State
        self.is_running = False
        self.markets = []

        logger.info("Polymarket Arbitrage Bot initialized")
        logger.info(f"Mode: {self.config.mode}")
        logger.info(f"Strategies: {', '.join(self.config.strategies)}")

    def _setup_logging(self):
        """Setup logging configuration."""
        # Remove default handler
        logger.remove()

        # Add console handler
        logger.add(
            sys.stdout,
            level=self.config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        )

        # Add file handler
        log_dir = Path(self.config.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            self.config.log_file,
            level=self.config.log_level,
            rotation=self.config.log_rotation,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
        )

    async def start(self):
        """Start the arbitrage bot."""
        self.is_running = True
        logger.info("Starting Polymarket Arbitrage Bot...")

        try:
            # Connect to API
            await self.api_client.connect()

            # Connect to WebSocket if enabled
            if self.ws_client:
                await self.ws_client.connect()
                self.ws_client.register_callback(self._on_market_update)

                # Start WebSocket listener in background
                asyncio.create_task(self.ws_client.listen())

            # Start main loop
            await self._main_loop()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
            if self.config.alert_on_errors:
                self.discord.send_error_alert(f"Fatal error: {e}")
                await self.telegram.send_error_alert(f"Fatal error: {e}")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the arbitrage bot."""
        self.is_running = False
        logger.info("Stopping Polymarket Arbitrage Bot...")

        # Close connections
        if self.ws_client:
            await self.ws_client.disconnect()
        await self.api_client.close()

        # Generate final report
        self._generate_final_report()

        logger.info("Bot stopped successfully")

    async def _main_loop(self):
        """Main processing loop."""
        iteration = 0

        while self.is_running:
            iteration += 1
            logger.info(f"Starting iteration {iteration}")

            try:
                # Fetch current markets
                await self._fetch_markets()

                # Detect arbitrage opportunities
                opportunities = self.detector.detect_opportunities(self.markets)

                if not opportunities:
                    logger.info("No opportunities detected in this iteration")
                else:
                    # Filter profitable opportunities
                    gas_price = await self.api_client.get_gas_price()
                    profitable = self.detector.filter_profitable_opportunities(
                        opportunities, gas_price
                    )

                    if profitable:
                        # Score and rank opportunities
                        scored = self.scorer.score_opportunities(
                            profitable, self.risk_manager.total_capital
                        )

                        logger.info(f"Found {len(scored)} profitable opportunities")

                        # Process opportunities
                        await self._process_opportunities(scored)
                    else:
                        logger.info("No profitable opportunities after filtering")

                # Check and manage existing positions
                await self._manage_positions()

                # Log iteration metrics
                self._log_iteration_metrics()

                # Wait before next iteration
                await asyncio.sleep(self.config.refresh_interval)

            except Exception as e:
                logger.error(f"Error in main loop iteration: {e}")
                if self.config.alert_on_errors:
                    self.discord.send_error_alert(f"Iteration error: {e}")

    async def _fetch_markets(self):
        """Fetch current market data."""
        try:
            markets_to_fetch = self.config.max_markets

            if (
                isinstance(self.config.markets_to_monitor, str)
                and self.config.markets_to_monitor == "all"
            ):
                self.markets = await self.api_client.get_markets(limit=markets_to_fetch)
            elif isinstance(self.config.markets_to_monitor, list):
                all_markets = []
                for category in self.config.markets_to_monitor:
                    markets = await self.api_client.get_markets(
                        category=category,
                        limit=markets_to_fetch // len(self.config.markets_to_monitor),
                    )
                    all_markets.extend(markets)
                self.markets = all_markets
            else:
                self.markets = await self.api_client.get_markets(limit=markets_to_fetch)

            logger.debug(f"Fetched {len(self.markets)} markets")

        except Exception as e:
            logger.error(f"Error fetching markets: {e}")

    async def _process_opportunities(self, scored_opportunities: list):
        """Process and potentially execute opportunities.

        Args:
            scored_opportunities: List of scored opportunities
        """
        # Allocate capital to opportunities
        current_exposure = self.risk_manager.current_exposure
        allocation = self.allocator.allocate_capital(
            scored_opportunities, self.risk_manager.total_capital, current_exposure
        )

        for opp_idx, position_size in allocation.items():
            scored_opp = scored_opportunities[opp_idx]

            # Log opportunity
            self.opp_logger.log_opportunity(scored_opp)

            # Send alert
            if self.config.alert_on_opportunities:
                self.discord.send_opportunity_alert(scored_opp, position_size)
                await self.telegram.send_opportunity_alert(scored_opp, position_size)

            # Execute if in auto-trade mode
            if self.config.mode == "auto_trade":
                # Check risk limits
                can_open, reason = self.risk_manager.can_open_position(position_size)

                if can_open:
                    trades = await self.executor.execute_opportunity(
                        scored_opp, position_size
                    )

                    if trades:
                        # Log executions
                        for trade in trades:
                            self.exec_logger.log_trade(trade)
                            self.performance_tracker.add_trade(trade)

                        # Send execution alert
                        if self.config.alert_on_executions:
                            net_profit = sum(t.net_amount for t in trades)
                            self.discord.send_execution_alert(trades, net_profit)
                            await self.telegram.send_execution_alert(trades, net_profit)
                else:
                    logger.warning(f"Cannot open position: {reason}")

    async def _manage_positions(self):
        """Manage existing positions (stop losses, profit taking)."""
        if self.config.mode != "auto_trade":
            return

        # Update position prices
        market_prices = {m.market_id: m for m in self.markets}
        self.risk_manager.update_position_prices(market_prices)

        # Check stop losses
        to_close_sl = self.risk_manager.check_stop_losses()

        # Check position age
        to_close_age = self.risk_manager.check_position_age()

        # Close positions
        for position_id in set(to_close_sl + to_close_age):
            # In production, this would execute closing trades
            logger.info(f"Closing position {position_id}")
            # self.risk_manager.remove_position(position_id)

    def _log_iteration_metrics(self):
        """Log metrics for current iteration."""
        metrics = self.performance_tracker.calculate_metrics()
        risk_metrics = self.risk_manager.get_risk_metrics()

        logger.info(
            f"Capital: ${risk_metrics['total_capital']:.2f}, "
            f"Exposure: ${risk_metrics['current_exposure']:.2f} "
            f"({risk_metrics['exposure_percentage']:.1f}%), "
            f"Open Positions: {risk_metrics['open_positions']}"
        )

    def _generate_final_report(self):
        """Generate and log final performance report."""
        report = self.performance_tracker.generate_report()
        logger.info("\n" + report)

        # Send performance report
        metrics = self.performance_tracker.calculate_metrics().to_dict()
        self.discord.send_performance_report(metrics)

        # Note: Telegram is async, so we can't easily call it here
        # In production, you'd want to handle this better

    async def _on_market_update(self, update: dict):
        """Handle real-time market update from WebSocket.

        Args:
            update: Market update data
        """
        # Update market in our list
        market_id = update.get("market_id")

        for i, market in enumerate(self.markets):
            if market.market_id == market_id:
                # Update prices
                market.yes_price = update.get("yes_price", market.yes_price)
                market.no_price = update.get("no_price", market.no_price)
                market.yes_bid = update.get("yes_bid", market.yes_bid)
                market.yes_ask = update.get("yes_ask", market.yes_ask)
                market.no_bid = update.get("no_bid", market.no_bid)
                market.no_ask = update.get("no_ask", market.no_ask)
                break


async def main():
    """Main entry point."""
    bot = PolymarketArbitrageBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
