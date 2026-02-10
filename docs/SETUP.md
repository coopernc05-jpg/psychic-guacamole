# Setup Guide

Complete setup instructions for the Polymarket Arbitrage Bot.

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Git
- (Optional) Polymarket account for auto-trading
- (Optional) Discord/Telegram for notifications

## Installation

### 1. Clone and Install

```bash
# Clone repository
git clone https://github.com/coopernc05-jpg/psychic-guacamole.git
cd psychic-guacamole

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```bash
# Polymarket API (for auto-trading)
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_SECRET=your_secret_here

# Wallet (for auto-trading)
WALLET_PRIVATE_KEY=your_private_key_here
WALLET_ADDRESS=your_wallet_address_here

# Polygon RPC
POLYGON_RPC_URL=https://polygon-rpc.com

# Notifications (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Initial capital for position sizing
INITIAL_CAPITAL=10000

# Safety settings
DEBUG=false
DRY_RUN=true  # Set to false only when ready for real trades
```

### 3. Configuration File

Review and customize `config.yaml`:

```yaml
# Start with conservative settings
min_profit_threshold: 10.0  # Higher threshold for safety
kelly_fraction: 0.1  # Very conservative (1/10 Kelly)
max_position_size: 100  # Start small
max_total_exposure: 500  # Limit total exposure

# Enable only reliable strategies initially
strategies:
  - yes_no_imbalance  # Most reliable
  - cross_market

# Keep in alert mode
mode: "alert"
```

## Polymarket API Setup

### Getting API Credentials

1. **Create Polymarket Account**
   - Visit https://polymarket.com/
   - Sign up and complete KYC if required

2. **Generate API Keys**
   - Navigate to Account Settings → API
   - Create new API key
   - Save the key and secret securely
   - **Never commit these to version control**

3. **Configure API Access**
   ```bash
   # Add to .env
   POLYMARKET_API_KEY=your_key
   POLYMARKET_SECRET=your_secret
   ```

### API Rate Limits

Be aware of Polymarket API rate limits:
- REST API: Typically 100 requests/minute
- WebSocket: 1 connection recommended
- Adjust `refresh_interval` in config if hitting limits

## Wallet Configuration

### Setting Up Trading Wallet

⚠️ **Security Warning**: Never share your private key or commit it to version control.

1. **Create New Wallet** (Recommended)
   ```bash
   # Use a wallet management tool or MetaMask
   # Export private key for the bot
   ```

2. **Fund Wallet**
   - Add MATIC for gas fees (start with ~10 MATIC)
   - Add USDC for trading (start small: $100-500)
   - Use Polygon network, not Ethereum mainnet

3. **Configure in .env**
   ```bash
   WALLET_PRIVATE_KEY=0x...  # Your private key
   WALLET_ADDRESS=0x...      # Your wallet address
   ```

4. **Verify Setup**
   ```bash
   # Check balances
   python -c "from web3 import Web3; w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com')); print(w3.eth.get_balance('YOUR_ADDRESS'))"
   ```

### Wallet Security Best Practices

- **Use a dedicated wallet** for the bot only
- **Start with minimal funds** while testing
- **Enable 2FA** on all related accounts
- **Store private keys securely** (password manager, hardware wallet backup)
- **Never share private keys** with anyone
- **Regularly audit transactions** and balances

## Discord Notifications Setup

### Create Discord Webhook

1. **Create Discord Server** (or use existing)
   - Create a channel for bot notifications (e.g., #arbitrage-alerts)

2. **Create Webhook**
   - Channel Settings → Integrations → Webhooks
   - Create New Webhook
   - Name it "Arbitrage Bot"
   - Copy webhook URL

3. **Configure Bot**
   ```bash
   # Add to .env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

4. **Test Notification**
   ```python
   from discord_webhook import DiscordWebhook
   webhook = DiscordWebhook(url="YOUR_WEBHOOK_URL")
   webhook.content = "Bot setup successful!"
   webhook.execute()
   ```

### Discord Notification Types

The bot sends:
- 🎯 **Opportunity Alerts**: When arbitrage detected
- ✅ **Execution Alerts**: When trades executed
- ⚠️ **Error Alerts**: When errors occur
- 📊 **Performance Reports**: Daily summaries

## Telegram Notifications Setup

### Create Telegram Bot

1. **Talk to BotFather**
   - Open Telegram and search for @BotFather
   - Send `/newbot`
   - Follow prompts to create bot
   - Save the bot token

2. **Get Chat ID**
   - Start chat with your new bot
   - Send any message
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat_id` in the response

3. **Configure Bot**
   ```bash
   # Add to .env
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

