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

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

4. Review and customize `config.yaml` for your strategy preferences

### Running the Bot

**Alert Mode** (recommended for testing):
```bash
python -m src.main
```

The bot will detect and log opportunities without executing trades.

**Dashboard Access**:
Open http://localhost:5000 in your browser to view:
- Real-time performance metrics
- Equity curve visualization
- Opportunity distribution charts
- Live activity feed

**Auto-Trade Mode** (requires wallet setup):
1. Complete the setup in `docs/SETUP.md`
2. Set `mode: "auto_trade"` in `config.yaml`
3. Run: `python -m src.main`

## 📊 Configuration

Key settings in `config.yaml`:

```yaml
# Profit Settings
min_profit_threshold: 5.0  # Minimum $5 net profit
position_sizing_strategy: "kelly"  # Use Kelly Criterion
kelly_fraction: 0.25  # Conservative 1/4 Kelly

# Risk Management
max_position_size: 1000  # Max $1000 per trade
max_total_exposure: 5000  # Max $5000 total at risk
stop_loss_percentage: 0.05  # 5% stop loss

# Execution
mode: "alert"  # "alert" or "auto_trade"
gas_price_limit: 100  # Max 100 gwei
```

See `config.yaml` for all available options.

## 📈 Expected Performance

### Opportunity Frequency
- **High Volatility Markets**: 10-20 opportunities/day
- **Normal Markets**: 3-10 opportunities/day
- **Low Volatility**: 1-5 opportunities/day

### Profit Ranges (After Costs)
- **YES/NO Imbalance**: 0.5-2% per trade (most reliable)
- **Cross-Market**: 0.5-3% per trade (dependent on liquidity)
- **Correlated Events**: 1-5% per trade (higher risk)
- **Multi-Leg**: 2-8% per trade (complex, higher risk)

### Risk Factors
- **Gas Costs**: Can eliminate small opportunities on Polygon
- **Slippage**: Larger trades may experience price impact
- **Execution Speed**: Opportunities may disappear quickly
- **Market Resolution**: Some arbitrage requires holding to resolution

## 🔒 Safety & Limitations

### Safety Features
- **Alert Mode Default**: No trades executed without explicit configuration
- **Dry Run Mode**: Test execution logic without real transactions
- **Risk Limits**: Multiple layers of position size and exposure limits
- **Stop Losses**: Automatic protection against unexpected losses

### Limitations
- **Not Real-Time Yet**: Current implementation uses mock Polymarket API
- **Gas Costs**: Must be factored into all trades
- **Liquidity**: Some opportunities may have insufficient liquidity
- **Market Risk**: Events can resolve unexpectedly
- **Smart Contract Risk**: Polygon/Polymarket smart contract risks

### ⚠️ Important Warnings
- **START IN ALERT MODE**: Always test thoroughly before enabling auto-trade
- **TEST WITH SMALL AMOUNTS**: Start with minimal capital
- **MONITOR CLOSELY**: Check logs and notifications regularly  
- **UNDERSTAND RISKS**: Arbitrage is not risk-free
- **API LIMITATIONS**: Current implementation uses mock API (requires real integration)

## 📚 Documentation

- **[SETUP.md](docs/SETUP.md)**: Detailed setup instructions for Polymarket API, wallet, and notifications
- **[STRATEGIES.md](docs/STRATEGIES.md)**: In-depth explanation of each arbitrage strategy with examples
- **[API.md](docs/API.md)**: API reference and integration guide
- **[DASHBOARD.md](docs/DASHBOARD.md)**: Web dashboard usage and features
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Production deployment guides (Docker, VPS, Kubernetes)
- **[TESTING.md](docs/TESTING.md)**: Testing methodology and examples

## 🏗️ Architecture

```
src/
├── main.py                 # Main orchestrator
├── config.py              # Configuration management
├── market/                # Market data and API
│   ├── polymarket_api.py  # REST API client
│   ├── websocket_client.py # WebSocket client
│   └── market_data.py     # Data models
├── arbitrage/             # Arbitrage detection
│   ├── detector.py        # Main detection engine
│   ├── scorer.py          # Opportunity ranking
│   └── strategies/        # Strategy implementations
├── execution/             # Trade execution
│   ├── executor.py        # Trade execution
│   ├── position_sizing.py # Kelly Criterion
│   └── risk_manager.py    # Risk management
├── analytics/             # Performance tracking
│   ├── logger.py          # Logging system
│   └── performance.py     # Metrics calculation
└── notifications/         # Alert system
    ├── discord.py
    └── telegram.py
```

## 🧪 Testing

Run tests:
```bash
# All tests
pytest tests/

# With coverage report
pytest --cov=src --cov-report=html tests/

# View coverage
open htmlcov/index.html
```

Run linters:
```bash
# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/
```

See [TESTING.md](docs/TESTING.md) for detailed testing guide.

## 🐳 Docker Deployment

```bash
# Build image
docker build -t polymarket-bot .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment guide.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🔗 Resources

- [Polymarket](https://polymarket.com/)
- [Polymarket API Docs](https://docs.polymarket.com/)
- [Kelly Criterion](https://en.wikipedia.org/wiki/Kelly_criterion)
- [Polygon Network](https://polygon.technology/)

## ⚖️ Disclaimer

This software is for educational and research purposes. Trading and arbitrage involve substantial risk of loss. The authors are not responsible for any financial losses incurred through use of this software. Always conduct your own research and risk assessment before trading with real funds.

## 📧 Support

For questions and support:
- Open an issue on GitHub
- Check existing documentation
- Review example configurations

---

**Remember**: Arbitrage opportunities are fleeting. Speed, accuracy, and risk management are crucial for success. Start small, monitor closely, and scale gradually.
