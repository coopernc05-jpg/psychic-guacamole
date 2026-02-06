# Polymarket Arbitrage Bot - Technical Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Polymarket Arbitrage Bot                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│   WebSocket  │    │    Arbitrage     │    │     Main     │
│    Client    │───▶│    Detector      │◀───│  Application │
│              │    │                  │    │              │
└──────────────┘    └──────────────────┘    └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Polymarket  │    │  3 Detection     │    │   Alert &    │
│  WebSocket   │    │  Algorithms      │    │   Logging    │
│   Endpoint   │    │                  │    │              │
└──────────────┘    └──────────────────┘    └──────────────┘
```

## Core Components

### 1. polymarket_client.py
**Purpose**: Real-time communication with Polymarket

**Key Features**:
- WebSocket connection management
- Market subscription handling
- Price update processing
- Data caching and distribution

**Key Methods**:
- `connect()` - Establish WebSocket connection
- `subscribe_to_market(market_id)` - Subscribe to a market
- `listen()` - Process incoming messages
- `add_price_callback(callback)` - Register callback for price updates

### 2. arbitrage_detector.py
**Purpose**: Detect arbitrage opportunities across markets

**Detection Algorithms**:

#### Cross-Market Arbitrage
```python
# Example: Two complementary outcomes
Market A (Candidate A wins): YES @ 0.45
Market B (Candidate B wins): YES @ 0.50
Total Cost: 0.95
Profit: 0.05 (5%)
```

#### YES/NO Imbalance
```python
# Example: Single market inefficiency
Market: Event occurs
YES ask: 0.48
NO ask: 0.48
Total Cost: 0.96
Profit: 0.04 (4%)
```

#### Multi-Leg Arbitrage
```python
# Example: Three mutually exclusive outcomes
Team A: YES @ 0.30
Team B: YES @ 0.33
Team C: YES @ 0.29
Total Cost: 0.92
Profit: 0.08 (8%)
```

**Key Methods**:
- `detect_all_opportunities()` - Run all detection algorithms
- `detect_cross_market_arbitrage()` - Find cross-market opportunities
- `detect_yes_no_imbalance()` - Find single-market inefficiencies
- `detect_multi_leg_arbitrage()` - Find multi-leg opportunities

### 3. main.py
**Purpose**: Coordinate components and manage bot lifecycle

**Key Features**:
- Bot initialization and configuration
- Market monitoring coordination
- Opportunity alerting
- Error handling and logging

**Key Methods**:
- `start(market_ids)` - Start monitoring markets
- `on_price_update()` - Handle price updates
- `check_for_arbitrage()` - Trigger arbitrage detection
- `alert_opportunity()` - Alert on opportunities

## Data Flow

```
1. WebSocket receives price update
         │
         ▼
2. Client parses and caches data
         │
         ▼
3. Callbacks triggered (main app)
         │
         ▼
4. Detector analyzes all markets
         │
         ▼
5. Opportunities identified
         │
         ▼
6. Alerts generated and logged
```

## Configuration

### Environment Variables (.env)
```env
POLYMARKET_WS_URL          # WebSocket endpoint
POLYMARKET_API_URL         # REST API endpoint
MIN_PROFIT_THRESHOLD       # Minimum profit to alert (e.g., 0.01 = 1%)
MAX_SPREAD_THRESHOLD       # Maximum spread to consider
```

### Thresholds
- **MIN_PROFIT_THRESHOLD**: Filters opportunities below this profit level
- **Margin for fees**: Built-in 1% margin for transaction costs

## Testing

### Unit Tests (test_arbitrage.py)
```bash
python test_arbitrage.py
```

Tests cover:
- YES/NO imbalance detection (buy and sell)
- Cross-market arbitrage detection
- Multi-leg arbitrage detection
- Minimum profit threshold filtering
- Edge cases and no-arbitrage scenarios

### Demo Mode (demo.py)
```bash
python demo.py
```

Features:
- Mock market data generation
- All detection algorithms
- Detailed opportunity reporting
- No external dependencies

## Performance Characteristics

### Speed
- Real-time WebSocket updates (<100ms latency)
- In-memory market data caching
- Efficient opportunity detection (O(n²) for n markets)

### Scalability
- Can monitor 100+ markets simultaneously
- Opportunity detection scales with market count
- Memory usage: ~1KB per market

### Reliability
- Automatic reconnection on disconnect
- Error handling and logging
- Graceful shutdown on interruption

## Arbitrage Mathematics

### Cross-Market Formula
```
If P(A) + P(B) < 1 and A,B are mutually exclusive:
Profit = 1 - (P(A) + P(B))
```

### YES/NO Imbalance Formula
```
If P(YES) + P(NO) < 1:
Profit = 1 - (P(YES) + P(NO))

If P(YES) + P(NO) > 1 (for bids):
Profit = (P(YES) + P(NO)) - 1
```

### Multi-Leg Formula
```
For n mutually exclusive outcomes:
If Σ P(i) < 1:
Profit = 1 - Σ P(i)
```

## Security Considerations

### API Keys
- No API keys required for public data
- Keep `.env` file secure if using authenticated endpoints

### Rate Limiting
- WebSocket: Generally no rate limits on subscriptions
- REST API: Check Polymarket's rate limits

### Data Validation
- All price data validated before processing
- NaN and invalid values filtered
- Market data integrity checks

## Limitations

### What the Bot Does NOT Do
- ❌ Execute trades automatically
- ❌ Manage funds or wallets
- ❌ Account for gas fees in profit calculations
- ❌ Handle order book depth analysis
- ❌ Provide investment advice

### Known Limitations
- Assumes infinite liquidity (real markets have depth limits)
- Does not account for slippage
- Transaction fees must be considered separately
- Execution delay not factored into profit calculations

## Future Enhancements

### Possible Additions
1. **Automated Trading**: Execute trades automatically
2. **Order Book Analysis**: Consider market depth
3. **Fee Calculator**: Account for all transaction costs
4. **Historical Analysis**: Track and analyze past opportunities
5. **Multi-Exchange**: Support other prediction markets
6. **Machine Learning**: Predict opportunity likelihood

### Integration Points
- Trading bots (for execution)
- Notification systems (Discord, Telegram, email)
- Database (for historical tracking)
- Analytics dashboard (visualization)

## Deployment

### Local Development
```bash
./setup.sh
python demo.py
python main.py
```

### Production Considerations
- Run as systemd service (Linux)
- Use process manager (PM2, supervisord)
- Configure logging to file
- Set up monitoring/alerting
- Consider using message queue for scaling

## Support & Maintenance

### Logging
All components use Python's logging module:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Failures requiring attention

### Monitoring
Key metrics to track:
- WebSocket connection uptime
- Number of opportunities detected
- Average profit per opportunity
- Detection latency

### Troubleshooting
See [USAGE.md](USAGE.md) for common issues and solutions.

## License

MIT License - See LICENSE file for details
