# Dashboard Guide

Complete guide to using the Polymarket Arbitrage Bot's web dashboard.

## Overview

The dashboard provides real-time monitoring and visualization of bot performance, opportunities, and trades through a modern web interface.

## Accessing the Dashboard

### Local Development
```
http://localhost:5000
```

### Docker Deployment
```
http://localhost:5000
```

### VPS/Cloud Deployment
```
http://your-server-ip:5000
```

**Security Note:** In production, use a reverse proxy with SSL and add authentication.

## Dashboard Features

### 1. Key Metrics Cards

Four main performance indicators displayed at the top:

#### Total P&L
- **What it shows:** Net profit/loss after all costs (gas fees, trading fees)
- **Color coding:** 
  - Green: Profitable ($X.XX)
  - Red: Loss (-$X.XX)

#### ROI (Return on Investment)
- **What it shows:** Percentage return on initial capital
- **Calculation:** `(Net P&L / Initial Capital) × 100`
- **Example:** $50 profit on $1000 capital = 5.00% ROI

#### Win Rate
- **What it shows:** Percentage of profitable trades
- **Calculation:** `(Winning Trades / Total Trades) × 100`
- **Subtitle:** Shows total number of trades executed

#### Sharpe Ratio
- **What it shows:** Risk-adjusted returns
- **Interpretation:**
  - < 0: Negative returns
  - 0-1: Subpar returns
  - 1-2: Good returns
  - 2+: Excellent returns

### 2. Equity Curve Chart

**Purpose:** Visualize portfolio value over time

**Features:**
- Line chart showing capital growth/decline
- X-axis: Time
- Y-axis: Portfolio value in USD
- Smooth curve with area fill
- Updates every 30 seconds

**How to interpret:**
- Upward trend = Profitable
- Downward trend = Losing
- Volatility = Risk level

### 3. Opportunities by Type

**Purpose:** Show distribution of detected arbitrage opportunities

**Chart type:** Doughnut chart

**Strategy types:**
- **CrossMarketArbitrage** - Same event, different markets
- **YesNoImbalanceArbitrage** - YES + NO ≠ 1.00
- **MultiLegArbitrage** - Complex 3+ market chains
- **CorrelatedEventArbitrage** - Related event mispricings

