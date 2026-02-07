"""Centralized logging configuration."""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    rotation: str = "100 MB",
    retention: str = "30 days",
    enable_console: bool = True,
):
    """Configure centralized logging for the bot.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        rotation: When to rotate log files
        retention: How long to keep old log files
        enable_console: Whether to log to console
    """
    # Remove default handler
    logger.remove()

    # Add console handler if enabled
    if enable_console:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Add file handler for all logs
    logger.add(
        log_path / "bot_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression="zip",
    )

    # Add separate error log
    logger.add(
        log_path / "errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=rotation,
        retention=retention,
        compression="zip",
    )

    logger.info(f"Logging initialized at level {log_level}")
    logger.info(f"Log files stored in: {log_path.absolute()}")


def configure_module_logging():
    """Configure per-module log levels."""
    # Reduce noise from verbose libraries
    logger.disable("aiohttp")
    logger.disable("websockets")

    # Can enable specific modules for debugging
    # logger.enable("src.market.polymarket_api")
    # logger.enable("src.arbitrage.detector")
