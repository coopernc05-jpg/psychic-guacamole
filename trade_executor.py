"""
Trade Executor Module
Handles automatic trade execution on Polymarket
"""
import asyncio
import logging
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import aiohttp
from datetime import datetime

from arbitrage_detector import ArbitrageOpportunity

logger = logging.getLogger(__name__)


@dataclass
class TradeOrder:
    """Represents a trade order"""
    market_id: str
    side: str  # 'YES' or 'NO'
    amount: float  # Amount in USD to invest
    price: float  # Price per share (0-1)
    order_id: Optional[str] = None
    status: str = 'pending'  # 'pending', 'submitted', 'filled', 'failed'
    filled_amount: float = 0.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ExecutionResult:
    """Result of trade execution"""
    success: bool
    opportunity: ArbitrageOpportunity
    orders: List[TradeOrder]
    total_invested: float
    expected_return: float
    actual_return: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TradeExecutor:
    """Executes trades on Polymarket based on arbitrage opportunities"""
    
    def __init__(self, 
                 api_url: str,
                 api_key: Optional[str] = None,
                 private_key: Optional[str] = None,
                 max_trade_size: float = 100.0,
                 dry_run: bool = True):
        """
        Initialize trade executor
        
        Args:
            api_url: Polymarket API URL
            api_key: API key for authentication (optional)
            private_key: Private key for wallet (optional)
            max_trade_size: Maximum trade size in USD per opportunity
            dry_run: If True, simulate trades without executing
        """
        self.api_url = api_url
        self.api_key = api_key
        self.private_key = private_key
        self.max_trade_size = max_trade_size
        self.dry_run = dry_run
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.execution_history: List[ExecutionResult] = []
        
        if dry_run:
            logger.warning("Trade Executor initialized in DRY-RUN mode - no real trades will be executed")
        else:
            logger.info("Trade Executor initialized in LIVE mode")
            if not api_key:
                logger.warning("No API key provided - authentication may fail")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def execute_opportunity(self, opportunity: ArbitrageOpportunity) -> ExecutionResult:
        """
        Execute trades for an arbitrage opportunity
        
        Args:
            opportunity: ArbitrageOpportunity to execute
            
        Returns:
            ExecutionResult with execution details
        """
        logger.info(f"Executing arbitrage opportunity: {opportunity.type}")
        
        try:
            # Generate trade orders based on opportunity type
            orders = self._generate_orders(opportunity)
            
            if not orders:
                return ExecutionResult(
                    success=False,
                    opportunity=opportunity,
                    orders=[],
                    total_invested=0,
                    expected_return=0,
                    error_message="Failed to generate orders"
                )
            
            # Calculate total investment
            total_invested = sum(order.amount for order in orders)
            
            # Check if within limits
            if total_invested > self.max_trade_size:
                logger.warning(f"Trade size {total_invested} exceeds max {self.max_trade_size}, scaling down")
                scale_factor = self.max_trade_size / total_invested
                for order in orders:
                    order.amount *= scale_factor
                total_invested = self.max_trade_size
            
            # Execute orders
            if self.dry_run:
                logger.info("DRY RUN: Simulating order execution")
                for order in orders:
                    order.status = 'filled'
                    order.filled_amount = order.amount
                success = True
            else:
                success = await self._execute_orders(orders)
            
            # Calculate expected return
            expected_return = total_invested * (1 + opportunity.expected_profit)
            
            result = ExecutionResult(
                success=success,
                opportunity=opportunity,
                orders=orders,
                total_invested=total_invested,
                expected_return=expected_return
            )
            
            self.execution_history.append(result)
            
            if success:
                logger.info(f"✅ Successfully executed arbitrage: invested ${total_invested:.2f}, "
                          f"expected return ${expected_return:.2f}")
            else:
                logger.error(f"❌ Failed to execute arbitrage opportunity")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing opportunity: {e}")
            return ExecutionResult(
                success=False,
                opportunity=opportunity,
                orders=[],
                total_invested=0,
                expected_return=0,
                error_message=str(e)
            )
    
    def _generate_orders(self, opportunity: ArbitrageOpportunity) -> List[TradeOrder]:
        """Generate trade orders based on opportunity type"""
        orders = []
        
        if opportunity.type == 'yes_no_imbalance':
            # Buy both YES and NO on the same market
            market_id = opportunity.markets[0]
            details = opportunity.details
            
            # Equal split between YES and NO
            amount_per_side = self.max_trade_size / 2
            
            orders.append(TradeOrder(
                market_id=market_id,
                side='YES',
                amount=amount_per_side,
                price=details.get('yes_ask', 0.5)
            ))
            
            orders.append(TradeOrder(
                market_id=market_id,
                side='NO',
                amount=amount_per_side,
                price=details.get('no_ask', 0.5)
            ))
            
        elif opportunity.type == 'cross_market':
            # Buy YES on both markets
            markets = opportunity.markets
            details = opportunity.details
            
            # Equal split between markets
            amount_per_market = self.max_trade_size / len(markets)
            
            # For cross-market, we typically buy YES on both
            for i, market_id in enumerate(markets):
                price_key = f'market{i+1}_yes_ask' if i == 0 else f'market{i}_yes_ask'
                price = details.get(price_key, 0.5)
                
                orders.append(TradeOrder(
                    market_id=market_id,
                    side='YES',
                    amount=amount_per_market,
                    price=price
                ))
        
        elif opportunity.type == 'multi_leg':
            # Buy YES on all markets
            markets = opportunity.markets
            markets_info = opportunity.details.get('markets_info', {})
            
            # Equal split between markets
            amount_per_market = self.max_trade_size / len(markets)
            
            for market_id in markets:
                market_info = markets_info.get(market_id, {})
                price = market_info.get('yes_ask', 0.5)
                
                orders.append(TradeOrder(
                    market_id=market_id,
                    side='YES',
                    amount=amount_per_market,
                    price=price
                ))
        
        return orders
    
    async def _execute_orders(self, orders: List[TradeOrder]) -> bool:
        """
        Execute orders on Polymarket
        
        Args:
            orders: List of TradeOrder to execute
            
        Returns:
            True if all orders succeeded, False otherwise
        """
        if not self.session:
            logger.error("No active session - use async context manager")
            return False
        
        all_success = True
        
        for order in orders:
            try:
                success = await self._place_order(order)
                if not success:
                    all_success = False
                    order.status = 'failed'
                else:
                    order.status = 'filled'
                    order.filled_amount = order.amount
                    
            except Exception as e:
                logger.error(f"Error placing order: {e}")
                order.status = 'failed'
                all_success = False
        
        return all_success
    
    async def _place_order(self, order: TradeOrder) -> bool:
        """
        Place a single order on Polymarket
        
        Args:
            order: TradeOrder to place
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Placing order: {order.side} on {order.market_id} "
                   f"for ${order.amount:.2f} at price {order.price:.3f}")
        
        # Prepare order payload
        payload = {
            'market_id': order.market_id,
            'side': order.side,
            'amount': order.amount,
            'price': order.price,
            'type': 'market'  # Market order for immediate execution
        }
        
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        try:
            # Make API request to place order
            async with self.session.post(
                f"{self.api_url}/orders",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status == 200 or response.status == 201:
                    result = await response.json()
                    order.order_id = result.get('order_id')
                    logger.info(f"✅ Order placed successfully: {order.order_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Order failed with status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Exception placing order: {e}")
            return False
    
    def get_execution_history(self) -> List[ExecutionResult]:
        """Get all execution history"""
        return self.execution_history.copy()
    
    def get_execution_stats(self) -> Dict:
        """Get execution statistics"""
        total_executions = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        failed = total_executions - successful
        
        total_invested = sum(r.total_invested for r in self.execution_history if r.success)
        expected_returns = sum(r.expected_return for r in self.execution_history if r.success)
        
        return {
            'total_executions': total_executions,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_executions if total_executions > 0 else 0,
            'total_invested': total_invested,
            'expected_returns': expected_returns,
            'expected_profit': expected_returns - total_invested
        }
