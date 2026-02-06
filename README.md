# Polymarket Arbitrage Detection Bot

A real-time arbitrage detection and automatic trading system for Polymarket that monitors multiple markets, identifies profitable trading opportunities, and can execute trades automatically.

## Features

### Multi-Market Arbitrage Detection
- **Cross-Market Arbitrage**: Detects arbitrage opportunities across different markets for the same event
- **YES/NO Imbalance Arbitrage**: Identifies pricing inefficiencies within a single market where YES + NO prices don't equal 1
- **Multi-Leg Arbitrage**: Finds complex arbitrage opportunities across 3+ related markets

### Real-Time Monitoring
- **WebSocket Integration**: Maintains persistent connections to Polymarket for live price feeds
- **Continuous Price Monitoring**: Tracks price changes across all subscribed markets in real-time
- **Instant Alerts**: Immediately notifies when arbitrage opportunities are detected

### Automatic Trade Execution (NEW!)
- **Auto-Trading**: Automatically executes trades when arbitrage opportunities are detected
- **Dry-Run Mode**: Test trading strategies without risking real money
- **Smart Order Generation**: Creates optimal orders based on opportunity type
- **Position Sizing**: Configurable maximum trade size with automatic scaling
- **Execution Tracking**: Comprehensive logging and statistics for all trades

## Installation

1. Clone the repository:
```bash
git clone https://github.com/coopernc05-jpg/psychic-guacamole.git
cd psychic-guacamole
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Edit `.env` to configure the bot:

```env
# Polymarket Configuration
POLYMARKET_WS_URL=wss://ws-subscriptions-clob.polymarket.com/ws/market
POLYMARKET_API_URL=https://clob.polymarket.com

# API Authentication (required for live trading)
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_PRIVATE_KEY=your_private_key_here

# Arbitrage Detection Settings
MIN_PROFIT_THRESHOLD=0.01    # Minimum profit (1%) to alert
MAX_SPREAD_THRESHOLD=0.05    # Maximum spread to consider

# Trading Settings
AUTO_TRADING_ENABLED=false   # Set to 'true' to enable automatic trading
DRY_RUN=true                 # Set to 'false' for live trading (BE CAREFUL!)
MAX_TRADE_SIZE=100.0         # Maximum amount in USD to invest per opportunity
```

### ⚠️ IMPORTANT SAFETY NOTES

- **Always start with `DRY_RUN=true`** to test without risking real money
- **Start with small `MAX_TRADE_SIZE`** values when going live
- **Never share your API keys** or commit them to version control
- **Understand the risks** - arbitrage opportunities can disappear quickly, and you may lose money
- **Test thoroughly** in dry-run mode before enabling live trading

## Usage

### Detection Only (Safe Mode)

Run the bot to detect opportunities without trading:

```bash
python main.py
```

By default, auto-trading is disabled. The bot will only alert you to opportunities.

### Demo Modes

Test arbitrage detection with mock data:
```bash
python demo.py
```

Test trade execution in dry-run mode:
```bash
python demo_trading.py
```

### Enable Automatic Trading

⚠️ **WARNING: Only enable auto-trading after thorough testing!**

1. First, test in dry-run mode:
```bash
# In .env file:
AUTO_TRADING_ENABLED=true
DRY_RUN=true
MAX_TRADE_SIZE=10.0

python main.py
```

2. Once confident, enable live trading (at your own risk):
```bash
# In .env file:
AUTO_TRADING_ENABLED=true
DRY_RUN=false
MAX_TRADE_SIZE=50.0  # Start small!
POLYMARKET_API_KEY=your_key
POLYMARKET_PRIVATE_KEY=your_key

python main.py
```

### Programmatic Usage

```python
import asyncio
from main import PolymarketArbitrageBot

async def run_bot():
    bot = PolymarketArbitrageBot()
    
    # Specify market IDs to monitor
    market_ids = [
        "0x1234...",  # Replace with actual Polymarket market IDs
        "0x5678...",
    ]
    
    await bot.start(market_ids)

