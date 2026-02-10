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
# Polymarket Arbitrage Bot

A comprehensive arbitrage detection and execution bot for Polymarket that **maximizes profit** through multiple arbitrage strategies, optimal position sizing, and automated risk management.

## 🎯 Features

### Arbitrage Detection Strategies
- **Cross-Market Arbitrage**: Detects price discrepancies for the same event across different markets
- **YES/NO Imbalance Arbitrage**: Finds opportunities where YES + NO prices ≠ 1.00
- **Multi-Leg Arbitrage**: Identifies complex arbitrage chains across 3+ related markets
- **Correlated Event Arbitrage**: Detects mispricing in related events with dependencies

### Profit Maximization Engine
- **Kelly Criterion** position sizing for optimal long-term growth
- Opportunity ranking by expected profit × confidence × capital efficiency
- Real-time gas cost calculation and profitability checks
- Slippage protection and limit order support
- Configurable minimum profit thresholds

### Real-time Monitoring
- WebSocket integration for live price feeds
- Simultaneous monitoring of 100+ markets
- Low-latency detection (<500ms)
- Event-driven architecture

### Risk Management
- Per-trade and total exposure limits
- Automatic stop-loss and profit-taking
- Position age monitoring
- Portfolio diversification tracking
- Comprehensive risk metrics

### Analytics & Performance Tracking
- Complete opportunity and execution logging
- Performance metrics: P&L, ROI, Sharpe ratio, win rate
- Market efficiency statistics
- Daily performance reports
- **Web Dashboard**: Real-time visualization with Chart.js

### Notifications
- Discord webhook integration
- Telegram bot support
- Alerts for opportunities, executions, and errors

### Production Infrastructure
- **Docker Support**: Containerized deployment with Docker Compose
- **CI/CD Pipeline**: Automated testing and deployment via GitHub Actions
- **Health Monitoring**: Health check endpoints and Prometheus metrics
- **Centralized Logging**: Log rotation and structured logging

## 🚀 Quick Start

### Installation

#### Option 1: Docker (Recommended for Production)

1. Clone the repository:
```bash
git clone https://github.com/coopernc05-jpg/psychic-guacamole.git
cd psychic-guacamole
```

2. Configure the bot:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

4. View logs and access dashboard:
```bash
docker-compose logs -f bot
# Dashboard: http://localhost:5000
```

#### Option 2: Local Development

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
2. Install dependencies:
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