4. **Test Notification**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
        -d "chat_id=<YOUR_CHAT_ID>&text=Test message"
   ```

## Testing in Alert Mode

### Initial Test Run

1. **Start in Alert Mode**
   ```bash
   # Ensure config.yaml has:
   mode: "alert"
   
   # Run bot
   python -m src.main
   ```

2. **Monitor Output**
   - Check console for detected opportunities
   - Verify notifications are received
   - Review logs in `logs/arbitrage_bot.log`

3. **Validate Detection**
   - Opportunities should show reasonable profit margins
   - Scores should be calculated correctly
   - Position sizes should be within limits

### What to Look For

✅ **Good signs**:
- Opportunities detected regularly
- Profit calculations make sense
- No error messages
- Notifications arriving

❌ **Red flags**:
- No opportunities for hours (may indicate API issues)
- Negative profit after costs
- Frequent errors or crashes
- Extremely high profit percentages (likely bugs)

## Transitioning to Auto-Trade

⚠️ **Only proceed after thorough testing in alert mode**

### Pre-Flight Checklist

- [ ] Ran in alert mode for at least 24 hours
- [ ] Verified opportunity detection accuracy
- [ ] Confirmed notifications working
- [ ] Reviewed logs for errors
- [ ] Funded wallet with test amount
- [ ] Verified gas price settings
- [ ] Set conservative position sizes
- [ ] Enabled `DRY_RUN=true` first

### Enable Auto-Trading

1. **Start with Dry Run**
   ```yaml
   # config.yaml
   mode: "auto_trade"
   
   # .env
   DRY_RUN=true
   ```
   
   This simulates trades without executing them.

2. **Monitor Dry Run**
   - Check execution logic
   - Verify trade sizing
   - Confirm risk management works

3. **Enable Live Trading**
   ```bash
   # .env - Only after dry run testing!
   DRY_RUN=false
   ```

4. **Start Small**
   ```yaml
   # config.yaml
   max_position_size: 50  # Very small positions
   max_total_exposure: 200
   min_profit_threshold: 10  # High threshold
   ```

5. **Monitor Closely**
   - Watch first few trades execute
   - Check transaction confirmations on Polygonscan
   - Verify P&L calculations
   - Monitor gas costs

### Scaling Up

After successful initial trades:

1. **Gradually Increase Limits**
   - Week 1: $50 max position, $200 exposure
   - Week 2: $100 max position, $500 exposure
   - Week 3: $250 max position, $1000 exposure
   - Month 2+: Scale based on performance

2. **Enable More Strategies**
   - Start with: `yes_no_imbalance`, `cross_market`
   - Add later: `correlated_events`, `multi_leg`

3. **Optimize Settings**
   - Adjust `kelly_fraction` based on results
   - Fine-tune `min_profit_threshold`
   - Optimize `gas_price_limit`

## Monitoring and Maintenance

### Daily Tasks

- Check bot is running (`ps aux | grep python`)
- Review opportunity logs
- Check notification channels
- Monitor wallet balances

### Weekly Tasks

- Review performance report
- Analyze missed opportunities
- Adjust configuration if needed
- Update software dependencies

### Monthly Tasks

- Full performance review
- Strategy effectiveness analysis
- Risk management assessment
- Software updates

## Troubleshooting

### Bot Won't Start

```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "aiohttp|pydantic|loguru"

# Check configuration
python -c "from src.config import load_config; print(load_config())"
```

### No Opportunities Detected

- Verify market data is loading: check logs
- Confirm strategies are enabled in config
- Lower `min_profit_threshold` temporarily
- Check API connectivity

### Notifications Not Working

- Verify webhook/token in .env
- Test notification endpoints manually
- Check firewall/network settings
- Review notification logs

### High Gas Costs

- Increase `gas_price_limit` in config
- Use `order_type: "limit"` instead of market orders
- Batch transactions when possible
- Consider gas-optimized execution paths

## Advanced Configuration

### Multiple Instances

Run multiple bots with different strategies:

```bash
# Instance 1: Conservative
python -m src.main --config config_conservative.yaml

# Instance 2: Aggressive  
python -m src.main --config config_aggressive.yaml
```

### Custom Strategies

Add your own strategies by:
1. Creating new file in `src/arbitrage/strategies/`
2. Implementing detection logic
3. Registering in `detector.py`

### Performance Tuning

Optimize for your use case:
- **Speed**: Enable WebSocket, reduce refresh_interval
- **Profit**: Lower min_profit_threshold, enable all strategies
- **Safety**: Higher Kelly_fraction limits, strict risk management

## Getting Help

- **Documentation**: Check STRATEGIES.md and API.md
- **Logs**: Review `logs/arbitrage_bot.log`
- **Issues**: Open GitHub issue with logs
- **Community**: Discord/Telegram support channels

## Next Steps

After setup:
1. Read [STRATEGIES.md](STRATEGIES.md) to understand each strategy
2. Review [API.md](API.md) for integration details
3. Start bot in alert mode
4. Monitor and optimize
5. Scale gradually

---

**Remember**: Start small, test thoroughly, and never risk more than you can afford to lose.