asyncio.run(run_bot())
```

### Getting Market IDs

To find Polymarket market IDs:
1. Visit [Polymarket](https://polymarket.com)
2. Navigate to a market
3. Extract the market ID from the URL or use the Polymarket API

## Architecture

### Core Components

1. **polymarket_client.py**: WebSocket client for real-time Polymarket data
   - Manages WebSocket connections
   - Handles market subscriptions
   - Processes price updates

2. **arbitrage_detector.py**: Arbitrage detection algorithms
   - Cross-market arbitrage detection
   - YES/NO imbalance detection
   - Multi-leg arbitrage detection

3. **trade_executor.py**: Automatic trade execution (NEW!)
   - Generates optimal orders for each arbitrage type
   - Executes trades via Polymarket API
   - Tracks execution history and statistics
   - Supports dry-run mode for safe testing

4. **main.py**: Main application logic
   - Coordinates WebSocket client and detector
   - Manages market subscriptions
   - Alerts on opportunities
   - Executes trades when auto-trading is enabled

## Arbitrage Strategies

### 1. Cross-Market Arbitrage
Exploits pricing differences across markets for the same event:
```
Market A: Event outcome X at 0.45
Market B: Event outcome Y at 0.45
Total cost: 0.90 (10% profit if outcomes are mutually exclusive)
```

### 2. YES/NO Imbalance Arbitrage
Exploits pricing inefficiencies within a single market:
```
Market: Question about event
YES price: 0.48
NO price: 0.48
Total cost: 0.96 (4% guaranteed profit)
```

### 3. Multi-Leg Arbitrage
Exploits opportunities across 3+ related markets:
```
Event with 3 outcomes:
Outcome A: 0.30
Outcome B: 0.35
Outcome C: 0.30
Total cost: 0.95 (5% profit if outcomes are exhaustive)
```

## Example Output

### Detection Only Mode
```
================================================================================
🚨 ARBITRAGE OPPORTUNITY DETECTED!
Type: yes_no_imbalance
Expected Profit: 3.5000%
Markets Involved: 1
Details: {
  'event_name': 'Presidential Election Winner',
  'yes_ask': 0.475,
  'no_ask': 0.490,
  'total_cost': 0.965,
  'strategy': 'Buy both YES and NO'
}
================================================================================
ℹ️  Auto-trading is DISABLED - no trade executed
```

### Auto-Trading Enabled (Dry-Run)
```
================================================================================
🚨 ARBITRAGE OPPORTUNITY DETECTED!
Type: yes_no_imbalance
Expected Profit: 3.0000%
Markets Involved: 1
Details: {...}
================================================================================
⚡ Auto-trading is ENABLED - executing trade...
DRY RUN: Simulating order execution
✅ Trade executed successfully!
   Invested: $100.00
   Expected Return: $103.00
   Expected Profit: $3.00
```

## Development

### Project Structure
```
psychic-guacamole/
├── main.py                   # Main application with auto-trading
├── polymarket_client.py      # WebSocket client
├── arbitrage_detector.py     # Arbitrage detection logic
├── trade_executor.py         # Automatic trade execution (NEW!)
├── demo.py                   # Detection demo with mock data
├── demo_trading.py           # Trading demo (dry-run mode)
├── test_arbitrage.py         # Unit tests for detection
├── test_trade_executor.py    # Unit tests for trading
├── requirements.txt          # Python dependencies
├── .env.example             # Example configuration
└── README.md                # Documentation
```

### Testing

Run all tests:
```bash
python test_arbitrage.py      # Test arbitrage detection
python test_trade_executor.py # Test trade execution
```

Test with demos:
```bash
python demo.py                # Test detection with mock data
python demo_trading.py        # Test trading in dry-run mode
```

## Important Notes

### Risk Disclaimer
- ⚠️ **USE AT YOUR OWN RISK** - This bot involves real money when live trading is enabled
- Arbitrage opportunities may disappear before trades complete
- You can lose money due to:
  - Transaction fees and gas costs
  - Slippage (price changes during execution)
  - Execution delays
  - Market volatility
  - Software bugs or errors
- **Always test in dry-run mode first**
- **Start with small trade sizes**
- Past performance does not guarantee future results
- This is for educational and research purposes

### Trading Limitations
- Requires Polymarket API key for live trading
- WebSocket connection stability depends on network
- Does not account for all costs:
  - Transaction fees (typically 2%)
  - Gas costs (on Polygon network)
  - Slippage
  - Market liquidity constraints
- Orders may not fill at expected prices
- Opportunities may vanish before execution completes

### Best Practices
1. **Always start with `DRY_RUN=true`**
2. **Test thoroughly** with small amounts before scaling up
3. **Monitor actively** - don't leave the bot running unattended initially
4. **Set conservative limits** on `MAX_TRADE_SIZE`
5. **Understand the markets** you're trading
6. **Keep API keys secure** - never commit them to version control
7. **Be prepared to lose money** - only trade what you can afford to lose

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.
