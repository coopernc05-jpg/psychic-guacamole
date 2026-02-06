"""Opportunity scoring and ranking system."""

from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from loguru import logger

from ..config import Config
from .detector import Opportunity


@dataclass
class ScoredOpportunity:
    """An opportunity with calculated score for ranking."""
    
    opportunity: Opportunity
    score: float
    profit_score: float
    capital_efficiency_score: float
    confidence_score: float
    risk_score: float
    execution_difficulty: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "opportunity_type": self.opportunity.__class__.__name__,
            "opportunity_details": str(self.opportunity),
            "total_score": self.score,
            "profit_score": self.profit_score,
            "capital_efficiency": self.capital_efficiency_score,
            "confidence": self.confidence_score,
            "risk_score": self.risk_score,
            "execution_difficulty": self.execution_difficulty
        }


class OpportunityScorer:
    """Scores and ranks arbitrage opportunities for optimal execution order."""
    
    def __init__(self, config: Config):
        """Initialize the scorer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Scoring weights
        self.weights = {
            "profit": 0.35,
            "capital_efficiency": 0.25,
            "confidence": 0.20,
            "risk": 0.15,
            "execution_difficulty": 0.05
        }
    
    def score_opportunities(
        self,
        opportunities: List[Opportunity],
        available_capital: float
    ) -> List[ScoredOpportunity]:
        """Score and rank all opportunities.
        
        Args:
            opportunities: List of detected opportunities
            available_capital: Available capital for trading
            
        Returns:
            List of scored opportunities, sorted by score (highest first)
        """
        scored = []
        
        for opp in opportunities:
            score = self._calculate_score(opp, available_capital)
            scored.append(score)
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Scored and ranked {len(scored)} opportunities")
        return scored
    
    def _calculate_score(
        self,
        opportunity: Opportunity,
        available_capital: float
    ) -> ScoredOpportunity:
        """Calculate comprehensive score for an opportunity.
        
        Args:
            opportunity: Arbitrage opportunity
            available_capital: Available capital
            
        Returns:
            Scored opportunity
        """
        # Calculate individual score components
        profit_score = self._score_profit(opportunity)
        capital_efficiency = self._score_capital_efficiency(opportunity)
        confidence = self._score_confidence(opportunity)
        risk = self._score_risk(opportunity)
        execution_diff = self._score_execution_difficulty(opportunity)
        
        # Calculate weighted total score (0-100)
        total_score = (
            profit_score * self.weights["profit"] +
            capital_efficiency * self.weights["capital_efficiency"] +
            confidence * self.weights["confidence"] +
            (100 - risk) * self.weights["risk"] +  # Lower risk is better
            (100 - execution_diff) * self.weights["execution_difficulty"]
        )
        
        return ScoredOpportunity(
            opportunity=opportunity,
            score=total_score,
            profit_score=profit_score,
            capital_efficiency_score=capital_efficiency,
            confidence_score=confidence,
            risk_score=risk,
            execution_difficulty=execution_diff
        )
    
    def _score_profit(self, opportunity: Opportunity) -> float:
        """Score based on expected profit.
        
        Args:
            opportunity: Arbitrage opportunity
            
        Returns:
            Profit score (0-100)
        """
        expected_profit = getattr(opportunity, 'expected_profit', 0)
        profit_pct = getattr(opportunity, 'profit_percentage', 0)
        
        # Combine absolute and percentage profit
        # Higher profit = higher score (capped at 100)
        absolute_score = min(expected_profit / 10 * 100, 100)  # $10 = 100 score
        percentage_score = min(profit_pct * 10, 100)  # 10% = 100 score
        
        return (absolute_score + percentage_score) / 2
    
    def _score_capital_efficiency(self, opportunity: Opportunity) -> float:
        """Score based on capital efficiency (profit per dollar invested).
        
        Args:
            opportunity: Arbitrage opportunity
            
        Returns:
            Capital efficiency score (0-100)
        """
        expected_profit = getattr(opportunity, 'expected_profit', 0)
        
        # Estimate capital required
        capital_required = self._estimate_capital_required(opportunity)
        
        if capital_required == 0:
            return 0
        
        # ROI as a percentage
        roi = (expected_profit / capital_required) * 100
        
        # Score: 5% ROI = 50 points, 10% ROI = 100 points
        score = min(roi * 10, 100)
        
        return score
    
    def _score_confidence(self, opportunity: Opportunity) -> float:
        """Score based on confidence in the opportunity.
        
        Args:
            opportunity: Arbitrage opportunity
            
        Returns:
            Confidence score (0-100)
        """
        # Different strategies have different confidence levels
        from .strategies import (
            YesNoImbalanceOpportunity,
            CrossMarketOpportunity,
            MultiLegOpportunity,
            CorrelatedEventsOpportunity
        )
        
        if isinstance(opportunity, YesNoImbalanceOpportunity):
            # YES/NO imbalance is most reliable
            base_confidence = 90
        elif isinstance(opportunity, CrossMarketOpportunity):
            # Cross-market is reliable if liquidity is good
            base_confidence = 80
        elif isinstance(opportunity, CorrelatedEventsOpportunity):
            # Correlation-based depends on correlation strength
            base_confidence = 70
        elif isinstance(opportunity, MultiLegOpportunity):
            # Multi-leg is complex and less reliable
            base_confidence = 60
        else:
            base_confidence = 75
        
        return base_confidence
    
    def _score_risk(self, opportunity: Opportunity) -> float:
        """Score based on risk level.
        
        Args:
            opportunity: Arbitrage opportunity
            
        Returns:
            Risk score (0-100, where 100 is highest risk)
        """
        from .strategies import (
            YesNoImbalanceOpportunity,
            CrossMarketOpportunity,
            MultiLegOpportunity,
            CorrelatedEventsOpportunity
        )
        
        # Base risk by strategy type
        if isinstance(opportunity, YesNoImbalanceOpportunity):
            risk = 10  # Low risk
        elif isinstance(opportunity, CrossMarketOpportunity):
            risk = 20  # Low-medium risk
        elif isinstance(opportunity, CorrelatedEventsOpportunity):
            risk = 40  # Medium risk
        elif isinstance(opportunity, MultiLegOpportunity):
            # Risk increases with complexity
            risk = 30 + (opportunity.complexity_score * 5)
        else:
            risk = 50
        
        return min(risk, 100)
    
    def _score_execution_difficulty(self, opportunity: Opportunity) -> float:
        """Score based on execution difficulty.
        
        Args:
            opportunity: Arbitrage opportunity
            
        Returns:
            Execution difficulty score (0-100, where 100 is most difficult)
        """
        from .strategies import (
            YesNoImbalanceOpportunity,
            CrossMarketOpportunity,
            MultiLegOpportunity,
            CorrelatedEventsOpportunity
        )
        
        if isinstance(opportunity, YesNoImbalanceOpportunity):
            # Simple: buy both YES and NO
            difficulty = 20
        elif isinstance(opportunity, CrossMarketOpportunity):
            # Medium: coordinate buy and sell
            difficulty = 30
        elif isinstance(opportunity, CorrelatedEventsOpportunity):
            # Medium-high: requires understanding correlation
            difficulty = 50
        elif isinstance(opportunity, MultiLegOpportunity):
            # High: many transactions to coordinate
            difficulty = 40 + (opportunity.complexity_score * 10)
        else:
            difficulty = 50
        
        return min(difficulty, 100)
    
    def _estimate_capital_required(self, opportunity: Opportunity) -> float:
        """Estimate capital required to execute opportunity.
        
        Args:
            opportunity: Arbitrage opportunity
            
        Returns:
            Estimated capital in USD
        """
        from .strategies import (
            YesNoImbalanceOpportunity,
            CrossMarketOpportunity,
            MultiLegOpportunity,
            CorrelatedEventsOpportunity
        )
        
        # Default position size for estimation
        position_size = 100
        
        if isinstance(opportunity, YesNoImbalanceOpportunity):
            # Buy both YES and NO
            capital = (opportunity.yes_price + opportunity.no_price) * position_size
        elif isinstance(opportunity, CrossMarketOpportunity):
            # Buy from one market
            capital = opportunity.buy_price * position_size
        elif isinstance(opportunity, MultiLegOpportunity):
            # Sum of all legs
            capital = sum(leg["price"] for leg in opportunity.legs) * position_size
        elif isinstance(opportunity, CorrelatedEventsOpportunity):
            # Two positions
            capital = (opportunity.implied_probability + opportunity.actual_probability) / 2 * position_size
        else:
            capital = position_size
        
        return capital
