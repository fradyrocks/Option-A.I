#!/usr/bin/env python3
"""
POCKET OPTION AI SIGNAL BOT
Main entry point - this file starts everything
"""

import asyncio
import schedule
import time
import threading
import os
import sys
from datetime import datetime
from loguru import logger
import pytz

# Setup logging first
os.makedirs("logs", exist_ok=True)
os.makedirs("models/trained_models", exist_ok=True)
os.makedirs("data", exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO",
    colorize=True
)
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)

# Import all modules
from src.utils.config import Config
from src.data.data_fetcher import DataFetcher
from src.intelligence.signal_generator import SignalGenerator
from src.bot.telegram_bot import TelegramBot

# ── GLOBAL OBJECTS ─────────────────────────────────────────
config    = Config()
fetcher   = DataFetcher()
generator = SignalGenerator(config)
bot       = TelegramBot(config, fetcher, generator)

# ── HOW OFTEN TO SCAN ──────────────────────────────────────
SCAN_INTERVAL_SECONDS = 60   # scan every 60 seconds
MAX_SIGNALS_PER_SCAN  = 2    # send max 2 signals per scan

def run_signal_scan():
    """
    This function runs every minute.
    It checks all currency pairs and sends
    signals when confidence is high enough.
    """
    logger.info("🔍 Scanning all currency pairs...")

    all_pairs    = config.otc_pairs + config.forex_pairs
    signals_sent = 0

    for pair in all_pairs:
        if signals_sent >= MAX_SIGNALS_PER_SCAN:
            break

        for timeframe in ['1m', '5m']:
            try:
                # Get price data
                df = fetcher.get_candles(pair, timeframe)

                if df is None or len(df) < 30:
                    continue

                # Analyze and generate signal
                signal = generator.generate_signal(pair, timeframe, df)

                # Only send if confidence is high enough
                if signal and signal['confidence'] >= config.min_confidence:
                    logger.success(
                        f"📡 {pair} | {timeframe} | "
                        f"{signal['direction']} | "
                        f"{signal['confidence']:.1f}%"
                    )

                    # Send to Telegram
                    asyncio.run(bot.send_signal_to_channel(signal))
                    signals_sent += 1

                    if signals_sent >= MAX_SIGNALS_PER_SCAN:
                        break

            except Exception as e:
                logger.error(f"Error with {pair}/{timeframe}: {e}")
                continue

    if signals_sent == 0:
        logger.info("💤 No qualifying signals this round")
    else:
        logger.success(f"✅ Sent {signals_sent} signal(s) this round")


def scanner_thread_function():
    """
    Runs in the background.
    Like a clock that ticks every minute
    and triggers a market scan.
    """
    logger.info("⏰ Signal scanner started")

    # Run once immediately on startup
    run_signal_scan()

    # Then run every 60 seconds
    schedule.every(SCAN_INTERVAL_SECONDS).seconds.do(run_signal_scan)

    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    """
    This is where everything starts.
    Think of it as turning the key in the ignition.
    """
    logger.info("=" * 55)
    logger.info("  🤖 POCKET OPTION AI SIGNAL BOT")
    logger.info("  Version 3.0 | Powered by AI + ML")
    logger.info("=" * 55)
    logger.info(
        f"🕐 Started: "
        f"{datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    logger.info(f"📊 OTC Pairs:   {len(config.otc_pairs)}")
    logger.info(f"💱 Forex Pairs: {len(config.forex_pairs)}")
    logger.info(f"🎯 Min Confidence: {config.min_confidence}%")
    logger.info("=" * 55)

    # Start the background scanner
    scanner = threading.Thread(
        target=scanner_thread_function,
        daemon=True,
        name="SignalScanner"
    )
    scanner.start()
    logger.info("✅ Background scanner is running")

    # Start the Telegram bot (this runs forever)
    logger.info("✅ Starting Telegram bot...")
    logger.info("🟢 BOT IS NOW LIVE!")
    bot.start()


if __name__ == "__main__":
    main()
