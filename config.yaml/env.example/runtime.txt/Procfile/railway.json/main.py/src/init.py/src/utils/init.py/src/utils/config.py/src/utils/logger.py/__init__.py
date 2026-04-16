"""
logger.py
---------
Sets up logging so you can see what
the bot is doing at all times.
"""

import os
import sys
from loguru import logger


def setup_logger(level: str = "INFO"):
    """Configure the application logger"""

    os.makedirs("logs", exist_ok=True)

    logger.remove()  # Remove default handler

    # Console output (what you see on Railway logs)
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True
    )

    # File output (saved to disk)
    logger.add(
        "logs/bot.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )

    logger.info("📝 Logger initialized")
    return logger
