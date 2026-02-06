# Polymarket Arbitrage Detection Bot

A real-time arbitrage detection system for Polymarket that monitors multiple markets and identifies profitable trading opportunities.

## Features

### Multi-Market Arbitrage Detection
- **Cross-Market Arbitrage**: Detects arbitrage opportunities across different markets for the same event
- **YES/NO Imbalance Arbitrage**: Identifies pricing inefficiencies within a single market where YES + NO prices don't equal 1
- **Multi-Leg Arbitrage**: Finds complex arbitrage opportunities across 3+ related markets

### Real-Time Monitoring
- **WebSocket Integration**: Maintains persistent connections to Polymarket for live price feeds
- **Continuous Price Monitoring**: Tracks price changes across all subscribed markets in real-time
- **Instant Alerts**: Immediately notifies when arbitrage opportunities are detected

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

# Arbitrage Detection Settings
MIN_PROFIT_THRESHOLD=0.01    # Minimum profit (1%) to alert
MAX_SPREAD_THRESHOLD=0.05    # Maximum spread to consider
```

## Usage

### Basic Usage

Run the bot with default settings:

```bash
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

3. **main.py**: Main application logic
   - Coordinates WebSocket client and detector
   - Manages market subscriptions
   - Alerts on opportunities

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
```

## Development

### Project Structure
```
psychic-guacamole/
├── main.py                 # Main application
├── polymarket_client.py    # WebSocket client
├── arbitrage_detector.py   # Arbitrage detection logic
├── requirements.txt        # Python dependencies
├── .env.example           # Example configuration
└── README.md              # Documentation
```

### Testing

To test the arbitrage detection logic without live data:

```python
from arbitrage_detector import ArbitrageDetector

detector = ArbitrageDetector(min_profit_threshold=0.01)

# Mock market data
market_data = {
    "market1": {
        "market_id": "market1",
        "yes_ask": 0.48,
        "no_ask": 0.48,
        "yes_bid": 0.45,
        "no_bid": 0.45,
        "event_name": "Test Event"
    }
}

opportunities = detector.detect_all_opportunities(market_data)
for opp in opportunities:
    print(opp)
```

## Important Notes

### Risk Disclaimer
- This bot is for educational and research purposes
- Arbitrage opportunities may disappear quickly
- Consider transaction fees, gas costs, and execution risk
- Past performance does not guarantee future results

### Limitations
- Requires active Polymarket market IDs
- WebSocket connection stability depends on network
- Does not execute trades automatically
- Does not account for:
  - Transaction fees
  - Slippage
  - Execution delays
  - Market liquidity

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.
