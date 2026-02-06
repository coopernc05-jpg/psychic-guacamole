"""Correlated events arbitrage strategy."""

from dataclasses import dataclass
from typing import List, Dict, Set
from loguru import logger

from ...market.market_data import Market


@dataclass
class CorrelatedEventsOpportunity:
    """Correlated events arbitrage opportunity."""
    
    primary_market: Market
    correlated_market: Market
    correlation_type: str  # "positive", "negative", "conditional"
    primary_outcome: str
    correlated_outcome: str
    implied_probability: float  # What correlated market should be priced at
    actual_probability: float  # What it's actually priced at
    mispricing: float
    profit_percentage: float
    expected_profit: float
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"Correlated Events Arb: {self.correlation_type} correlation | "
            f"Primary: {self.primary_market.question[:30]}... | "
            f"Correlated: {self.correlated_market.question[:30]}... | "
            f"Mispricing: {self.mispricing:.3f} | Profit: {self.profit_percentage:.2f}%"
        )


class CorrelatedEventsStrategy:
    """Detect mispricing in related events with dependencies."""
    
    def __init__(self, min_profit_pct: float = 0.5, min_mispricing: float = 0.05):
        """Initialize strategy.
        
        Args:
            min_profit_pct: Minimum profit percentage threshold
            min_mispricing: Minimum mispricing threshold
        """
        self.min_profit_pct = min_profit_pct
        self.min_mispricing = min_mispricing
        
        # Define correlation patterns (simplified)
        self.correlation_patterns = [
            {"keywords": ["election", "president"], "type": "election"},
            {"keywords": ["win", "championship"], "type": "sports"},
            {"keywords": ["pass", "vote"], "type": "legislation"},
        ]
    
    def detect(self, markets: List[Market]) -> List[CorrelatedEventsOpportunity]:
        """Detect correlated events arbitrage opportunities.
        
        Examples:
        - If "Biden wins election" = 60%, then "Democrat wins" should be >= 60%
        - If "Team A wins championship" = 40%, then "Team A makes finals" should be >= 40%
        - If "Bill passes Senate" = 70% and "Bill passes House" = 60%, 
          then "Bill becomes law" should be <= 60% (min of both)
        
        Args:
            markets: List of markets to analyze
            
        Returns:
            List of detected opportunities
        """
        opportunities = []
        
        # Group markets by event type
        event_groups = self._group_by_event_type(markets)
        
        for event_type, group_markets in event_groups.items():
            if len(group_markets) >= 2:
                # Find correlations within each group
                opps = self._find_correlations_in_group(group_markets, event_type)
                opportunities.extend(opps)
        
        logger.debug(f"Correlated events strategy found {len(opportunities)} opportunities")
        return opportunities
    
    def _group_by_event_type(self, markets: List[Market]) -> Dict[str, List[Market]]:
        """Group markets by event type.
        
        Args:
            markets: List of markets
            
        Returns:
            Dictionary of event type to markets
        """
        groups = {}
        
        for market in markets:
            event_type = self._identify_event_type(market)
            if event_type not in groups:
                groups[event_type] = []
            groups[event_type].append(market)
        
        return groups
    
    def _identify_event_type(self, market: Market) -> str:
        """Identify the type of event based on question.
        
        Args:
            market: Market to classify
            
        Returns:
            Event type string
        """
        question_lower = market.question.lower()
        
        for pattern in self.correlation_patterns:
            if any(keyword in question_lower for keyword in pattern["keywords"]):
                return pattern["type"]
        
        return market.category
    
    def _find_correlations_in_group(
        self, 
        markets: List[Market],
        event_type: str
    ) -> List[CorrelatedEventsOpportunity]:
        """Find correlation-based arbitrage within a group.
        
        Args:
            markets: List of related markets
            event_type: Type of event
            
        Returns:
            List of opportunities
        """
        opportunities = []
        
        # Check each pair for correlation patterns
        for i, market1 in enumerate(markets):
            for market2 in markets[i+1:]:
                # Check if market1 implies constraints on market2
                opp = self._check_correlation(market1, market2, event_type)
                if opp:
                    opportunities.append(opp)
                
                # Check reverse direction
                opp_reverse = self._check_correlation(market2, market1, event_type)
                if opp_reverse:
                    opportunities.append(opp_reverse)
        
        return opportunities
    
    def _check_correlation(
        self,
        primary: Market,
        correlated: Market,
        event_type: str
    ) -> CorrelatedEventsOpportunity | None:
        """Check if there's a correlation-based mispricing.
        
        Args:
            primary: Primary market
            correlated: Correlated market
            event_type: Type of event
            
        Returns:
            Opportunity if mispricing detected, None otherwise
        """
        # Simplified correlation logic
        # In production, this would use more sophisticated probability models
        
        correlation_type = self._determine_correlation_type(primary, correlated)
        
        if correlation_type == "positive":
            # If primary YES = 70%, correlated YES should be >= 70%
            implied_prob = primary.yes_price
            actual_prob = correlated.yes_price
            
            if implied_prob > actual_prob + self.min_mispricing:
                mispricing = implied_prob - actual_prob
                profit_pct = (mispricing / actual_prob) * 100
                
                if profit_pct >= self.min_profit_pct:
                    return CorrelatedEventsOpportunity(
                        primary_market=primary,
                        correlated_market=correlated,
                        correlation_type=correlation_type,
                        primary_outcome="YES",
                        correlated_outcome="YES",
                        implied_probability=implied_prob,
                        actual_probability=actual_prob,
                        mispricing=mispricing,
                        profit_percentage=profit_pct,
                        expected_profit=mispricing * 100
                    )
        
        elif correlation_type == "negative":
            # If primary YES = 70%, correlated NO should be >= 70%
            implied_prob = primary.yes_price
            actual_prob = correlated.no_price
            
            if implied_prob > actual_prob + self.min_mispricing:
                mispricing = implied_prob - actual_prob
                profit_pct = (mispricing / actual_prob) * 100
                
                if profit_pct >= self.min_profit_pct:
                    return CorrelatedEventsOpportunity(
                        primary_market=primary,
                        correlated_market=correlated,
                        correlation_type=correlation_type,
                        primary_outcome="YES",
                        correlated_outcome="NO",
                        implied_probability=implied_prob,
                        actual_probability=actual_prob,
                        mispricing=mispricing,
                        profit_percentage=profit_pct,
                        expected_profit=mispricing * 100
                    )
        
        return None
    
    def _determine_correlation_type(self, market1: Market, market2: Market) -> str:
        """Determine correlation type between two markets.
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            Correlation type: "positive", "negative", or "conditional"
        """
        # Simplified heuristic based on question similarity
        q1 = market1.question.lower()
        q2 = market2.question.lower()
        
        # Check for negative keywords
        negative_keywords = ["not", "won't", "fail", "lose", "against"]
        if any(kw in q2 for kw in negative_keywords):
            return "negative"
        
        return "positive"  # Default to positive correlation
