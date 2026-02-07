"""Trade execution system."""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from loguru import logger

from ..config import Config
from ..market.market_data import Trade, Position, OrderSide, OrderType
from ..arbitrage.detector import Opportunity
from ..arbitrage.scorer import ScoredOpportunity

if TYPE_CHECKING:
    from ..arbitrage.strategies.yes_no_imbalance import YesNoImbalanceOpportunity
    from ..arbitrage.strategies.cross_market import CrossMarketOpportunity
    from ..arbitrage.strategies.multi_leg import MultiLegOpportunity
    from ..arbitrage.strategies.correlated_events import CorrelatedEventsOpportunity


class TradeExecutor:
    """Executes arbitrage trades on Polymarket."""

    def __init__(self, config: Config):
        """Initialize trade executor.

        Args:
            config: Configuration object
        """
        self.config = config
        self.executed_trades: list[Trade] = []
        self.open_positions: Dict[str, Position] = {}
        self.mode = config.mode

    async def execute_opportunity(
        self, scored_opportunity: ScoredOpportunity, position_size: float
    ) -> Optional[list[Trade]]:
        """Execute an arbitrage opportunity.

        Args:
            scored_opportunity: Scored opportunity to execute
            position_size: Size of position in USD

        Returns:
            List of executed trades, or None if execution failed
        """
        if self.mode == "alert":
            # Alert mode: just log the opportunity
            self._log_alert(scored_opportunity, position_size)
            return None

        # Auto-trade mode: execute the trades
        return await self._execute_trades(scored_opportunity, position_size)

    def _log_alert(self, scored_opportunity: ScoredOpportunity, position_size: float):
        """Log an alert for an opportunity.

        Args:
            scored_opportunity: Opportunity to alert on
            position_size: Recommended position size
        """
        opp = scored_opportunity.opportunity
        logger.info("=" * 80)
        logger.info("🎯 ARBITRAGE OPPORTUNITY DETECTED")
        logger.info("=" * 80)
        logger.info(f"Type: {opp.__class__.__name__}")
        logger.info(f"Details: {str(opp)}")
        logger.info(f"Score: {scored_opportunity.score:.2f}/100")
        logger.info(f"Profit Score: {scored_opportunity.profit_score:.2f}")
        logger.info(
            f"Capital Efficiency: {scored_opportunity.capital_efficiency_score:.2f}"
        )
        logger.info(f"Confidence: {scored_opportunity.confidence_score:.2f}")
        logger.info(f"Risk: {scored_opportunity.risk_score:.2f}")
        logger.info(f"Recommended Position Size: ${position_size:.2f}")
        logger.info("=" * 80)

    async def _execute_trades(
        self, scored_opportunity: ScoredOpportunity, position_size: float
    ) -> Optional[list[Trade]]:
        """Execute trades for an opportunity.

        Args:
            scored_opportunity: Opportunity to execute
            position_size: Position size in USD

        Returns:
            List of executed trades
        """
        from ..arbitrage.strategies import (
            YesNoImbalanceOpportunity,
            CrossMarketOpportunity,
            MultiLegOpportunity,
            CorrelatedEventsOpportunity,
        )

        opp = scored_opportunity.opportunity
        trades = []

        try:
            if isinstance(opp, YesNoImbalanceOpportunity):
                trades = await self._execute_yes_no_imbalance(opp, position_size)
            elif isinstance(opp, CrossMarketOpportunity):
                trades = await self._execute_cross_market(opp, position_size)
            elif isinstance(opp, MultiLegOpportunity):
                trades = await self._execute_multi_leg(opp, position_size)
            elif isinstance(opp, CorrelatedEventsOpportunity):
                trades = await self._execute_correlated_events(opp, position_size)
            else:
                logger.error(f"Unknown opportunity type: {type(opp)}")
                return None

            if trades:
                self.executed_trades.extend(trades)
                logger.info(f"Successfully executed {len(trades)} trades")

            return trades

        except Exception as e:
            logger.error(f"Error executing opportunity: {e}")
            return None

    async def _execute_yes_no_imbalance(
        self, opportunity: "YesNoImbalanceOpportunity", position_size: float
    ) -> list[Trade]:
        """Execute YES/NO imbalance arbitrage.

        Args:
            opportunity: YES/NO imbalance opportunity
            position_size: Position size

        Returns:
            List of executed trades
        """
        trades = []
        market_id = opportunity.market.market_id

        if opportunity.action == "buy_both":
            # Buy both YES and NO
            yes_trade = await self._place_order(
                market_id=market_id,
                outcome="YES",
                side=OrderSide.BUY,
                price=opportunity.yes_price,
                size=position_size,
            )
            if yes_trade:
                trades.append(yes_trade)

            no_trade = await self._place_order(
                market_id=market_id,
                outcome="NO",
                side=OrderSide.BUY,
                price=opportunity.no_price,
                size=position_size,
            )
            if no_trade:
                trades.append(no_trade)

        elif opportunity.action == "sell_both":
            # Sell both YES and NO
            yes_trade = await self._place_order(
                market_id=market_id,
                outcome="YES",
                side=OrderSide.SELL,
                price=opportunity.yes_price,
                size=position_size,
            )
            if yes_trade:
                trades.append(yes_trade)

            no_trade = await self._place_order(
                market_id=market_id,
                outcome="NO",
                side=OrderSide.SELL,
                price=opportunity.no_price,
                size=position_size,
            )
            if no_trade:
                trades.append(no_trade)

        return trades

    async def _execute_cross_market(
        self, opportunity: "CrossMarketOpportunity", position_size: float
    ) -> list[Trade]:
        """Execute cross-market arbitrage.

        Args:
            opportunity: Cross-market opportunity
            position_size: Position size

        Returns:
            List of executed trades
        """
        trades = []

        # Buy from cheaper market
        buy_trade = await self._place_order(
            market_id=opportunity.buy_market,
            outcome=opportunity.outcome,
            side=OrderSide.BUY,
            price=opportunity.buy_price,
            size=position_size,
        )
        if buy_trade:
            trades.append(buy_trade)

        # Sell to more expensive market
        sell_trade = await self._place_order(
            market_id=opportunity.sell_market,
            outcome=opportunity.outcome,
            side=OrderSide.SELL,
            price=opportunity.sell_price,
            size=position_size,
        )
        if sell_trade:
            trades.append(sell_trade)

        return trades

    async def _execute_multi_leg(
        self, opportunity: "MultiLegOpportunity", position_size: float
    ) -> list[Trade]:
        """Execute multi-leg arbitrage.

        Args:
            opportunity: Multi-leg opportunity
            position_size: Position size per leg

        Returns:
            List of executed trades
        """
        trades = []

        for leg in opportunity.legs:
            trade = await self._place_order(
                market_id=leg["market_id"],
                outcome=leg["outcome"],
                side=OrderSide.BUY if leg["action"] == "buy" else OrderSide.SELL,
                price=leg["price"],
                size=position_size / len(opportunity.legs),
            )
            if trade:
                trades.append(trade)

        return trades

    async def _execute_correlated_events(
        self, opportunity: "CorrelatedEventsOpportunity", position_size: float
    ) -> list[Trade]:
        """Execute correlated events arbitrage.

        Args:
            opportunity: Correlated events opportunity
            position_size: Position size

        Returns:
            List of executed trades
        """
        trades = []

        # Buy underpriced correlated market
        trade = await self._place_order(
            market_id=opportunity.correlated_market.market_id,
            outcome=opportunity.correlated_outcome,
            side=OrderSide.BUY,
            price=opportunity.actual_probability,
            size=position_size,
        )
        if trade:
            trades.append(trade)

        return trades

    async def _place_order(
        self, market_id: str, outcome: str, side: OrderSide, price: float, size: float
    ) -> Optional[Trade]:
        """Place an order on Polymarket.

        Args:
            market_id: Market ID
            outcome: Outcome (YES/NO)
            side: Buy or sell
            price: Limit price
            size: Position size in USD

        Returns:
            Trade object if successful, None otherwise
        """
        # Mock implementation - in production, this would:
        # 1. Connect to Polymarket API
        # 2. Sign transaction with wallet
        # 3. Submit order to blockchain
        # 4. Wait for confirmation
        # 5. Handle errors and retries

        if self.config.dry_run:
            logger.info(
                f"DRY RUN: Would place {side.value} order for {outcome} on {market_id[:8]}... at {price:.3f} for ${size:.2f}"
            )
            return None

        try:
            # Simulate order placement
            await asyncio.sleep(0.1)  # Simulate network delay

            trade = Trade(
                trade_id=f"trade_{len(self.executed_trades)}_{datetime.now().timestamp()}",
                market_id=market_id,
                outcome=outcome,
                side=side,
                price=price,
                size=size,
                timestamp=datetime.now(),
                gas_cost=2.0,  # Approximate gas cost in USD
            )

            logger.info(
                f"Executed trade: {side.value} {size:.2f} {outcome} @ {price:.3f} on {market_id[:8]}..."
            )

            return trade

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None
