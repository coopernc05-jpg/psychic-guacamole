# Arbitrage Strategies Guide

Comprehensive guide to all arbitrage strategies implemented in the Polymarket Arbitrage Bot.

## Table of Contents
- [Strategy Overview](#strategy-overview)
- [YES/NO Imbalance Arbitrage](#yesno-imbalance-arbitrage)
- [Cross-Market Arbitrage](#cross-market-arbitrage)
- [Order Book Spread Trading](#order-book-spread-trading)
- [Multi-Leg Arbitrage](#multi-leg-arbitrage)
- [Correlated Events Arbitrage](#correlated-events-arbitrage)
- [Time-Based Arbitrage](#time-based-arbitrage)
- [Strategy Comparison](#strategy-comparison)
- [Best Practices](#best-practices)

## Strategy Overview

Each strategy exploits different market inefficiencies:

| Strategy | Reliability | Profit Potential | Complexity | Risk Level |
|----------|------------|------------------|------------|------------|
| YES/NO Imbalance | ⭐⭐⭐⭐⭐ | 0.3-2% | Low | Very Low |
| Cross-Market | ⭐⭐⭐⭐ | 0.5-3% | Low | Low |
| Order Book Spread | ⭐⭐⭐⭐ | 0.5-2% | Medium | Low |
| Correlated Events | ⭐⭐⭐ | 0.8-5% | Medium | Medium |
| Multi-Leg | ⭐⭐ | 1.0-8% | High | High |
| Time-Based | ⭐⭐⭐ | 0.6-4% | Medium | Medium |

## YES/NO Imbalance Arbitrage

### Concept

In prediction markets, YES + NO should always equal 1.00 (100%). When this doesn't hold, there's an arbitrage opportunity.

**Formula**: `YES_price + NO_price ≠ 1.00`

### How It Works

#### Scenario 1: Sum < 1.00 (Buy Both)
```
Market: "Will it rain tomorrow?"
YES ask: $0.45
NO ask: $0.48
Sum: $0.93

Arbitrage: Buy both for $0.93, guaranteed return $1.00
Profit: $0.07 (7.5% return)
```

**Execution**:
1. Buy $100 of YES shares @ $0.45 = 222 shares
2. Buy $100 of NO shares @ $0.48 = 208 shares
3. Total cost: $200
4. When market resolves, win $222 or $208 (whichever outcome)
5. Net profit: ~$15 after costs

#### Scenario 2: Sum > 1.00 (Sell Both)
```
Market: "Will GDP exceed 3%?"
YES bid: $0.58
NO bid: $0.46
Sum: $1.04

Arbitrage: Sell both for $1.04, only need to pay $1.00
Profit: $0.04 (4% return)
```

**Execution**:
1. Sell $100 of YES shares @ $0.58
2. Sell $100 of NO shares @ $0.46
3. Receive: $204
4. Must cover one outcome: -$100
5. Net profit: $4

### Why It Happens

- **Rapid price movements**: Bots/traders don't update both sides simultaneously
- **Low liquidity**: Not enough traders to arbitrage away
- **Market fragmentation**: Different user bases for YES/NO
- **Gas costs**: Small imbalances below gas costs ignored

### Risk Factors

- **Very Low Risk**: Guaranteed profit if held to resolution
- **Execution risk**: Prices might change before both orders fill
- **Resolution risk**: Market could be cancelled (rare)
- **Liquidity risk**: May not be able to buy/sell desired amounts

### Expected Performance

- **Frequency**: Most common arbitrage type
- **Profit**: 0.5-2% after costs
- **Hold time**: Until market resolution (hours to months)
- **Win rate**: ~95%+ (highest of all strategies)

### Example Opportunities

**Example 1: Presidential Election**
```python
Market: "Will Biden win 2024 election?"
YES: $0.52, NO: $0.46
Sum: $0.98
Opportunity: Buy both for guaranteed 2% profit
```

**Example 2: Sports Game**
```python
Market: "Lakers win tonight?"
YES: $0.55, NO: $0.47
Sum: $1.02
Opportunity: Sell both for 2% profit
```

### Configuration

```yaml
# In config.yaml
strategies:
  - yes_no_imbalance

min_arbitrage_percentage: 0.5  # Minimum 0.5% profit
```

## Cross-Market Arbitrage

### Concept

Same event listed on different markets with different prices. Buy low, sell high.

### How It Works

```
Market A: "Trump wins primary?"
YES: $0.65 (ask)

Market B: "Trump wins primary?"  
YES: $0.70 (bid)

Arbitrage: Buy on A @ $0.65, sell on B @ $0.70
Profit: $0.05 (7.7% return)
```

**Execution**:
1. Simultaneously buy YES on Market A
2. Sell YES on Market B
3. Lock in $0.05 spread regardless of outcome
4. Net profit: Spread - (2× gas costs)

### Why It Happens

- **Information asymmetry**: Different traders on each market
- **Liquidity differences**: One market may be less liquid
- **Market segmentation**: Markets in different categories
- **Time delays**: Prices update at different speeds

### Risk Factors

- **Low-Medium Risk**: Simultaneous execution required
- **Execution risk**: One side might not fill
- **Price movement**: Spread could narrow before execution
- **Liquidity risk**: Insufficient depth on one side

### Expected Performance

- **Frequency**: Common during high volatility
- **Profit**: 0.5-3% after costs
- **Hold time**: Immediate (if properly executed)
- **Win rate**: ~80-90%

### Example Opportunities

**Example 1: Duplicate Listings**
```python
Market 1: "Senate flips to GOP?" - YES @ $0.60
Market 2: "Republicans control Senate?" - YES @ $0.64
Action: Buy Market 1, sell Market 2
Profit: 6.7%
```

**Example 2: Different Wording**
```python
Market 1: "Bitcoin > $50k by March?" - YES @ $0.72
Market 2: "BTC under $50k in Q1?" - NO @ $0.25
# Note: Opposite outcomes, so compare YES to (1-NO)
Action: Buy Market 2 NO, sell Market 1 YES
Profit: 3%
```

### Configuration

```yaml
strategies:
  - cross_market

min_arbitrage_percentage: 0.5
max_markets: 100  # More markets = more opportunities
```

## Order Book Spread Trading

### Concept

Act as a market maker by placing limit orders between the bid and ask prices to capture the spread. Provide liquidity and profit from the bid-ask spread.

**Formula**: `Spread % = ((Ask - Bid) / MidPrice) × 100`

### How It Works

#### Market Making Strategy
```
Market: "Will inflation exceed 3%?"
YES bid: $0.48
YES ask: $0.52
Spread: 4% (attractive for market making)

Strategy: Place limit order at $0.50
- If it fills, you capture ~2% profit from the spread
- Acts as liquidity provider to the market
```

**Execution**:
1. Identify markets with wide spreads (≥2%)
2. Place limit order at midpoint or slightly favorable
3. Wait for order to fill
4. Profit from the spread capture
5. Hold to resolution or exit with profit

#### Example Trade
```
Market: "Republican wins 2024 election"
YES bid: $0.54
YES ask: $0.58
Mid price: $0.56
Spread: 3.6%

Action: Place limit buy at $0.55
Expected profit: ~1.8% of position size
```

### Why It Happens

- **Low liquidity markets**: Wide spreads due to few participants
- **Volatile events**: Spreads widen during uncertainty
- **Impatient traders**: Pay spread for immediate execution
- **Information asymmetry**: Some traders willing to pay for speed

### Risk Factors

- **Low Risk**: Capturing spread is relatively safe
- **Execution risk**: Order may not fill if market moves away
- **Inventory risk**: May hold position longer than expected
- **Market risk**: Events can move against you before exit
- **Liquidity risk**: May be hard to exit if needed

### Expected Performance

- **Frequency**: Depends on market activity
- **Profit**: 0.5-2% per successful fill
- **Hold time**: Minutes to hours (ideally)
- **Win rate**: ~70-80% when properly executed

### Configuration

```yaml
strategies:
  order_book_spread:
    enabled: true
    min_spread_pct: 2.0  # Minimum 2% spread required
    min_profit_pct: 0.5  # Minimum 0.5% profit after costs
```

### Best Practices

1. **Focus on liquid markets**: Easier to exit if needed
2. **Monitor order book depth**: Ensure sufficient liquidity
3. **Set time limits**: Don't hold positions indefinitely
4. **Scale positions**: Start small, increase with success
5. **Watch for news**: Events can cause rapid price movements

## Multi-Leg Arbitrage

### Concept

Exploit relationships across 3+ markets to create a profitable chain.

### How It Works

```
Market A: "Candidate X wins primary" - YES @ $0.70
Market B: "Candidate X wins nomination" - YES @ $0.60  
Market C: "Candidate X wins election" - YES @ $0.50

Logic: If X wins primary (A), they're likely to win nomination (B)
       If B is priced lower than A, there's mispricing

Action: Buy B (underpriced relative to A)
Expected profit: When correlation corrects
```

**Complex Example**:
```
3 markets about same event:
- "Team wins championship" @ $0.40
- "Team makes finals" @ $0.55
- "Team makes playoffs" @ $0.65

Logic check: Championship ≤ Finals ≤ Playoffs
Issue: $0.40 < $0.55 < $0.65 ✓ Looks correct
But: If championship is $0.40, finals should be ≥ $0.40
      If finals is $0.55, championship should be ≤ $0.55

This creates complex arbitrage opportunities
```

### Why It Happens

- **Complex reasoning**: Most traders don't check correlations
- **Separate markets**: Not obvious they're related
- **Incomplete information**: Traders focus on one market
- **Mathematical constraints**: Violate probability rules

### Risk Factors

- **Medium-High Risk**: Requires correlation to hold
- **Correlation risk**: Markets may not be as correlated as assumed
- **Timing risk**: Relationships may take time to align
- **Execution complexity**: Multiple trades required
- **Higher slippage**: More transactions = more costs

### Expected Performance

- **Frequency**: Less common, requires analysis
- **Profit**: 2-8% potential
- **Hold time**: Days to weeks
- **Win rate**: ~60-70%

### Example Opportunities

**Example 1: Election Cascade**
```python
Primary → Nomination → General Election

Market chain:
- Primary win: $0.80
- Nomination: $0.70
- General: $0.55

If primary win is 80%, nomination should be ≥80%
Opportunity: Buy nomination @ $0.70
```

**Example 2: Sports Progression**
```python
Playoffs → Conference Finals → Championship

Prices:
- Playoffs: $0.90
- Conference: $0.50  # Underpriced!
- Championship: $0.30

Logic: If 90% chance playoffs, conference should be higher
Action: Buy conference finals position
```

### Configuration

```yaml
strategies:
  - multi_leg

min_arbitrage_percentage: 1.0  # Higher threshold
max_legs: 5  # Limit complexity
```

## Correlated Events Arbitrage

### Concept

Find mispricing between related events with dependencies.

### How It Works

**Positive Correlation**:
```
Market A: "Biden wins presidency" @ $0.60
Market B: "Democrat wins presidency" @ $0.55

Issue: Biden IS a Democrat, so B should be ≥ A
Opportunity: Buy B @ $0.55 (underpriced)
```

**Negative Correlation**:
```
Market A: "Trump wins" @ $0.45
Market B: "Biden wins" @ $0.48

Issue: Both can't win, sum should be ≤ 1.00
Current sum: $0.93
This is actually correct (other candidates possible)
```

**Conditional Probability**:
```
Market A: "Bill passes Senate" @ $0.70
Market B: "Bill passes House" @ $0.60
Market C: "Bill becomes law" @ $0.65

Logic: Bill becomes law ONLY if passes both chambers
P(Law) ≤ min(P(Senate), P(House))
P(Law) ≤ min(0.70, 0.60) = 0.60

Current: $0.65 > $0.60 - MISPRICED!
Opportunity: Sell C @ $0.65
```

### Why It Happens

- **Complex relationships**: Most traders miss correlations
- **Different market participants**: Not all see both markets
- **Cognitive biases**: Overestimate independent probabilities
- **Market inefficiency**: Slow to correct complex mispricings

### Risk Factors

- **Medium Risk**: Depends on correlation strength
- **Assumption risk**: Correlation may not hold as expected
- **External factors**: Unknown variables affect outcomes
- **Time risk**: May take longer to correct

### Expected Performance

- **Frequency**: Moderate, requires market knowledge
- **Profit**: 1-5%
- **Hold time**: Days to weeks
- **Win rate**: ~70-80%

### Example Opportunities

**Example 1: Political Dependencies**
```python
"Senate flips to GOP" @ $0.50
"GOP trifecta (Pres + Senate + House)" @ $0.45

Logic: Trifecta requires Senate flip
P(Trifecta) ≤ P(Senate flip)
$0.45 < $0.50 ✓ Correct ordering

But if strong correlation expected:
Opportunity may exist in magnitude of difference
```

**Example 2: Economic Indicators**
```python
"Fed raises rates" @ $0.80
"Inflation above 3%" @ $0.40

Logic: High inflation strongly correlates with rate hikes
If inflation is only 40%, why are rates 80%?
This suggests market may be mispricing relationship
```

### Configuration

```yaml
strategies:
  - correlated_events

min_arbitrage_percentage: 0.5
min_mispricing: 0.05  # Minimum 5% mispricing
```

## Time-Based Arbitrage

### Concept

Monitor price changes near event resolution to detect panic selling, last-minute mispricing, or volatility spikes that create temporary arbitrage opportunities.

**Focus**: Markets within 24 hours of resolution

### How It Works

#### Opportunity Types

**1. Panic Selling**
```
Market: "Will Fed raise rates on March 15?"
Date: March 14, 8:00 PM (16 hours to resolution)

Price History:
- 7 days ago: YES @ $0.82
- 3 days ago: YES @ $0.80
- 1 day ago: YES @ $0.78
- NOW: YES @ $0.65 (sudden 16% drop)

Analysis: Panic selling on uncertain news
Strategy: Buy YES at $0.65, expect reversion to $0.75+
Potential profit: 15%+
```

**2. Last-Minute Mispricing**
```
Market: "Will unemployment be below 4%?"
Date: Report day, 2 hours before announcement

Price: YES @ $0.45
Historical average: YES @ $0.60
Recent data suggests: ~70% chance of YES

Analysis: Severe mispricing due to low liquidity
Strategy: Buy YES before announcement
Potential profit: 20%+
```

**3. Volatility Spike**
```
Market: "Will candidate win debate poll?"
During debate: Price swings wildly

Price movements:
- 8:00 PM: YES @ $0.55
- 8:15 PM: YES @ $0.42 (candidate stumbles)
- 8:30 PM: YES @ $0.58 (strong recovery)
- 8:45 PM: YES @ $0.48 (overreaction)

Strategy: Buy during overreactions, sell on recovery
```

### Why It Happens

- **Emotional trading**: Fear and greed amplified near resolution
- **Information cascades**: One large trade triggers panic
- **Low liquidity**: Fewer participants near resolution
- **News reactions**: Markets overreact to breaking news
- **Time pressure**: Traders rush to exit positions

### Risk Factors

- **Medium Risk**: Requires timing and market understanding
- **Event risk**: Outcome may be different than expected
- **Volatility risk**: Prices can continue moving against you
- **Liquidity risk**: Hard to exit if wrong
- **Time risk**: Limited window to realize profit

### Expected Performance

- **Frequency**: Depends on events resolving soon
- **Profit**: 0.6-4% per successful trade
- **Hold time**: Minutes to hours
- **Win rate**: ~65-75% with good timing

### Configuration

```yaml
strategies:
  time_based:
    enabled: true
    min_profit_pct: 0.6  # Minimum 0.6% profit threshold
    time_window_hours: 24  # Monitor markets within 24h of resolution
    volatility_threshold: 2.0  # Minimum volatility score
```

### Best Practices

1. **Build price history**: Track prices over time for context
2. **Understand the event**: Know what's driving price movements
3. **Set strict stops**: Time-based trades can move fast
4. **React quickly**: Opportunities disappear rapidly
5. **Avoid gambling**: Don't trade without clear edge

### Example Scenarios

**Scenario 1: Election Night**
```
Market: "Will Biden win Pennsylvania?"
11:00 PM: Early results favor Trump
Price drops: YES @ $0.40 (was $0.65)

Analysis:
- Historical correlation: PA mirrors national polls
- National polls: Biden +3%
- Urban areas not yet counted (favor Biden)

Strategy: Buy YES @ $0.40
Outcome: Urban votes counted, Biden wins
Exit: YES @ $0.85
Profit: 112%
```

**Scenario 2: Economic Data**
```
Market: "Will CPI exceed 3.5%?"
8:25 AM: 5 minutes before release
Price: YES @ $0.52

Analysis:
- Consensus: 3.6% (above threshold)
- Price undervalues consensus
- Market inefficient this close to release

Strategy: Buy YES @ $0.52
8:30 AM: CPI released at 3.7%
Exit: YES @ $0.95
Profit: 83%
```

## Strategy Comparison

### Execution Complexity

**Simplest → Most Complex**
1. YES/NO Imbalance (2 trades, same market)
2. Cross-Market (2 trades, different markets)
3. Correlated Events (2-3 trades, requires analysis)
4. Multi-Leg (3+ trades, complex coordination)

### Profit Potential

**Lowest → Highest**
1. YES/NO Imbalance: 0.5-2%
2. Cross-Market: 0.5-3%
3. Correlated Events: 1-5%
4. Multi-Leg: 2-8%

### Risk Level

**Safest → Riskiest**
1. YES/NO Imbalance (nearly risk-free)
2. Cross-Market (low execution risk)
3. Correlated Events (moderate assumptions)
4. Multi-Leg (highest complexity risk)

### Recommended for Beginners

Start with:
1. **YES/NO Imbalance** - Learn the basics
2. **Cross-Market** - Once comfortable

Add later:
3. **Correlated Events** - When you understand markets better
4. **Multi-Leg** - Advanced strategy

## Best Practices

### Strategy Selection

**Conservative Portfolio** (Low Risk):
```yaml
strategies:
  - yes_no_imbalance
  - cross_market
min_arbitrage_percentage: 1.0
kelly_fraction: 0.1
```

**Balanced Portfolio** (Medium Risk):
```yaml
strategies:
  - yes_no_imbalance
  - cross_market
  - correlated_events
min_arbitrage_percentage: 0.5
kelly_fraction: 0.25
```

**Aggressive Portfolio** (Higher Risk):
```yaml
strategies:
  - cross_market
  - correlated_events
  - multi_leg
min_arbitrage_percentage: 0.3
kelly_fraction: 0.5
```

### Timing Considerations

- **YES/NO Imbalance**: Execute immediately (closes fast)
- **Cross-Market**: Execute simultaneously (spread can narrow)
- **Correlated Events**: Can wait for better prices
- **Multi-Leg**: Requires careful timing across all legs

### Position Sizing

**By Strategy**:
- YES/NO: Full Kelly (low risk)
- Cross-Market: 0.5× Kelly
- Correlated: 0.25× Kelly
- Multi-Leg: 0.1× Kelly

### Common Mistakes to Avoid

1. **Ignoring Gas Costs**: Always calculate net profit
2. **Simultaneous Execution**: Don't execute legs sequentially
3. **Overconfidence**: Backtest doesn't guarantee future results
4. **Over-leveraging**: Start small, scale gradually
5. **Ignoring Liquidity**: Can't execute if no volume

### Market Selection

**Best Markets for Each Strategy**:

- **YES/NO Imbalance**: High-volume, liquid markets
- **Cross-Market**: Similar events across categories
- **Correlated Events**: Political, economic indicators
- **Multi-Leg**: Championship tournaments, election primaries

### Performance Monitoring

Track by strategy:
```python
# Example performance tracking
{
    "yes_no_imbalance": {
        "opportunities": 45,
        "executed": 38,
        "win_rate": 97%,
        "avg_profit": 1.2%
    },
    "cross_market": {
        "opportunities": 23,
        "executed": 15,
        "win_rate": 87%,
        "avg_profit": 1.8%
    }
}
```

## Advanced Topics

### Combining Strategies

Execute multiple strategies on same markets:
```python
# Market has both YES/NO imbalance AND cross-market opportunity
# Prioritize based on:
1. Profit potential
2. Execution certainty
3. Capital requirements
```

### Dynamic Strategy Adjustment

Adjust based on market conditions:
```python
# High volatility → Enable more strategies
# Low liquidity → Focus on YES/NO imbalance
# High gas → Increase min_profit_threshold
```

### Strategy-Specific Risk Management

Different risk limits per strategy:
```yaml
risk_limits:
  yes_no_imbalance:
    max_position: 2000
    stop_loss: 0.03
  multi_leg:
    max_position: 500
    stop_loss: 0.10
```

## Conclusion

Each strategy has its place in a well-diversified arbitrage portfolio. Start conservative, learn from experience, and gradually expand to more complex strategies as you gain confidence and capital.

**Remember**: The best strategy is the one you understand well and execute consistently.
