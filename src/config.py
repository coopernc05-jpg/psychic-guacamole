"""Configuration management for Polymarket Arbitrage Bot."""

import os
from pathlib import Path
from typing import List, Optional, Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Main configuration class for the arbitrage bot."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Profit Maximization Settings
    min_profit_threshold: float = Field(default=5.0, description="Minimum net profit in USD")
    position_sizing_strategy: Literal["kelly", "fixed", "percentage"] = "kelly"
    kelly_fraction: float = Field(default=0.25, ge=0.0, le=1.0)
    max_position_size: float = Field(default=1000.0, description="Max USD per trade")
    max_total_exposure: float = Field(default=5000.0, description="Max total USD at risk")
    
    # Arbitrage Detection
    strategies: List[str] = Field(
        default=["cross_market", "yes_no_imbalance", "multi_leg", "correlated_events"]
    )
    min_arbitrage_percentage: float = Field(default=0.5, description="Minimum profit margin %")
    
    # Market Monitoring
    websocket_enabled: bool = True
    markets_to_monitor: str | List[str] = "all"
    refresh_interval: int = Field(default=1, ge=1)
    max_markets: int = Field(default=100, ge=1)
    
    # Risk Management
    max_slippage: float = Field(default=0.02, ge=0.0, le=1.0)
    safety_margin: float = Field(default=1.5, ge=1.0)
    stop_loss_percentage: float = Field(default=0.05, ge=0.0, le=1.0)
    max_position_age_hours: int = Field(default=24, ge=1)
    
    # Execution
    mode: Literal["alert", "auto_trade"] = "alert"
    gas_price_limit: int = Field(default=100, description="Maximum gwei for gas")
    order_type: Literal["market", "limit"] = "limit"
    execution_timeout: int = Field(default=30, ge=1)
    
    # Gas & Fee Settings
    polygon_rpc_url: str = "https://polygon-rpc.com"
    gas_safety_buffer: float = Field(default=1.2, ge=1.0)
    
    # Notifications
    discord_webhook: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    alert_on_opportunities: bool = True
    alert_on_executions: bool = True
    alert_on_errors: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/arbitrage_bot.log"
    log_rotation: str = "100 MB"
    
    # API Settings
    polymarket_api_url: str = "https://clob.polymarket.com"
    polymarket_ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws"
    polymarket_api_key: Optional[str] = None
    polymarket_secret: Optional[str] = None
    api_timeout: int = Field(default=10, ge=1)
    api_retry_attempts: int = Field(default=3, ge=1)
    
    # Wallet Configuration
    wallet_private_key: Optional[str] = None
    wallet_address: Optional[str] = None
    
    # Initial Capital
    initial_capital: float = Field(default=10000.0, gt=0)
    
    # Performance Tracking
    enable_analytics: bool = True
    analytics_db_path: str = "data/analytics.db"
    track_missed_opportunities: bool = True
    
    # Advanced Settings
    debug: bool = False
    dry_run: bool = True


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file and environment variables.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Config object with loaded settings
    """
    config_file = Path(config_path)
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            yaml_config = yaml.safe_load(f)
    else:
        yaml_config = {}
    
    # Environment variables override YAML config
    return Config(**yaml_config)


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = load_config()
    return config
