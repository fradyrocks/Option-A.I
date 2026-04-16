"""
telegram_bot.py
---------------
Handles all Telegram communication.
Receives commands from users and sends signals.
Like the bot's mouth and ears!
"""

import asyncio
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from loguru import logger

from .signal_formatter import SignalFormatter


class TelegramBot:
    """
    The Telegram interface for the signal bot.
    Handles commands and broadcasts signals.
    """

    def __init__(self, config, fetcher, generator):
        self.config    = config
        self.fetcher   = fetcher
        self.generator = generator
        self.formatter = SignalFormatter()
        self.app       = None
        self._build()

    def _build(self):
        """Set up the Telegram bot with all commands"""
        if not self.config.telegram_token:
            logger.error("❌ No Telegram token found!")
            return

        self.app = (
            Application.builder()
            .token(self.config.telegram_token)
            .build()
        )

        # Register commands
        self.app.add_handler(
            CommandHandler("start",  self._cmd_start)
        )
        self.app.add_handler(
            CommandHandler("signal", self._cmd_signal)
        )
        self.app.add_handler(
            CommandHandler("pairs",  self._cmd_pairs)
        )
        self.app.add_handler(
            CommandHandler("help",   self._cmd_start)
        )
        self.app.add_handler(
            CallbackQueryHandler(self._on_button)
        )

        logger.success("✅ Telegram bot configured")

    def start(self):
        """Start listening for Telegram messages"""
        if not self.app:
            logger.error("Bot not built properly!")
            return

        logger.info("📱 Telegram bot polling started...")
        self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    async def send_signal_to_channel(self, signal: Dict):
        """Send a signal message to the Telegram channel"""
        if not self.app:
            return

        channel = self.config.channel_id
        if not channel:
            logger.warning("No channel ID configured!")
            return

        try:
            msg = self.formatter.signal_message(signal)
            await self.app.bot.send_message(
                chat_id=channel,
                text=msg,
                parse_mode='Markdown'
            )
            logger.success(
                f"📡 Signal sent to channel: "
                f"{signal['pair']} {signal['direction']} "
                f"({signal['confidence']:.1f}%)"
            )
        except Exception as e:
            logger.error(f"Failed to send signal: {e}")

    # ── COMMAND HANDLERS ───────────────────────────────────
    async def _cmd_start(self, update: Update,
                          ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /start and /help"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 Get Signal Now", callback_data="signal"
                ),
                InlineKeyboardButton(
                    "📋 View Pairs", callback_data="pairs"
                )
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            self.formatter.welcome_message(),
            parse_mode='Markdown',
            reply_markup=markup
        )

    async def _cmd_signal(self, update: Update,
                           ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /signal - generate signal on demand"""
        await update.message.reply_text(
            "🔄 *Analyzing markets... please wait*",
            parse_mode='Markdown'
        )

        signal = await self._best_signal()

        if signal:
            msg = self.formatter.signal_message(signal)
            await update.message.reply_text(
                msg, parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "⏳ No high-confidence signal right now.\n"
                "Please wait a moment and try again.\n"
                "The bot automatically sends signals when ready!"
            )

    async def _cmd_pairs(self, update: Update,
                          ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /pairs - list all pairs"""
        otc   = self.config.otc_pairs
        forex = self.config.forex_pairs

        msg  = "📊 *ALL MONITORED PAIRS*\n\n"
        msg += "🏷️ *OTC Pairs (Weekend Trading):*\n"
        for p in otc:
            msg += f"  • `{p}`\n"
        msg += "\n💱 *Forex Pairs:*\n"
        for p in forex:
            msg += f"  • `{p}`\n"
        msg += f"\n🎯 *Min confidence:* {self.config.min_confidence}%"

        await update.message.reply_text(msg, parse_mode='Markdown')

    async def _on_button(self, update: Update,
                          ctx: ContextTypes.DEFAULT_TYPE):
        """Handle button presses"""
        query = update.callback_query
        await query.answer()

        if query.data == "signal":
            await query.message.reply_text(
                "🔄 *Analyzing...*", parse_mode='Markdown'
            )
            signal = await self._best_signal()
            if signal:
                msg = self.formatter.signal_message(signal)
                await query.message.reply_text(
                    msg, parse_mode='Markdown'
                )
            else:
                await query.message.reply_text(
                    "⏳ No strong signal right now. Try again soon!"
                )

        elif query.data == "pairs":
            otc = "\n".join(
                f"  • `{p}`" for p in self.config.otc_pairs
            )
            await query.message.reply_text(
                f"📊 *OTC Pairs:*\n{otc}",
                parse_mode='Markdown'
            )

    async def _best_signal(self):
        """Find the best signal from all pairs"""
        pairs    = self.config.otc_pairs + self.config.forex_pairs
        best     = None
        best_conf = 0

        for pair in pairs[:6]:  # Check first 6 pairs only
            for tf in ['5m', '1m']:
                try:
                    df = self.fetcher.get_candles(pair, tf)
                    s  = self.generator.generate_signal(
                        pair, tf, df
                    )
                    if s and s['confidence'] > best_conf:
                        best_conf = s['confidence']
                        best      = s
                except Exception:
                    continue

        return best
