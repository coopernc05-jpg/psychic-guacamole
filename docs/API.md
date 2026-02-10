# API Reference and Integration Guide

Complete API reference for the Polymarket Arbitrage Bot and integration instructions.

## Table of Contents
- [Bot API](#bot-api)
- [Polymarket API Integration](#polymarket-api-integration)
- [Configuration API](#configuration-api)
- [Strategy API](#strategy-api)
- [Execution API](#execution-api)
- [Analytics API](#analytics-api)
- [WebSocket API](#websocket-api)
- [Custom Strategy Development](#custom-strategy-development)

## Bot API

### Main Bot Class

```python
from src.main import PolymarketArbitrageBot

# Initialize bot
bot = PolymarketArbitrageBot(config_path="config.yaml")

# Start bot (async)
await bot.start()

# Stop bot (async)
await bot.stop()
```

### Bot Methods

#### `start()`
Start the arbitrage bot main loop.

```python
await bot.start()
```

**Returns**: None  
**Raises**: `KeyboardInterrupt`, `Exception`

#### `stop()`
Stop the bot and cleanup resources.

```python
await bot.stop()
```

**Returns**: None

#### Private Methods

- `_fetch_markets()`: Fetch current market data
- `_process_opportunities()`: Process detected opportunities
- `_manage_positions()`: Check and manage open positions
- `_on_market_update(update)`: Handle WebSocket market updates

## Polymarket API Integration

### API Client

```python
from src.market.polymarket_api import PolymarketAPIClient
from src.config import load_config

config = load_config()
client = PolymarketAPIClient(config)

# Connect
await client.connect()

# Fetch markets
markets = await client.get_markets(category="politics", limit=50)

# Get specific market
market = await client.get_market(market_id="0x123...")

# Get order book
order_book = await client.get_order_book(market_id="0x123...", outcome="YES")

# Get gas price
gas_price = await client.get_gas_price()

# Close connection
await client.close()
```

### Market Data Models

```python
from src.market.market_data import Market, OrderBook, Trade, Position

# Market object
market = Market(
    market_id="0x123...",
    question="Will it rain?",
    description="Weather prediction",
    category="weather",
    end_date=datetime(2024, 12, 31),
    status=MarketStatus.ACTIVE,
    yes_price=0.55,
    no_price=0.45,
    yes_bid=0.54,
    yes_ask=0.56,
    no_bid=0.44,
    no_ask=0.46,
    volume_24h=10000,
    liquidity=50000,
    metadata={}
)

# Access properties
print(market.spread)  # Bid-ask spread
print(market.price_sum)  # YES + NO prices
```

### Order Book

```python
order_book = OrderBook(
    market_id="0x123...",
    outcome="YES",
    bids=[(0.54, 100), (0.53, 200)],  # (price, size)
    asks=[(0.56, 150), (0.57, 250)],
    timestamp=datetime.now()
)

# Access properties
best_bid = order_book.best_bid  # (0.54, 100)
best_ask = order_book.best_ask  # (0.56, 150)
mid_price = order_book.mid_price  # 0.55
```

## Configuration API

### Loading Configuration

```python
from src.config import load_config, get_config, Config

# Load from file
config = load_config("custom_config.yaml")

# Get global config instance
config = get_config()

# Access settings
print(config.min_profit_threshold)
print(config.kelly_fraction)
print(config.strategies)
```

### Configuration Schema

```python
class Config(BaseSettings):
    # Profit Maximization
    min_profit_threshold: float = 5.0
    position_sizing_strategy: Literal["kelly", "fixed", "percentage"] = "kelly"
    kelly_fraction: float = 0.25
    max_position_size: float = 1000.0
    max_total_exposure: float = 5000.0
    
    # Arbitrage Detection
    strategies: List[str] = ["cross_market", "yes_no_imbalance", ...]
    min_arbitrage_percentage: float = 0.5
    
    # Market Monitoring
    websocket_enabled: bool = True
    markets_to_monitor: str | List[str] = "all"
    refresh_interval: int = 1
    max_markets: int = 100
    
    # Risk Management
    max_slippage: float = 0.02
    safety_margin: float = 1.5
    stop_loss_percentage: float = 0.05
    
    # Execution
    mode: Literal["alert", "auto_trade"] = "alert"
    gas_price_limit: int = 100
    
    # ... (see src/config.py for complete schema)
```

## Strategy API

### Arbitrage Detector

```python
from src.arbitrage.detector import ArbitrageDetector

detector = ArbitrageDetector(config)

# Detect opportunities
opportunities = detector.detect_opportunities(markets)

# Filter profitable opportunities
gas_price = 30.0  # gwei
profitable = detector.filter_profitable_opportunities(opportunities, gas_price)
```

### Opportunity Scorer

```python
from src.arbitrage.scorer import OpportunityScorer

scorer = OpportunityScorer(config)

# Score opportunities
available_capital = 10000.0
scored = scorer.score_opportunities(opportunities, available_capital)

# Access scored opportunity
for scored_opp in scored:
    print(f"Score: {scored_opp.score}/100")
    print(f"Profit: {scored_opp.profit_score}")
    print(f"Confidence: {scored_opp.confidence_score}")
    print(f"Risk: {scored_opp.risk_score}")
```

### Individual Strategies

#### Cross-Market Strategy

```python
from src.arbitrage.strategies.cross_market import CrossMarketStrategy

strategy = CrossMarketStrategy(min_profit_pct=0.5)
opportunities = strategy.detect(markets)

for opp in opportunities:
    print(f"Buy from: {opp.buy_market}")
    print(f"Sell to: {opp.sell_market}")
    print(f"Profit: {opp.profit_percentage}%")
```

#### YES/NO Imbalance Strategy

```python
from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceStrategy

strategy = YesNoImbalanceStrategy(min_profit_pct=0.5)
opportunities = strategy.detect(markets)

for opp in opportunities:
    print(f"Market: {opp.market.question}")
    print(f"Action: {opp.action}")  # "buy_both" or "sell_both"
    print(f"Imbalance: {opp.imbalance}")
```

#### Multi-Leg Strategy

```python
from src.arbitrage.strategies.multi_leg import MultiLegStrategy

strategy = MultiLegStrategy(min_profit_pct=1.0, max_legs=5)
opportunities = strategy.detect(markets)

for opp in opportunities:
    print(f"Legs: {opp.complexity_score}")
    for leg in opp.legs:
        print(f"  {leg['action']} {leg['outcome']} on {leg['market_id']}")
```

#### Correlated Events Strategy

```python
from src.arbitrage.strategies.correlated_events import CorrelatedEventsStrategy

strategy = CorrelatedEventsStrategy(min_profit_pct=0.5)
opportunities = strategy.detect(markets)

for opp in opportunities:
    print(f"Correlation: {opp.correlation_type}")
    print(f"Mispricing: {opp.mispricing}")
```

## Execution API

### Position Sizing

```python
from src.execution.position_sizing import PositionSizer, kelly_criterion

# Kelly Criterion calculation
win_prob = 0.70
win_return = 0.50  # 50% return
kelly_f = kelly_criterion(win_prob, win_return)
print(f"Kelly fraction: {kelly_f}")

# Position sizer
sizer = PositionSizer(config)
position_size = sizer.calculate_position_size(
    opportunity_profit_pct=5.0,
    opportunity_confidence=0.80,
    available_capital=10000.0
)
print(f"Position size: ${position_size}")
```

### Capital Allocator

```python
from src.execution.position_sizing import CapitalAllocator

allocator = CapitalAllocator(config)

# Allocate capital
allocation = allocator.allocate_capital(
    opportunities=scored_opportunities,
    total_capital=10000.0,
    current_exposure=2000.0
)

# Returns: {opportunity_index: position_size}
for idx, size in allocation.items():
    print(f"Opportunity {idx}: ${size}")
```

### Trade Executor

```python
from src.execution.executor import TradeExecutor

executor = TradeExecutor(config)

# Execute opportunity
trades = await executor.execute_opportunity(
    scored_opportunity=scored_opp,
    position_size=500.0
)

# Check executed trades
if trades:
    for trade in trades:
        print(f"{trade.side.value} {trade.outcome} @ {trade.price}")
```

### Risk Manager

```python
from src.execution.risk_manager import RiskManager

risk_mgr = RiskManager(config)

# Check if can open position
can_open, reason = risk_mgr.can_open_position(position_size=500.0)
if can_open:
    # Add position
    risk_mgr.add_position(position)

# Update prices
market_prices = {m.market_id: m for m in markets}
risk_mgr.update_position_prices(market_prices)

# Check stop losses
to_close = risk_mgr.check_stop_losses()

# Get risk metrics
metrics = risk_mgr.get_risk_metrics()
print(f"Total capital: ${metrics['total_capital']}")
print(f"Current exposure: ${metrics['current_exposure']}")
print(f"Open positions: {metrics['open_positions']}")
```

## Analytics API

### Opportunity Logger

```python
from src.analytics.logger import OpportunityLogger

opp_logger = OpportunityLogger(log_dir="data/opportunities")

# Log opportunity
opp_logger.log_opportunity(scored_opportunity)

# Get statistics
stats = opp_logger.get_statistics()
print(f"Total opportunities: {stats['total_opportunities']}")
print(f"By type: {stats['by_type']}")
```

### Execution Logger

```python
from src.analytics.logger import ExecutionLogger

exec_logger = ExecutionLogger(log_dir="data/executions")

# Log trade
exec_logger.log_trade(trade)

# Log closed position
exec_logger.log_position_close(position)

# Get statistics
trade_stats = exec_logger.get_trade_statistics()
position_stats = exec_logger.get_position_statistics()
```

### Performance Tracker

```python
from src.analytics.performance import PerformanceTracker

tracker = PerformanceTracker(initial_capital=10000.0)

# Add trades and positions
tracker.add_trade(trade)
tracker.add_closed_position(position)

# Calculate metrics
metrics = tracker.calculate_metrics()
print(f"ROI: {metrics.roi}%")
print(f"Sharpe Ratio: {metrics.sharpe_ratio}")
print(f"Win Rate: {metrics.win_rate}%")

# Generate report
report = tracker.generate_report()
print(report)
```

## WebSocket API

### WebSocket Client

```python
from src.market.websocket_client import WebSocketClient

ws_client = WebSocketClient(config)

# Connect
await ws_client.connect()

# Subscribe to market
await ws_client.subscribe_market("0x123...")

# Register callback
async def on_update(update):
    print(f"Market {update['market_id']} updated")
    print(f"YES: {update['yes_price']}, NO: {update['no_price']}")

ws_client.register_callback(on_update)

# Start listening
await ws_client.listen()

# Disconnect
await ws_client.disconnect()
```

### WebSocket Message Format

```python
# Market update message
{
    "type": "market_update",
    "market_id": "0x123...",
    "yes_price": 0.55,
    "no_price": 0.45,
    "yes_bid": 0.54,
    "yes_ask": 0.56,
    "no_bid": 0.44,
    "no_ask": 0.46,
    "timestamp": "2024-01-01T12:00:00"
}

# Trade notification
{
    "type": "trade",
    "market_id": "0x123...",
    "outcome": "YES",
    "price": 0.55,
    "size": 100,
    "timestamp": "2024-01-01T12:00:00"
}

# Error message
{
    "type": "error",
    "message": "Connection lost"
}
```

## Custom Strategy Development

### Creating a New Strategy

1. **Create strategy file**: `src/arbitrage/strategies/my_strategy.py`

```python
from dataclasses import dataclass
from typing import List
from loguru import logger
from ...market.market_data import Market

@dataclass
class MyOpportunity:
    """Custom opportunity type."""
    market: Market
    expected_profit: float
    profit_percentage: float
    # ... other fields
    
    def __str__(self) -> str:
        return f"My Strategy: {self.market.question} | Profit: {self.profit_percentage}%"

class MyStrategy:
    """Custom arbitrage strategy."""
    
    def __init__(self, min_profit_pct: float = 0.5):
        self.min_profit_pct = min_profit_pct
    
    def detect(self, markets: List[Market]) -> List[MyOpportunity]:
        """Detect opportunities using custom logic.
        
        Args:
            markets: List of markets to analyze
            
        Returns:
            List of detected opportunities
        """
        opportunities = []
        
        for market in markets:
            # Your custom detection logic here
            if self._is_opportunity(market):
                opp = self._create_opportunity(market)
                opportunities.append(opp)
        
        logger.debug(f"My strategy found {len(opportunities)} opportunities")
        return opportunities
    
    def _is_opportunity(self, market: Market) -> bool:
        """Check if market presents an opportunity."""
        # Custom logic
        return True
    
    def _create_opportunity(self, market: Market) -> MyOpportunity:
        """Create opportunity object."""
        # Calculate metrics
        return MyOpportunity(
            market=market,
            expected_profit=10.0,
            profit_percentage=2.0
        )
```

2. **Register in detector**: `src/arbitrage/detector.py`

```python
from .strategies.my_strategy import MyStrategy, MyOpportunity

# Add to Opportunity type alias
Opportunity = Union[
    CrossMarketOpportunity,
    YesNoImbalanceOpportunity,
    MultiLegOpportunity,
    CorrelatedEventsOpportunity,
    MyOpportunity  # Add your strategy
]

# Add to ArbitrageDetector.__init__
if "my_strategy" in config.strategies:
    self.strategies.append(
        MyStrategy(min_profit_pct=config.min_arbitrage_percentage)
    )
```

3. **Add to config**: `config.yaml`

```yaml
strategies:
  - yes_no_imbalance
  - cross_market
  - my_strategy  # Enable your strategy
```

4. **Implement scorer logic**: `src/arbitrage/scorer.py`

```python
# Add scoring logic for your opportunity type
if isinstance(opportunity, MyOpportunity):
    base_confidence = 75  # Your confidence level
```

### Strategy Best Practices

1. **Type Safety**: Use dataclasses and type hints
2. **Logging**: Log at appropriate levels
3. **Error Handling**: Catch and handle exceptions
4. **Testing**: Write unit tests for detection logic
5. **Documentation**: Document strategy clearly

### Example: Volatility Strategy

```python
@dataclass
class VolatilityOpportunity:
    """Opportunity based on price volatility."""
    market: Market
    volatility_score: float
    expected_profit: float
    profit_percentage: float

class VolatilityStrategy:
    """Detect opportunities in highly volatile markets."""
    
    def __init__(self, min_profit_pct: float = 0.5, volatility_threshold: float = 0.10):
        self.min_profit_pct = min_profit_pct
        self.volatility_threshold = volatility_threshold
        self.price_history: Dict[str, List[float]] = {}
    
    def detect(self, markets: List[Market]) -> List[VolatilityOpportunity]:
        opportunities = []
        
        for market in markets:
            # Track price history
            if market.market_id not in self.price_history:
                self.price_history[market.market_id] = []
            
            self.price_history[market.market_id].append(market.yes_price)
            
            # Calculate volatility
            if len(self.price_history[market.market_id]) >= 10:
                volatility = self._calculate_volatility(
                    self.price_history[market.market_id]
                )
                
                if volatility > self.volatility_threshold:
                    # High volatility = opportunity to profit from swings
                    opp = VolatilityOpportunity(
                        market=market,
                        volatility_score=volatility,
                        expected_profit=volatility * 1000,  # Estimate
                        profit_percentage=volatility * 100
                    )
                    opportunities.append(opp)
        
        return opportunities
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility (standard deviation)."""
        if len(prices) < 2:
            return 0.0
        
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        return variance ** 0.5
```

## Error Handling

### Common Exceptions

```python
# API Connection Errors
try:
    await client.connect()
except aiohttp.ClientError as e:
    logger.error(f"Failed to connect: {e}")

# Configuration Errors
try:
    config = load_config("config.yaml")
except FileNotFoundError:
    logger.error("Config file not found")

# Execution Errors
try:
    trades = await executor.execute_opportunity(opp, size)
except Exception as e:
    logger.error(f"Execution failed: {e}")
    # Send alert
    discord.send_error_alert(str(e))
```

## Testing

### Unit Testing Strategies

```python
import pytest
from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceStrategy
from src.market.market_data import Market, MarketStatus

def test_yes_no_imbalance_detection():
    """Test YES/NO imbalance detection."""
    # Create test market
    market = Market(
        market_id="test_1",
        question="Test?",
        description="Test market",
        category="test",
        end_date=datetime.now(),
        status=MarketStatus.ACTIVE,
        yes_price=0.50,
        no_price=0.45,
        yes_bid=0.49,
        yes_ask=0.51,
        no_bid=0.44,
        no_ask=0.46,
        volume_24h=1000,
        liquidity=5000
    )
    
    strategy = YesNoImbalanceStrategy(min_profit_pct=0.5)
    opportunities = strategy.detect([market])
    
    assert len(opportunities) == 1
    assert opportunities[0].action == "buy_both"
    assert opportunities[0].price_sum < 1.0
```

## Performance Optimization

### Async Best Practices

```python
# Use asyncio.gather for parallel operations
markets_data = await asyncio.gather(
    client.get_markets(category="politics"),
    client.get_markets(category="sports"),
    client.get_markets(category="crypto")
)

# Use async context managers
async with PolymarketAPIClient(config) as client:
    markets = await client.get_markets()
```

### Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedAPIClient:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(seconds=60)
    
    async def get_markets(self, category: str):
        cache_key = f"markets_{category}"
        
        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return data
        
        # Fetch fresh data
        data = await self._fetch_markets(category)
        self.cache[cache_key] = (datetime.now(), data)
        return data
```

## Conclusion

This API reference provides comprehensive coverage of the bot's functionality. For specific implementation details, refer to the source code and inline documentation.

For questions or contributions, please open an issue on GitHub.
