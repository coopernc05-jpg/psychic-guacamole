"""Multi-leg arbitrage strategy."""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from itertools import combinations
from loguru import logger

from ...market.market_data import Market


@dataclass
class MultiLegOpportunity:
    """Multi-leg arbitrage opportunity across 3+ markets."""
    
    markets: List[Market]
    legs: List[Dict[str, any]]  # List of trade legs
    total_profit_percentage: float
    expected_profit: float
    complexity_score: int  # Number of legs
    
    def __str__(self) -> str:
        """String representation."""
        market_ids = [m.market_id[:8] for m in self.markets]
        return (
            f"Multi-Leg Arb ({self.complexity_score} legs): "
            f"Markets: {', '.join(market_ids)}... | "
            f"Profit: {self.total_profit_percentage:.2f}%"
        )


class MultiLegStrategy:
    """Detect complex arbitrage chains across 3+ related markets."""
    
    def __init__(self, min_profit_pct: float = 1.0, max_legs: int = 5):
        """Initialize strategy.
        
        Args:
            min_profit_pct: Minimum total profit percentage threshold
            max_legs: Maximum number of legs to consider
        """
        self.min_profit_pct = min_profit_pct
        self.max_legs = max_legs
    
    def detect(self, markets: List[Market]) -> List[MultiLegOpportunity]:
        """Detect multi-leg arbitrage opportunities.
        
        This strategy looks for arbitrage chains where:
        1. Market A outcome correlates with Market B outcome
        2. Market B outcome correlates with Market C outcome
        3. The chain creates a profit opportunity
        
        Args:
            markets: List of markets to analyze
            
        Returns:
            List of detected opportunities
        """
        opportunities = []
        
        # Group related markets by category
        market_groups = self._group_related_markets(markets)
        
        for group in market_groups:
            if len(group) >= 3:
                # Find arbitrage chains within the group
                opps = self._find_chains_in_group(group)
                opportunities.extend(opps)
        
        logger.debug(f"Multi-leg strategy found {len(opportunities)} opportunities")
        return opportunities
    
    def _group_related_markets(self, markets: List[Market]) -> List[List[Market]]:
        """Group markets that are potentially related.
        
        Args:
            markets: List of markets
            
        Returns:
            List of related market groups
        """
        groups = {}
        
        for market in markets:
            category = market.category
            if category not in groups:
                groups[category] = []
            groups[category].append(market)
        
        # Return groups with at least 3 markets
        return [group for group in groups.values() if len(group) >= 3]
    
    def _find_chains_in_group(self, markets: List[Market]) -> List[MultiLegOpportunity]:
        """Find arbitrage chains within a group of related markets.
        
        Args:
            markets: List of related markets
            
        Returns:
            List of opportunities
        """
        opportunities = []
        
        # Try combinations of 3, 4, 5... markets up to max_legs
        for num_markets in range(3, min(len(markets) + 1, self.max_legs + 1)):
            for market_combo in combinations(markets, num_markets):
                opp = self._check_chain(list(market_combo))
                if opp:
                    opportunities.append(opp)
        
        return opportunities
    
    def _check_chain(self, markets: List[Market]) -> MultiLegOpportunity | None:
        """Check if a chain of markets creates an arbitrage opportunity.
        
        This is a simplified implementation. In production, this would:
        1. Identify correlation patterns between markets
        2. Calculate optimal position sizes for each leg
        3. Account for dependencies and conditional probabilities
        
        Args:
            markets: Chain of markets to check
            
        Returns:
            Opportunity if profitable, None otherwise
        """
        # Simplified logic: Look for mispricing in related events
        # For example, if Market A YES implies Market B YES should be higher
        
        legs = []
        total_expected_return = 0
        
        # Build a synthetic chain
        for i, market in enumerate(markets):
            # Alternate between buying YES and NO to create a balanced chain
            if i % 2 == 0:
                leg = {
                    "market_id": market.market_id,
                    "action": "buy",
                    "outcome": "YES",
                    "price": market.yes_ask,
                    "question": market.question[:50]
                }
                expected_return = 1.0 - market.yes_ask
            else:
                leg = {
                    "market_id": market.market_id,
                    "action": "buy",
                    "outcome": "NO",
                    "price": market.no_ask,
                    "question": market.question[:50]
                }
                expected_return = 1.0 - market.no_ask
            
            legs.append(leg)
            total_expected_return += expected_return
        
        # Calculate if the chain is profitable
        total_cost = sum(leg["price"] for leg in legs)
        potential_return = len(markets)  # Maximum possible return
        profit = potential_return - total_cost
        profit_pct = (profit / total_cost) * 100 if total_cost > 0 else 0
        
        if profit_pct >= self.min_profit_pct:
            return MultiLegOpportunity(
                markets=markets,
                legs=legs,
                total_profit_percentage=profit_pct,
                expected_profit=profit * 100,  # For $100 position
                complexity_score=len(markets)
            )
        
        return None
