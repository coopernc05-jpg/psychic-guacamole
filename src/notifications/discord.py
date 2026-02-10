"""Discord webhook notifications."""

import asyncio
from typing import Optional, Dict, Any
from discord_webhook import DiscordWebhook, DiscordEmbed
from loguru import logger

from ..config import Config
from ..arbitrage.scorer import ScoredOpportunity


class DiscordNotifier:
    """Send notifications via Discord webhook."""

    def __init__(self, config: Config):
        """Initialize Discord notifier.

        Args:
            config: Configuration object
        """
        self.config = config
        self.webhook_url = config.discord_webhook
        self.enabled = bool(self.webhook_url)

        if not self.enabled:
            logger.info("Discord notifications disabled (no webhook URL)")

    def send_opportunity_alert(
        self, scored_opportunity: ScoredOpportunity, position_size: float
    ):
        """Send an opportunity alert to Discord.

        Args:
            scored_opportunity: Scored opportunity
            position_size: Recommended position size
        """
        if not self.enabled:
            return

        try:
            webhook = DiscordWebhook(url=self.webhook_url)

            opp = scored_opportunity.opportunity

            # Create embed
            embed = DiscordEmbed(
                title="🎯 Arbitrage Opportunity Detected!",
                description=f"**Type:** {opp.__class__.__name__}",
                color=0x00FF00,
            )

            # Add fields
            embed.add_embed_field(
                name="Details",
                value=str(opp)[:1024],  # Discord field limit
                inline=False,
            )

            embed.add_embed_field(
                name="Score", value=f"{scored_opportunity.score:.2f}/100", inline=True
            )

            embed.add_embed_field(
                name="Profit Score",
                value=f"{scored_opportunity.profit_score:.2f}",
                inline=True,
            )

            embed.add_embed_field(
                name="Confidence",
                value=f"{scored_opportunity.confidence_score:.2f}",
                inline=True,
            )

            embed.add_embed_field(
                name="Recommended Size", value=f"${position_size:.2f}", inline=True
            )

            embed.set_footer(text="Polymarket Arbitrage Bot")
            embed.set_timestamp()

            webhook.add_embed(embed)
            response = webhook.execute()

            if response.status_code == 200:
                logger.debug("Sent Discord notification")
            else:
                logger.warning(
                    f"Discord webhook returned status {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    def send_execution_alert(self, trades: list, net_profit: float):
        """Send a trade execution alert to Discord.

        Args:
            trades: List of executed trades
            net_profit: Net profit from execution
        """
        if not self.enabled:
            return

        try:
            webhook = DiscordWebhook(url=self.webhook_url)

            embed = DiscordEmbed(
                title="✅ Trades Executed",
                description=f"Executed {len(trades)} trades",
                color=0x0099FF,
            )

            embed.add_embed_field(
                name="Net Profit", value=f"${net_profit:.2f}", inline=True
            )

            embed.add_embed_field(
                name="Number of Trades", value=str(len(trades)), inline=True
            )

            embed.set_footer(text="Polymarket Arbitrage Bot")
            embed.set_timestamp()

            webhook.add_embed(embed)
            webhook.execute()

        except Exception as e:
            logger.error(f"Failed to send Discord execution alert: {e}")

    def send_error_alert(self, error_message: str):
        """Send an error alert to Discord.

        Args:
            error_message: Error message to send
        """
        if not self.enabled:
            return

        try:
            webhook = DiscordWebhook(url=self.webhook_url)

            embed = DiscordEmbed(
                title="⚠️ Error Alert", description=error_message[:2000], color=0xFF0000
            )

            embed.set_footer(text="Polymarket Arbitrage Bot")
            embed.set_timestamp()

            webhook.add_embed(embed)
            webhook.execute()

        except Exception as e:
            logger.error(f"Failed to send Discord error alert: {e}")

    def send_performance_report(self, metrics: Dict[str, Any]):
        """Send a performance report to Discord.

        Args:
            metrics: Performance metrics dictionary
        """
        if not self.enabled:
            return

        try:
            webhook = DiscordWebhook(url=self.webhook_url)

            embed = DiscordEmbed(
                title="📊 Performance Report",
                description="Daily performance summary",
                color=0xFFA500,
            )

            embed.add_embed_field(
                name="Net P&L", value=f"${metrics.get('net_pnl', 0):.2f}", inline=True
            )

            embed.add_embed_field(
                name="ROI", value=f"{metrics.get('roi', 0):.2f}%", inline=True
            )

            embed.add_embed_field(
                name="Win Rate", value=f"{metrics.get('win_rate', 0):.2f}%", inline=True
            )

            embed.add_embed_field(
                name="Total Trades",
                value=str(metrics.get("total_trades", 0)),
                inline=True,
            )

            embed.add_embed_field(
                name="Sharpe Ratio",
                value=f"{metrics.get('sharpe_ratio', 0):.2f}",
                inline=True,
            )

            embed.set_footer(text="Polymarket Arbitrage Bot")
            embed.set_timestamp()

            webhook.add_embed(embed)
            webhook.execute()

        except Exception as e:
            logger.error(f"Failed to send Discord performance report: {e}")
