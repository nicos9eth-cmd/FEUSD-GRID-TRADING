#!/usr/bin/env python3
"""Entry point for FEUSD Grid Trading Bot."""
import asyncio
import logging
import signal
import sys

from src.bot import bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    bot.stop()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        bot.stop()
