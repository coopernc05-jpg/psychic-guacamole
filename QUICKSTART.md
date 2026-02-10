# Quick Start Guide

Get the Polymarket Arbitrage Bot running in 5 minutes.

## Installation

```bash
# Clone repository
git clone https://github.com/coopernc05-jpg/psychic-guacamole.git
cd psychic-guacamole

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

## Basic Configuration

Edit `.env`:
```bash
# Set initial capital for position sizing
INITIAL_CAPITAL=10000

# Enable dry run mode (no real trades)
DRY_RUN=true

# Optional: Add notification webhooks
DISCORD_WEBHOOK_URL=your_webhook_url
```

## Run in Alert Mode

```bash
python -m src.main
```

The bot will:
1. Connect to Polymarket API (mock mode currently)
2. Monitor markets for arbitrage opportunities
3. Detect and score opportunities
4. Log alerts to console and logs/

## Understanding the Output

When an opportunity is detected, you'll see:
```
🎯 ARBITRAGE OPPORTUNITY DETECTED
================================================================================
Type: YesNoImbalanceOpportunity
Details: YES/NO Imbalance: Market XYZ... | YES: 0.450, NO: 0.480, Sum: 0.930 | Action: buy_both | Profit: 7.53%
Score: 85.23/100
Profit Score: 75.00
Capital Efficiency: 90.00
Confidence: 90.00
Risk: 10.00
Recommended Position Size: $125.00
================================================================================
```

## Key Metrics Explained

- **Score**: Overall opportunity ranking (0-100)
- **Profit Score**: Expected profit potential
- **Capital Efficiency**: Profit per dollar invested
- **Confidence**: How certain the opportunity is
- **Risk**: Risk level (lower is better)
- **Position Size**: Recommended capital to allocate

## Configuration Profiles

### Conservative (Recommended for Beginners)
```yaml
# config.yaml
min_profit_threshold: 10.0
kelly_fraction: 0.1
max_position_size: 100
max_total_exposure: 500
strategies:
  - yes_no_imbalance
```

### Balanced
```yaml
min_profit_threshold: 5.0
kelly_fraction: 0.25
max_position_size: 500
max_total_exposure: 2000
strategies:
  - yes_no_imbalance
  - cross_market
```

### Aggressive
```yaml
min_profit_threshold: 2.0
kelly_fraction: 0.5
max_position_size: 1000
max_total_exposure: 5000
strategies:
  - yes_no_imbalance
  - cross_market
  - correlated_events
  - multi_leg
```

## Testing Individual Components

### Test Configuration
```bash
python -c "from src.config import load_config; print(load_config())"
```

### Test Strategy Detection
```bash
python -c "
from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceStrategy
from src.market.market_data import Market, MarketStatus
from datetime import datetime

# Create test market
market = Market(
    market_id='test',
    question='Test?',
    description='Test',
    category='test',
    end_date=datetime.now(),
    status=MarketStatus.ACTIVE,
    yes_price=0.45,
    no_price=0.48,
    yes_bid=0.44,
    yes_ask=0.46,
    no_bid=0.47,
    no_ask=0.49,
    volume_24h=1000,
    liquidity=5000
)

strategy = YesNoImbalanceStrategy()
opps = strategy.detect([market])
print(f'Found {len(opps)} opportunities')
if opps:
    print(opps[0])
"
```

### Test Kelly Criterion
```bash
python -c "
from src.execution.position_sizing import kelly_criterion

# 60% win probability, 100% return
kelly = kelly_criterion(0.6, 1.0)
print(f'Kelly Criterion: {kelly:.3f} ({kelly*100:.1f}% of capital)')
"
```

## Running Tests

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_strategies.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Common Issues

### Import Errors
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt

# Check Python version (requires 3.10+)
python --version
```

### Configuration Errors
```bash
# Verify config file exists
ls -la config.yaml

# Test loading
python -c "from src.config import load_config; load_config()"
```

### No Opportunities Detected
- This is normal in mock mode (no real Polymarket API connected)
- Lower `min_arbitrage_percentage` in config.yaml
- Check that strategies are enabled

## Next Steps

1. **Read Documentation**
   - [SETUP.md](docs/SETUP.md) - Complete setup guide
   - [STRATEGIES.md](docs/STRATEGIES.md) - Strategy details
   - [API.md](docs/API.md) - API reference

2. **Customize Configuration**
   - Adjust risk parameters
   - Enable/disable strategies
   - Set up notifications

3. **Monitor Performance**
   - Check logs in `logs/`
   - Review opportunity logs in `data/opportunities/`
   - Analyze performance metrics

4. **Transition to Auto-Trade** (Advanced)
   - Complete wallet setup
   - Test in dry-run mode
   - Start with small positions
   - Monitor closely

## Safety Checklist

Before enabling auto-trade:
- [ ] Tested in alert mode for 24+ hours
- [ ] Verified opportunity detection
- [ ] Configured notifications
- [ ] Set conservative position limits
- [ ] Funded wallet with test amount
- [ ] Enabled dry-run mode first
- [ ] Read all documentation
- [ ] Understand all risks

## Support

- **Documentation**: Check docs/ folder
- **Issues**: Open GitHub issue
- **Logs**: Review logs/arbitrage_bot.log

## Quick Commands Reference

```bash
# Start bot
python -m src.main

# Run tests
pytest tests/

# Check logs
tail -f logs/arbitrage_bot.log

# View opportunities
cat data/opportunities/opportunities_*.jsonl | tail -10

# Check git status
git status

# Update code
git pull origin main
```

## Performance Expectations

In alert mode with mock data:
- **Opportunities detected**: Variable (depends on mock data)
- **CPU usage**: Low (<5%)
- **Memory**: ~100MB
- **Network**: Minimal (mock mode)

With real Polymarket API:
- **Opportunities**: 3-20 per day (market dependent)
- **Latency**: <500ms detection
- **API calls**: ~100/hour
- **WebSocket**: Persistent connection

## Example Session

```bash
$ python -m src.main
2024-02-06 21:50:00 | INFO     | Polymarket Arbitrage Bot initialized
2024-02-06 21:50:00 | INFO     | Mode: alert
2024-02-06 21:50:00 | INFO     | Strategies: cross_market, yes_no_imbalance
2024-02-06 21:50:00 | INFO     | Starting Polymarket Arbitrage Bot...
2024-02-06 21:50:00 | INFO     | Connected to Polymarket API
2024-02-06 21:50:01 | INFO     | Starting iteration 1
2024-02-06 21:50:01 | DEBUG    | Fetched 50 markets
2024-02-06 21:50:01 | DEBUG    | YES/NO imbalance strategy found 2 opportunities
2024-02-06 21:50:01 | DEBUG    | Cross-market strategy found 1 opportunities
2024-02-06 21:50:01 | INFO     | Total opportunities detected: 3 from 50 markets
2024-02-06 21:50:01 | INFO     | Found 3 profitable opportunities
================================================================================
🎯 ARBITRAGE OPPORTUNITY DETECTED
...
```

---

**Ready to maximize profit!** Start with alert mode, learn the system, then scale up gradually.
