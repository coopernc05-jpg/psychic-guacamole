# Usage Guide

## Quick Start

### 1. Installation

Run the setup script:
```bash
./setup.sh
```

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configuration

Edit `.env` file:
```env
POLYMARKET_WS_URL=wss://ws-subscriptions-clob.polymarket.com/ws/market
MIN_PROFIT_THRESHOLD=0.01  # 1% minimum profit
```

### 3. Run Demo

Test the arbitrage detection with mock data:
```bash
python demo.py
```

### 4. Run the Bot

With real Polymarket market IDs:
```bash
python main.py
```

## Understanding the Output

### Arbitrage Types

#### 1. Cross-Market Arbitrage
```
Type: cross_market
Expected Profit: 5.00%
Markets Involved: 2

Strategy: Buy YES on both markets
Event: Presidential Election
Market 1 YES ask: 0.46
Market 2 YES ask: 0.49
Total cost: 0.95 (5% profit)
```

**Explanation**: Two markets for the same event have complementary outcomes. Buying YES on both costs less than $1, guaranteeing profit.

#### 2. YES/NO Imbalance
```
Type: yes_no_imbalance
Expected Profit: 3.00%
Markets Involved: 1

Strategy: Buy both YES and NO
YES ask: 0.49
NO ask: 0.48
Total cost: 0.97 (3% profit)
```

**Explanation**: In a single market, the combined cost of buying YES and NO is less than $1, creating a guaranteed profit.

#### 3. Multi-Leg Arbitrage
```
Type: multi_leg
Expected Profit: 7.00%
Markets Involved: 3

Strategy: Buy YES on all markets
Team A: 0.31
Team B: 0.33
Team C: 0.29
Total cost: 0.93 (7% profit)
```

**Explanation**: Three mutually exclusive outcomes with a combined cost less than $1, allowing profit regardless of which outcome occurs.

## Advanced Usage

### Custom Market Monitoring

```python
import asyncio
from main import PolymarketArbitrageBot

async def monitor_specific_markets():
    bot = PolymarketArbitrageBot()
    
    # Get market IDs from Polymarket
    market_ids = [
        "0x1234567890abcdef...",  # Market 1
        "0xfedcba0987654321...",  # Market 2
        "0xabcdef1234567890...",  # Market 3
    ]
    
    # Start monitoring
    await bot.start(market_ids)

asyncio.run(monitor_specific_markets())
```

### Custom Callbacks

```python
from polymarket_client import PolymarketWSClient

async def my_price_handler(price_data):
    print(f"Market {price_data['market_id']}: YES={price_data['yes_price']}")

client = PolymarketWSClient("wss://...")
client.add_price_callback(my_price_handler)
await client.connect()
await client.listen()
```

### Adjusting Sensitivity

Change the minimum profit threshold:
```python
from arbitrage_detector import ArbitrageDetector

# Only alert on opportunities with 5%+ profit
detector = ArbitrageDetector(min_profit_threshold=0.05)
```

## Finding Market IDs

### Method 1: Polymarket Website
1. Visit https://polymarket.com
2. Navigate to a market
3. Check the URL or inspect the page source

### Method 2: Polymarket API
```python
import requests

response = requests.get("https://clob.polymarket.com/markets")
markets = response.json()

for market in markets:
    print(f"{market['question']}: {market['id']}")
```

## Troubleshooting

### WebSocket Connection Issues
```
Error: Failed to connect to WebSocket
```

**Solution**: Check your internet connection and firewall settings. Some networks block WebSocket connections.

### No Opportunities Found
```
No arbitrage opportunities found!
```

**Causes**:
- Markets are efficiently priced
- Not enough markets being monitored
- Profit threshold is too high

**Solutions**:
- Monitor more markets
- Lower `MIN_PROFIT_THRESHOLD` in `.env`
- Check during high volatility events

### Invalid Market Data
```
Error processing message: KeyError
```

**Solution**: The market data format may have changed. Check Polymarket's API documentation for updates.

## Best Practices

### 1. Start with Demo
Always test with `demo.py` before using real market data.

### 2. Monitor Multiple Markets
The more markets you monitor, the more opportunities you'll find.

### 3. Set Realistic Thresholds
Account for:
- Transaction fees (typically 2%)
- Gas costs (on blockchain)
- Slippage (price changes during execution)
- Execution time

### 4. Act Quickly
Arbitrage opportunities disappear fast. Consider:
- Automated execution (with proper risk management)
- Pre-funded accounts
- Low-latency connections

### 5. Understand the Markets
Before trading:
- Read the market rules
- Understand the outcomes
- Check the resolution criteria
- Verify the event timing

## Risk Management

### Transaction Costs
```
Gross Profit: 3.5%
- Transaction Fee (2%): -2.0%
- Gas Cost (~$5): -0.5%
= Net Profit: 1.0%
```

### Execution Risk
- Market prices can change before your order executes
- Some markets may have low liquidity
- Network congestion can delay transactions

### Smart Contract Risk
- Polymarket runs on blockchain (Polygon)
- Understand smart contract risks
- Never invest more than you can afford to lose

## Support

For issues or questions:
1. Check the main [README.md](README.md)
2. Review this usage guide
3. Open an issue on GitHub

## License

MIT License - See LICENSE file
