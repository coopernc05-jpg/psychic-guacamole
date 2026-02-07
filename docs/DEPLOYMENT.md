# Deployment Guide

Complete guide for deploying the Polymarket Arbitrage Bot in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [VPS Deployment](#vps-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Security Best Practices](#security-best-practices)
7. [Monitoring & Maintenance](#monitoring--maintenance)

## Local Development

### Prerequisites
- Python 3.11 or 3.12
- pip package manager
- Git

### Setup Steps

1. **Clone the repository:**
```bash
git clone https://github.com/coopernc05-jpg/psychic-guacamole.git
cd psychic-guacamole
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. **Run the bot:**
```bash
python -m src.main
```

6. **Access dashboard:**
Open http://localhost:5000 in your browser

## Docker Deployment

### Quick Start

1. **Build the Docker image:**
```bash
docker build -t polymarket-bot .
```

2. **Run with Docker Compose:**
```bash
docker-compose up -d
```

3. **View logs:**
```bash
docker-compose logs -f bot
```

4. **Stop the bot:**
```bash
docker-compose down
```

### Configuration

Edit `docker-compose.yml` to customize:
- Port mappings
- Volume mounts
- Environment variables
- Resource limits

### Persistent Data

Data is stored in Docker volumes:
- `./logs` - Log files
- `./data` - Analytics data

## VPS Deployment

### DigitalOcean Droplet

1. **Create Droplet:**
   - Ubuntu 22.04 LTS
   - Minimum 2GB RAM
   - 1 vCPU

2. **SSH into server:**
```bash
ssh root@your-server-ip
```

3. **Install Docker:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

4. **Install Docker Compose:**
```bash
apt install docker-compose
```

5. **Clone and deploy:**
```bash
git clone https://github.com/coopernc05-jpg/psychic-guacamole.git
cd psychic-guacamole
cp .env.example .env
# Edit .env with production settings
docker-compose up -d
```

6. **Setup firewall:**
```bash
ufw allow 22/tcp      # SSH
ufw allow 5000/tcp    # Dashboard
ufw enable
```

### AWS EC2

1. **Launch EC2 Instance:**
   - Amazon Linux 2023 or Ubuntu 22.04
   - t3.medium (2 vCPU, 4GB RAM recommended)
   - Configure security group to allow port 5000

2. **Connect and install Docker:**
```bash
# For Amazon Linux
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# For Ubuntu
sudo apt update
sudo apt install docker.io docker-compose -y
```

3. **Deploy application:**
```bash
git clone https://github.com/coopernc05-jpg/psychic-guacamole.git
cd psychic-guacamole
sudo docker-compose up -d
```

### Systemd Service (Non-Docker)

Create `/etc/systemd/system/polymarket-bot.service`:

```ini
[Unit]
Description=Polymarket Arbitrage Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/psychic-guacamole
Environment="PATH=/home/botuser/psychic-guacamole/venv/bin"
ExecStart=/home/botuser/psychic-guacamole/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable polymarket-bot
sudo systemctl start polymarket-bot
sudo systemctl status polymarket-bot
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker image pushed to registry

### Deployment Steps

1. **Create namespace:**
```bash
kubectl create namespace polymarket-bot
```

2. **Create secret for environment variables:**
```bash
kubectl create secret generic bot-secrets \
  --from-literal=POLYMARKET_API_KEY=your_key \
  --from-literal=PRIVATE_KEY=your_private_key \
  -n polymarket-bot
```

3. **Create deployment manifest** (`k8s/deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: polymarket-bot
  namespace: polymarket-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: polymarket-bot
  template:
    metadata:
      labels:
        app: polymarket-bot
    spec:
      containers:
      - name: bot
        image: ghcr.io/coopernc05-jpg/psychic-guacamole:latest
        ports:
        - containerPort: 5000
        env:
        - name: POLYMARKET_API_KEY
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: POLYMARKET_API_KEY
        - name: PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: PRIVATE_KEY
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: bot-logs-pvc
      - name: data
        persistentVolumeClaim:
          claimName: bot-data-pvc
```

4. **Create service** (`k8s/service.yaml`):
```yaml
apiVersion: v1
kind: Service
metadata:
  name: polymarket-bot-service
  namespace: polymarket-bot
spec:
  selector:
    app: polymarket-bot
  ports:
  - port: 5000
    targetPort: 5000
  type: LoadBalancer
```

5. **Deploy:**
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

6. **Check status:**
```bash
kubectl get pods -n polymarket-bot
kubectl logs -f deployment/polymarket-bot -n polymarket-bot
```

## Environment Configuration

### Required Variables

```bash
# Polymarket API (if using real API)
POLYMARKET_API_KEY=your_api_key
POLYMARKET_SECRET=your_secret
POLYMARKET_PASSPHRASE=your_passphrase

# Wallet
PRIVATE_KEY=your_wallet_private_key

# Notifications
DISCORD_WEBHOOK_URL=your_discord_webhook
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Optional Variables

```bash
# Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:pass@localhost:5432/polymarket_bot
```

## Security Best Practices

### 1. API Keys & Secrets

- **Never commit secrets to Git**
- Use environment variables or secret management services
- Rotate keys regularly
- Use separate keys for dev/prod

### 2. Network Security

- **Restrict dashboard access:**
  - Use firewall rules
  - Consider VPN or SSH tunnel for dashboard access
  - Add authentication (implement in production)

- **HTTPS for production:**
  - Use reverse proxy (nginx/Caddy) with SSL
  - Configure Let's Encrypt for free certificates

### 3. Wallet Security

- **Never share private keys**
- Use hardware wallet for large amounts
- Test with small amounts first
- Keep backup of keys in secure location

### 4. Docker Security

- Run as non-root user (already configured)
- Scan images for vulnerabilities
- Use minimal base images
- Keep images updated

### 5. Log Security

- **Don't log sensitive data:**
  - No private keys
  - No API secrets
  - Sanitize user inputs

- **Secure log files:**
  - Restrict file permissions
  - Rotate logs regularly
  - Consider encrypted storage

## Monitoring & Maintenance

### Health Checks

Dashboard health endpoint: `http://localhost:5000/api/health`

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-02-07T23:00:00Z",
  "uptime_seconds": 3600,
  "api_status": {
    "healthy": true,
    "last_check": "2024-02-07T22:59:00Z"
  }
}
```

### Prometheus Metrics

Add to dashboard to export metrics:
```python
from src.utils.metrics import metrics_exporter

# Add route in dashboard
@app.route('/metrics')
def metrics():
    return metrics_exporter.export_metrics(), 200, {'Content-Type': metrics_exporter.get_content_type()}
```

### Log Monitoring

View real-time logs:
```bash
# Docker
docker-compose logs -f bot

# Systemd
journalctl -u polymarket-bot -f

# Kubernetes
kubectl logs -f deployment/polymarket-bot -n polymarket-bot
```

### Backup Strategy

1. **Configuration:** Backup `.env` and `config.yaml`
2. **Data:** Backup `./data` and `./logs` directories
3. **Database:** If using PostgreSQL, backup database

### Update Procedure

1. **Pull latest code:**
```bash
git pull origin main
```

2. **Rebuild Docker image:**
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

3. **Verify deployment:**
```bash
docker-compose logs bot
curl http://localhost:5000/api/health
```

## Troubleshooting

### Common Issues

**Bot won't start:**
- Check environment variables
- Verify API keys
- Review logs for errors

**Dashboard not accessible:**
- Check firewall rules
- Verify port is not in use
- Check Docker port mapping

**No opportunities detected:**
- Verify API connectivity
- Check market data is updating
- Review strategy configurations

### Support Resources

- GitHub Issues: Report bugs and request features
- Documentation: Review all docs in `docs/` directory
- Logs: Check `logs/` directory for detailed error messages

## Production Checklist

Before deploying to production:

- [ ] All API keys configured correctly
- [ ] Wallet funded with test amount
- [ ] Dashboard accessible and showing data
- [ ] Notifications working (Discord/Telegram)
- [ ] Logs being written correctly
- [ ] Health checks passing
- [ ] Firewall configured
- [ ] SSL/HTTPS enabled for dashboard
- [ ] Backups configured
- [ ] Monitoring alerts set up
- [ ] Tested in alert mode first
- [ ] Small position sizes configured
- [ ] Stop-loss limits set appropriately

---

**Remember:** Start with alert mode, test thoroughly, and scale gradually. Never risk more than you can afford to lose.
