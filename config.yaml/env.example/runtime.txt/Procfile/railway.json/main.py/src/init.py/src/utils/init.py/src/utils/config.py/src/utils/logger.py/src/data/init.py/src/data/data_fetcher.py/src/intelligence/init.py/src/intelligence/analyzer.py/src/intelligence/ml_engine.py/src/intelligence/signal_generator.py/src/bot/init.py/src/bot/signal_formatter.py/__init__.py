"""
signal_formatter.py
-------------------
Makes signals look beautiful in Telegram.
Like a graphic designer for your messages!
"""

from datetime import datetime
from typing import Dict
import pytz


class SignalFormatter:
    """Formats signals into pretty Telegram messages"""

    def signal_message(self, signal: Dict) -> str:
        """Create the main signal message"""

        direction = signal['direction']
        pair      = signal['pair']
        tf        = signal['timeframe']
        conf      = signal['confidence']
        price     = signal['price']
        expiry    = signal['expiry']
        risk      = signal['risk']
        market    = signal['market']
        now       = signal['timestamp']

        # Direction visuals
        if direction == "CALL":
            dir_line = "🟢 ▲  C A L L  (BUY UP)"
            dir_bg   = "🟩🟩🟩🟩🟩"
        else:
            dir_line = "🔴 ▼  P U T  (SELL DOWN)"
            dir_bg   = "🟥🟥🟥🟥🟥"

        # Confidence bar
        bar  = self._conf_bar(conf)
        stars = self._stars(conf)

        # Get analysis data
        analyses = signal.get('analyses', {})
        patterns = analyses.get('patterns', {}).get('patterns', [])
        trend_s  = analyses.get('trend',    {}).get('signals', [])
        mom_s    = analyses.get('momentum', {}).get('signals', [])
        ml       = analyses.get('ml',       {})
        votes    = signal.get('votes', {})

        # Time
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%d %b %Y")

        # ── BUILD THE MESSAGE ──────────────────────────────
        msg  = "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🤖  *AI SIGNAL BOT PRO*  🤖\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        msg += f"{dir_bg}\n"
        msg += f"*{dir_line}*\n"
        msg += f"{dir_bg}\n\n"

        msg += f"📊 *Asset:* `{pair}`\n"
        msg += f"🏷️ *Type:* {market}\n"
        msg += f"⏰ *Chart:* {tf} candles\n"
        msg += f"💰 *Entry:* `{price:.5f}`\n"
        msg += f"{expiry}\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📈 *AI CONFIDENCE SCORE*\n"
        msg += f"`{bar}`\n"
        msg += f"🎯 *{conf:.1f}%* confidence {stars}\n"
        msg += f"{risk}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        # Patterns found
        if patterns:
            msg += "🕯️ *PATTERNS DETECTED:*\n"
            for p in patterns[:3]:
                msg += f"  ✦ {p['name']}\n"
            msg += "\n"

        # Trend signals
        if trend_s:
            msg += "📉 *TREND ANALYSIS:*\n"
            for s in trend_s[:2]:
                msg += f"  • {s}\n"
            msg += "\n"

        # Momentum signals
        if mom_s:
            msg += "⚡ *MOMENTUM:*\n"
            for s in mom_s[:2]:
                msg += f"  • {s}\n"
            msg += "\n"

        # ML Report
        if ml.get('ml_active'):
            prob  = ml.get('probability', 0.5)
            mvotes = ml.get('model_votes', {})
            msg += "🤖 *AI MODEL VOTES:*\n"
            msg += f"  🌲 Random Forest:  {mvotes.get('random_forest', '?')}\n"
            msg += f"  ⚡ XGBoost:        {mvotes.get('xgboost', '?')}\n"
            msg += f"  📈 Gradient Boost: {mvotes.get('gradient_boost', '?')}\n"
            msg += f"  📊 Probability:    `{prob:.1%}`\n\n"

        # Vote summary
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🗳️ *INDICATOR VOTES:*\n"
        msg += f"  🟢 CALL score: {votes.get('call', 0):.0f}\n"
        msg += f"  🔴 PUT  score: {votes.get('put', 0):.0f}\n\n"

        msg += f"📅 {date_str}  🕐 {time_str} UTC\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "⚠️ _Trade responsibly. Not financial advice._"

        return msg

    def welcome_message(self) -> str:
        return (
            "🤖 *AI SIGNAL BOT PRO*\n\n"
            "Welcome! I analyze markets using:\n"
            "• 15+ Technical Indicators\n"
            "• 15+ Candlestick Patterns\n"
            "• 3 AI/ML Models\n"
            "• OTC + Forex Coverage\n\n"
            "📡 *I will send signals automatically!*\n\n"
            "Commands:\n"
            "/signal - Get a signal now\n"
            "/pairs  - See all pairs\n"
            "/help   - Show this message\n\n"
            "🟢 *Bot is ACTIVE and monitoring!*"
        )

    def _conf_bar(self, conf: float) -> str:
        filled = int(conf / 10)
        empty  = 10 - filled
        fill   = "█" if conf >= 80 else ("▓" if conf >= 70 else "░")
        return fill * filled + "░" * empty + f" {conf:.0f}%"

    def _stars(self, conf: float) -> str:
        if conf >= 92:
            return "⭐⭐⭐⭐⭐"
        elif conf >= 85:
            return "⭐⭐⭐⭐"
        elif conf >= 78:
            return "⭐⭐⭐"
        elif conf >= 70:
            return "⭐⭐"
        else:
            return "⭐"
