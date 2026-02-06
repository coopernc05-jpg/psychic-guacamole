"""Cross-market arbitrage strategy."""

from dataclasses import dataclass
from typing import List, Tuple
from loguru import logger

from ...market.market_data import Market


@dataclass
class CrossMarketOpportunity:
    """Cross-market arbitrage opportunity."""
    
    market1: Market
    market2: Market
    buy_market: str  # Which market to buy from
    sell_market: str  # Which market to sell to
    outcome: str  # YES or NO
    buy_price: float
    sell_price: float
    profit_percentage: float
    expected_profit: float
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"Cross-Market Arb: Buy {self.outcome} @ {self.buy_price:.3f} "
            f"from {self.buy_market[:8]}..., Sell @ {self.sell_price:.3f} "
            f"to {self.sell_market[:8]}... | Profit: {self.profit_percentage:.2f}%"
        )


class CrossMarketStrategy:
    """Detect price discrepancies for the same event across different markets."""
    
    def __init__(self, min_profit_pct: float = 0.5):
        """Initialize strategy.
        
        Args:
            min_profit_pct: Minimum profit percentage threshold
        """
        self.min_profit_pct = min_profit_pct
    
    def detect(self, markets: List[Market]) -> List[CrossMarketOpportunity]:
        """Detect cross-market arbitrage opportunities.
        
        Args:
            markets: List of markets to analyze
            
        Returns:
            List of detected opportunities
        """
        opportunities = []
        
        # Group markets by similar questions/events
        market_groups = self._group_similar_markets(markets)
        
        for group in market_groups:
            # Find arbitrage opportunities within each group
            opps = self._find_arbitrage_in_group(group)
            opportunities.extend(opps)
        
        logger.debug(f"Cross-market strategy found {len(opportunities)} opportunities")
        return opportunities
    
    def _group_similar_markets(self, markets: List[Market]) -> List[List[Market]]:
        """Group markets that represent the same or similar events.
        
        Args:
            markets: List of markets
            
        Returns:
            List of market groups
        """
        # Simple grouping by category and similar questions
        # In production, this would use more sophisticated matching
        groups = {}
        
        for market in markets:
            # Create a simple key based on category and normalized question
            key = self._normalize_question(market.question)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(market)
        
        # Return only groups with multiple markets
        return [group for group in groups.values() if len(group) > 1]
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for grouping.
        
        Args:
            question: Market question
            
        Returns:
            Normalized question string
        """
        # Simple normalization - remove punctuation, lowercase, take first 50 chars
        normalized = question.lower().replace("?", "").replace("!", "").strip()
        return normalized[:50]
    
    def _find_arbitrage_in_group(
        self, 
        markets: List[Market]
    ) -> List[CrossMarketOpportunity]:
        """Find arbitrage opportunities within a group of similar markets.
        
        Args:
            markets: List of similar markets
            
        Returns:
            List of opportunities
        """
        opportunities = []
        
        # Compare each pair of markets
        for i, market1 in enumerate(markets):
            for market2 in markets[i+1:]:
                # Check YES outcome arbitrage
                yes_opp = self._check_price_difference(
                    market1, market2, "YES",
                    market1.yes_ask, market2.yes_bid
                )
                if yes_opp:
                    opportunities.append(yes_opp)
                
                yes_opp_reverse = self._check_price_difference(
                    market2, market1, "YES",
                    market2.yes_ask, market1.yes_bid
                )
                if yes_opp_reverse:
                    opportunities.append(yes_opp_reverse)
                
                # Check NO outcome arbitrage
                no_opp = self._check_price_difference(
                    market1, market2, "NO",
                    market1.no_ask, market2.no_bid
                )
                if no_opp:
                    opportunities.append(no_opp)
                
                no_opp_reverse = self._check_price_difference(
                    market2, market1, "NO",
                    market2.no_ask, market1.no_bid
                )
                if no_opp_reverse:
                    opportunities.append(no_opp_reverse)
        
        return opportunities
    
    def _check_price_difference(
        self,
        buy_market: Market,
        sell_market: Market,
        outcome: str,
        buy_price: float,
        sell_price: float
    ) -> CrossMarketOpportunity | None:
        """Check if price difference creates arbitrage opportunity.
        
        Args:
            buy_market: Market to buy from
            sell_market: Market to sell to
            outcome: YES or NO
            buy_price: Price to buy at
            sell_price: Price to sell at
            
        Returns:
            Opportunity if profitable, None otherwise
        """
        if sell_price <= buy_price:
            return None
        
        # Calculate profit percentage
        profit_pct = ((sell_price - buy_price) / buy_price) * 100
        
        if profit_pct < self.min_profit_pct:
            return None
        
        # Estimate profit for $100 trade (for ranking purposes)
        position_size = 100
        expected_profit = (sell_price - buy_price) * position_size
        
        return CrossMarketOpportunity(
            market1=buy_market,
            market2=sell_market,
            buy_market=buy_market.market_id,
            sell_market=sell_market.market_id,
            outcome=outcome,
            buy_price=buy_price,
            sell_price=sell_price,
            profit_percentage=profit_pct,
            expected_profit=expected_profit
        )
