"""
Arbitrage Detection Module
Implements various arbitrage detection strategies for Polymarket
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""
    type: str  # 'cross_market', 'yes_no_imbalance', 'multi_leg'
    markets: List[str]
    expected_profit: float
    details: dict
    timestamp: str
    
    def __str__(self):
        return (f"Arbitrage [{self.type}]: "
                f"Profit={self.expected_profit:.4f}, "
                f"Markets={', '.join(self.markets)}")


class ArbitrageDetector:
    """Detects various types of arbitrage opportunities"""
    
    def __init__(self, min_profit_threshold: float = 0.01):
        self.min_profit_threshold = min_profit_threshold
        self.opportunities: List[ArbitrageOpportunity] = []
        
    def detect_all_opportunities(self, market_data: Dict[str, dict]) -> List[ArbitrageOpportunity]:
        """Detect all types of arbitrage opportunities"""
        opportunities = []
        
        # Detect cross-market arbitrage
        opportunities.extend(self.detect_cross_market_arbitrage(market_data))
        
        # Detect YES/NO imbalance arbitrage
        opportunities.extend(self.detect_yes_no_imbalance(market_data))
        
        # Detect multi-leg arbitrage
        opportunities.extend(self.detect_multi_leg_arbitrage(market_data))
        
        # Filter by minimum profit threshold
        filtered_opportunities = [
            opp for opp in opportunities 
            if opp.expected_profit >= self.min_profit_threshold
        ]
        
        self.opportunities = filtered_opportunities
        return filtered_opportunities
    
    def detect_cross_market_arbitrage(self, market_data: Dict[str, dict]) -> List[ArbitrageOpportunity]:
        """
        Detect cross-market arbitrage: same event, different outcomes or markets
        
        Example: If two markets are for the same event but different outcomes,
        and their combined probabilities don't sum to 1, there's an arbitrage opportunity.
        """
        opportunities = []
        markets_list = list(market_data.items())
        
        # Group markets by event
        events: Dict[str, List[tuple]] = {}
        for market_id, data in markets_list:
            event_name = data.get('event_name', '')
            if event_name:
                if event_name not in events:
                    events[event_name] = []
                events[event_name].append((market_id, data))
        
        # Check each event with multiple markets
        for event_name, event_markets in events.items():
            if len(event_markets) < 2:
                continue
            
            # Compare pairs of markets
            for i in range(len(event_markets)):
                for j in range(i + 1, len(event_markets)):
                    market1_id, market1_data = event_markets[i]
                    market2_id, market2_data = event_markets[j]
                    
                    # Check if outcomes are complementary or overlapping
                    opp = self._check_cross_market_pair(
                        market1_id, market1_data,
                        market2_id, market2_data,
                        event_name
                    )
                    if opp:
                        opportunities.append(opp)
        
        return opportunities
    
    def _check_cross_market_pair(self, market1_id: str, market1_data: dict,
                                  market2_id: str, market2_data: dict,
                                  event_name: str) -> Optional[ArbitrageOpportunity]:
        """Check a pair of markets for cross-market arbitrage"""
        
        # Get best prices for buying YES on both markets
        yes1_ask = market1_data.get('yes_ask', 0)
        yes2_ask = market2_data.get('yes_ask', 0)
        
        # If outcomes are mutually exclusive, probabilities should sum to <= 1
        # If sum of ask prices < 1, we can buy both and guarantee profit
        total_cost = yes1_ask + yes2_ask
        
        if total_cost > 0 and total_cost < 0.99:  # Allow small margin for fees
            expected_profit = 1.0 - total_cost
            
            return ArbitrageOpportunity(
                type='cross_market',
                markets=[market1_id, market2_id],
                expected_profit=expected_profit,
                details={
                    'event_name': event_name,
                    'market1_yes_ask': yes1_ask,
                    'market2_yes_ask': yes2_ask,
                    'total_cost': total_cost,
                    'strategy': 'Buy YES on both markets'
                },
                timestamp=datetime.now().isoformat()
            )
        
        return None
    
    def detect_yes_no_imbalance(self, market_data: Dict[str, dict]) -> List[ArbitrageOpportunity]:
        """
        Detect YES/NO imbalance arbitrage on the same market
        
        In a properly priced market, YES price + NO price should equal 1.
        If there's an imbalance, we can exploit it.
        """
        opportunities = []
        
        for market_id, data in market_data.items():
            yes_bid = data.get('yes_bid', 0)
            no_bid = data.get('no_bid', 0)
            yes_ask = data.get('yes_ask', 0)
            no_ask = data.get('no_ask', 0)
            
            # Check if we can buy YES and NO for less than 1
            if yes_ask > 0 and no_ask > 0:
                total_cost = yes_ask + no_ask
                
                if total_cost < 0.99:  # Allow small margin
                    expected_profit = 1.0 - total_cost
                    
                    opportunities.append(ArbitrageOpportunity(
                        type='yes_no_imbalance',
                        markets=[market_id],
                        expected_profit=expected_profit,
                        details={
                            'event_name': data.get('event_name', ''),
                            'yes_ask': yes_ask,
                            'no_ask': no_ask,
                            'total_cost': total_cost,
                            'strategy': 'Buy both YES and NO'
                        },
                        timestamp=datetime.now().isoformat()
                    ))
            
            # Check if we can sell YES and NO for more than 1
            if yes_bid > 0 and no_bid > 0:
                total_revenue = yes_bid + no_bid
                
                if total_revenue > 1.01:  # Allow small margin
                    expected_profit = total_revenue - 1.0
                    
                    opportunities.append(ArbitrageOpportunity(
                        type='yes_no_imbalance',
                        markets=[market_id],
                        expected_profit=expected_profit,
                        details={
                            'event_name': data.get('event_name', ''),
                            'yes_bid': yes_bid,
                            'no_bid': no_bid,
                            'total_revenue': total_revenue,
                            'strategy': 'Sell both YES and NO'
                        },
                        timestamp=datetime.now().isoformat()
                    ))
        
        return opportunities
    
    def detect_multi_leg_arbitrage(self, market_data: Dict[str, dict]) -> List[ArbitrageOpportunity]:
        """
        Detect multi-leg arbitrage opportunities
        
        Example: Three related markets where combined probabilities 
        create an arbitrage opportunity
        """
        opportunities = []
        markets_list = list(market_data.items())
        
        # Group markets by event
        events: Dict[str, List[tuple]] = {}
        for market_id, data in markets_list:
            event_name = data.get('event_name', '')
            if event_name:
                if event_name not in events:
                    events[event_name] = []
                events[event_name].append((market_id, data))
        
        # Check events with 3+ markets for multi-leg opportunities
        for event_name, event_markets in events.items():
            if len(event_markets) >= 3:
                opp = self._check_multi_leg_opportunity(event_name, event_markets)
                if opp:
                    opportunities.append(opp)
        
        return opportunities
    
    def _check_multi_leg_opportunity(self, event_name: str, 
                                     event_markets: List[tuple]) -> Optional[ArbitrageOpportunity]:
        """Check for multi-leg arbitrage in a set of related markets"""
        
        # Calculate total cost to buy YES on all markets
        total_cost = 0
        market_ids = []
        details_info = {}
        
        for market_id, data in event_markets:
            yes_ask = data.get('yes_ask', 0)
            if yes_ask <= 0:
                return None  # Skip if any market has invalid data
            
            total_cost += yes_ask
            market_ids.append(market_id)
            details_info[market_id] = {
                'outcome': data.get('outcome', ''),
                'yes_ask': yes_ask
            }
        
        # If outcomes are mutually exclusive and exhaustive, buying all should cost ~1
        # If total cost < 1, we have an arbitrage opportunity
        # If total cost > 1, there might be an opportunity to sell
        
        if total_cost < 0.95:  # Significant discount
            expected_profit = 1.0 - total_cost
            
            return ArbitrageOpportunity(
                type='multi_leg',
                markets=market_ids,
                expected_profit=expected_profit,
                details={
                    'event_name': event_name,
                    'num_legs': len(market_ids),
                    'total_cost': total_cost,
                    'markets_info': details_info,
                    'strategy': 'Buy YES on all markets'
                },
                timestamp=datetime.now().isoformat()
            )
        
        return None
    
    def get_latest_opportunities(self) -> List[ArbitrageOpportunity]:
        """Get the most recent arbitrage opportunities found"""
        return self.opportunities.copy()