**Colors:**
- Purple (#667eea) - Cross-market
- Dark purple (#764ba2) - Multi-leg
- Orange (#f59e0b) - YES/NO imbalance
- Green (#10b981) - Correlated events

### 4. Win/Loss Distribution

**Purpose:** Visualize trade performance

**Chart type:** Pie chart

**Segments:**
- Green: Winning trades
- Red: Losing trades

**Insights:**
- Balanced chart = Consistent performance
- Mostly green = Strong strategy
- Mostly red = Need to adjust parameters

### 5. Activity Feed

**Purpose:** Real-time log of opportunities and trades

**Item types:**

#### Opportunity Items (Orange)
```
⚠️ OPPORTUNITY
YesNoImbalanceArbitrage
Score: 85.32 • Profit Score: 78.45
2024-02-07 15:30:45
```

**What it means:**
- New arbitrage opportunity detected
- Score indicates quality (0-100)
- Higher score = better opportunity

#### Trade Items (Green)
```
✓ TRADE
BUY YES
Price: $0.55 • Size: 100.00 • Market: abc123
2024-02-07 15:31:02
```

**What it means:**
- Trade was executed
- Shows price, size, and market
- Timestamp shows execution time

**Features:**
- Auto-scrolls to show newest items
- Keeps last 50 items
- Real-time updates via WebSocket

## Real-Time Updates

The dashboard uses WebSocket connections for instant updates:

### Auto-refresh Intervals
- **Metrics cards:** Every 10 seconds
- **Equity curve:** Every 30 seconds
- **Activity feed:** Real-time (instant)

### Connection Status
- **Green pulsing dot:** Connected and updating
- **Gray dot:** Disconnected (check network/server)

## API Endpoints

The dashboard exposes these REST APIs:

### GET /api/metrics
Returns current performance metrics
```json
{
  "metrics": {
    "total_pnl": 125.50,
    "roi": 12.55,
    "win_rate": 65.00,
    "sharpe_ratio": 1.85,
    "total_trades": 23
  },
  "capital": {
    "initial": 1000.00,
    "current": 1125.50
  }
}
```

### GET /api/opportunities
Returns opportunity statistics
```json
{
  "statistics": {
    "total_opportunities": 156,
    "by_type": {
      "YesNoImbalanceArbitrage": 89,
      "CrossMarketArbitrage": 45,
      "MultiLegArbitrage": 12,
      "CorrelatedEventArbitrage": 10
    },
    "avg_score": 72.3
  },
  "recent": [...]
}
```

### GET /api/trades
Returns trade statistics
```json
{
  "trade_statistics": {
    "total_trades": 23,
    "total_volume": 2300.00,
    "total_gas_costs": 12.50
  },
  "position_statistics": {
    "total_positions": 20,
    "winning_positions": 13,
    "losing_positions": 7,
    "win_rate": 65.00
  },
  "recent_trades": [...]
}
```

### GET /api/equity-curve
Returns equity curve data for charting
```json
[
  {
    "timestamp": "2024-02-07T15:00:00Z",
    "value": 1000.00
  },
  {
    "timestamp": "2024-02-07T16:00:00Z",
    "value": 1025.50
  }
]
```

### GET /api/health
Returns system health status
```json
{
  "status": "healthy",
  "timestamp": "2024-02-07T15:30:00Z",
  "uptime_seconds": 3600,
  "api_status": {
    "healthy": true,
    "last_check": "2024-02-07T15:29:00Z"
  }
}
```

## Configuration UI (Future Enhancement)

Currently, configuration is managed via `config.yaml`. A configuration UI is planned for future releases.

**Planned features:**
- Edit risk parameters
- Enable/disable strategies
- Adjust profit thresholds
- Toggle notification settings

## Integrating Dashboard in Bot

The dashboard runs alongside the bot. Here's how to enable it:

```python
from src.analytics.dashboard import create_dashboard
from src.analytics.performance import PerformanceTracker
from src.analytics.logger import OpportunityLogger, ExecutionLogger

# Create components
performance_tracker = PerformanceTracker(initial_capital=1000)
opportunity_logger = OpportunityLogger()
execution_logger = ExecutionLogger()

# Create dashboard
dashboard = create_dashboard(
    performance_tracker=performance_tracker,
    opportunity_logger=opportunity_logger,
    execution_logger=execution_logger,
    host="0.0.0.0",
    port=5000,
    debug=False
)

# Run in background thread
dashboard.run_in_thread()

# Or run in main thread (blocking)
# dashboard.run()
```

## Performance Considerations

### Resource Usage
- **CPU:** Minimal (<5%)
- **Memory:** ~50-100 MB
- **Network:** WebSocket connections use minimal bandwidth

### Scaling
- Dashboard can handle 10+ concurrent viewers
- For more users, consider:
  - Increase server resources
  - Use load balancer
  - Cache API responses

## Security Recommendations

### Production Deployment

1. **Use HTTPS**
```nginx
server {
    listen 443 ssl;
    server_name bot.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

2. **Add Authentication**
```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Check credentials
    return username == "admin" and password == "secure_password"

@app.route('/')
@auth.login_required
def index():
    return render_template('dashboard.html')
```

3. **Firewall Rules**
```bash
# Only allow from specific IPs
ufw allow from YOUR_IP to any port 5000

# Or use VPN for access
```

4. **Rate Limiting**
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)
```

## Troubleshooting

### Dashboard won't load
1. Check bot is running: `ps aux | grep python`
2. Check port is open: `netstat -an | grep 5000`
3. Check firewall: `ufw status`
4. Check logs: `tail -f logs/bot_*.log`

### No data showing
1. Verify bot has detected opportunities
2. Check opportunity/execution logs in `data/` directory
3. Refresh browser (Ctrl+F5)
4. Check browser console for errors

### WebSocket not connecting
1. Check browser supports WebSockets
2. Verify no proxy blocking WebSocket
3. Check CORS settings
4. Inspect network tab in browser dev tools

### Charts not rendering
1. Verify Chart.js CDN is accessible
2. Check browser console for JavaScript errors
3. Try different browser
4. Clear browser cache

## Mobile Access

The dashboard is responsive and works on mobile devices:

- **Phone:** Vertical layout, scrollable
- **Tablet:** Optimized grid layout
- **Desktop:** Full feature display

**Tip:** Add to home screen on iOS/Android for app-like experience.

## Browser Compatibility

Tested and supported:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Future Enhancements

Planned features:
- [ ] Historical performance comparison
- [ ] Custom date range selection
- [ ] Export data to CSV/JSON
- [ ] Alert configuration UI
- [ ] Strategy performance breakdown
- [ ] Market heat map
- [ ] Trade execution history table
- [ ] Real-time position monitor
- [ ] Risk metrics dashboard
- [ ] Backtesting interface

## Tips & Best Practices

1. **Keep dashboard open** during bot operation for monitoring
2. **Check health endpoint** regularly for system status
3. **Monitor win rate** - should be >50% for profitable bot
4. **Watch equity curve** - should trend upward over time
5. **Review activity feed** - understand what opportunities are being detected
6. **Set alerts** - configure Discord/Telegram for critical events
7. **Regular backups** - export data periodically

## Support

For dashboard issues:
- Check logs in `logs/` directory
- Review GitHub issues
- Consult main README.md

---

**Remember:** The dashboard is for monitoring only. All bot configuration and control happens through `config.yaml` and command line.
