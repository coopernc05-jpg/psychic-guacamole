"""Telegram bot notifications."""

import asyncio
from typing import Optional, Dict, Any
from loguru import logger

try:
    from telegram import Bot
    from telegram.error import TelegramError

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed, Telegram notifications disabled")

from ..config import Config
from ..arbitrage.scorer import ScoredOpportunity


class TelegramNotifier:
    """Send notifications via Telegram bot."""

    def __init__(self, config: Config):
        """Initialize Telegram notifier.

        Args:
            config: Configuration object
        """
        self.config = config
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.enabled = bool(self.bot_token and self.chat_id and TELEGRAM_AVAILABLE)

        if self.enabled:
            self.bot = Bot(token=self.bot_token)
        else:
            self.bot = None
            logger.info("Telegram notifications disabled")

    async def send_opportunity_alert(
        self, scored_opportunity: ScoredOpportunity, position_size: float
    ):
        """Send an opportunity alert to Telegram.

        Args:
            scored_opportunity: Scored opportunity
            position_size: Recommended position size
        """
        if not self.enabled:
            return

        try:
            opp = scored_opportunity.opportunity

            message = (
                "🎯 *Arbitrage Opportunity Detected!*\n\n"
                f"*Type:* {opp.__class__.__name__}\n"
                f"*Score:* {scored_opportunity.score:.2f}/100\n"
                f"*Profit Score:* {scored_opportunity.profit_score:.2f}\n"
                f"*Confidence:* {scored_opportunity.confidence_score:.2f}\n"
                f"*Position Size:* ${position_size:.2f}\n\n"
                f"*Details:*\n{str(opp)}"
            )

            await self.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode="Markdown"
            )

            logger.debug("Sent Telegram notification")

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    async def send_execution_alert(self, trades: list, net_profit: float):
        """Send a trade execution alert to Telegram.

        Args:
            trades: List of executed trades
            net_profit: Net profit from execution
        """
        if not self.enabled:
            return

        try:
            message = (
                "✅ *Trades Executed*\n\n"
                f"*Number of Trades:* {len(trades)}\n"
                f"*Net Profit:* ${net_profit:.2f}"
            )

            await self.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Failed to send Telegram execution alert: {e}")

    async def send_error_alert(self, error_message: str):
        """Send an error alert to Telegram.

        Args:
            error_message: Error message to send
        """
        if not self.enabled:
            return

        try:
            message = f"⚠️ *Error Alert*\n\n{error_message}"

            await self.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Failed to send Telegram error alert: {e}")

    async def send_performance_report(self, metrics: Dict[str, Any]):
        """Send a performance report to Telegram.

        Args:
            metrics: Performance metrics dictionary
        """
        if not self.enabled:
            return

        try:
            message = (
                "📊 *Performance Report*\n\n"
                f"*Net P&L:* ${metrics.get('net_pnl', 0):.2f}\n"
                f"*ROI:* {metrics.get('roi', 0):.2f}%\n"
                f"*Win Rate:* {metrics.get('win_rate', 0):.2f}%\n"
                f"*Total Trades:* {metrics.get('total_trades', 0)}\n"
                f"*Sharpe Ratio:* {metrics.get('sharpe_ratio', 0):.2f}"
            )

            await self.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Failed to send Telegram performance report: {e}")
