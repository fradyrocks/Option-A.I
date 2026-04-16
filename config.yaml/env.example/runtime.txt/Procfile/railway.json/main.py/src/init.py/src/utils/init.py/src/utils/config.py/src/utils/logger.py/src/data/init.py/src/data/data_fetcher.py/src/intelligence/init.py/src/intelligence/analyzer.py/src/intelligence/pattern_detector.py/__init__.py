"""
pattern_detector.py
-------------------
Finds candlestick patterns in price charts.
Like recognizing shapes - a hammer means 
price is likely going UP, etc.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from loguru import logger


class PatternDetector:
    """
    Detects 15+ candlestick patterns automatically.
    Each pattern gives a CALL or PUT signal.
    """

    def detect_all_patterns(self, df: pd.DataFrame) -> Dict:
        """Run all pattern checks on the latest candles"""

        if len(df) < 3:
            return {
                "patterns":      [],
                "score":         0,
                "direction":     "NEUTRAL",
                "confidence":    0,
                "pattern_count": 0
            }

        last  = df.iloc[-1]
        prev  = df.iloc[-2]
        prev2 = df.iloc[-3]

        all_patterns = []
        total_score  = 0

        # ── SINGLE CANDLE PATTERNS ─────────────────────────
        checks = [
            self._hammer(last),
            self._shooting_star(last),
            self._doji(last),
            self._marubozu(last),
        ]

        # ── TWO CANDLE PATTERNS ────────────────────────────
        checks += [
            self._engulfing(last, prev),
            self._harami(last, prev),
            self._piercing_line(last, prev),
            self._dark_cloud(last, prev),
            self._tweezer(last, prev),
        ]

        # ── THREE CANDLE PATTERNS ──────────────────────────
        checks += [
            self._morning_star(last, prev, prev2),
            self._evening_star(last, prev, prev2),
            self._three_soldiers(last, prev, prev2),
            self._three_crows(last, prev, prev2),
        ]

        for result in checks:
            if result is not None:
                all_patterns.append(result)
                total_score += result.get('score', 0)

        direction = (
            "CALL" if total_score > 0
            else "PUT" if total_score < 0
            else "NEUTRAL"
        )

        return {
            "patterns":      all_patterns,
            "score":         total_score,
            "direction":     direction,
            "confidence":    min(abs(total_score), 100),
            "pattern_count": len(all_patterns)
        }

    # ── HELPER FUNCTIONS ───────────────────────────────────
    def _body(self, c) -> float:
        return abs(c['close'] - c['open'])

    def _range(self, c) -> float:
        return c['high'] - c['low']

    def _upper_wick(self, c) -> float:
        return c['high'] - max(c['open'], c['close'])

    def _lower_wick(self, c) -> float:
        return min(c['open'], c['close']) - c['low']

    def _bullish(self, c) -> bool:
        return c['close'] > c['open']

    def _bearish(self, c) -> bool:
        return c['close'] < c['open']

    # ── SINGLE CANDLE PATTERNS ─────────────────────────────
    def _doji(self, c) -> Optional[Dict]:
        body = self._body(c)
        rng  = self._range(c)
        if rng > 0 and body / rng < 0.08:
            return {
                "name":        "⚖️ Doji",
                "type":        "NEUTRAL",
                "score":       0,
                "description": "Market undecided - watch next candle"
            }
        return None

    def _hammer(self, c) -> Optional[Dict]:
        body = self._body(c)
        lw   = self._lower_wick(c)
        uw   = self._upper_wick(c)
        rng  = self._range(c)

        if rng == 0 or body == 0:
            return None

        if lw >= 2 * body and uw <= 0.3 * body:
            return {
                "name":        "🔨 Hammer",
                "type":        "BULLISH",
                "score":       28,
                "description": "Strong CALL signal - buyers pushing back!"
            }
        return None

    def _shooting_star(self, c) -> Optional[Dict]:
        body = self._body(c)
        uw   = self._upper_wick(c)
        lw   = self._lower_wick(c)
        rng  = self._range(c)

        if rng == 0 or body == 0:
            return None

        if uw >= 2 * body and lw <= 0.3 * body:
            return {
                "name":        "⭐ Shooting Star",
                "type":        "BEARISH",
                "score":       -28,
                "description": "Strong PUT signal - sellers taking over!"
            }
        return None

    def _marubozu(self, c) -> Optional[Dict]:
        body = self._body(c)
        rng  = self._range(c)

        if rng == 0:
            return None

        if body / rng > 0.92:
            if self._bullish(c):
                return {
                    "name":        "🟢 Bullish Marubozu",
                    "type":        "BULLISH",
                    "score":       32,
                    "description": "Full bull candle - strong CALL!"
                }
            else:
                return {
                    "name":        "🔴 Bearish Marubozu",
                    "type":        "BEARISH",
                    "score":       -32,
                    "description": "Full bear candle - strong PUT!"
                }
        return None

    # ── TWO CANDLE PATTERNS ────────────────────────────────
    def _engulfing(self, last, prev) -> Optional[Dict]:
        last_body = self._body(last)
        prev_body = self._body(prev)

        # Bullish Engulfing
        if (self._bearish(prev) and self._bullish(last) and
                last['open'] < prev['close'] and
                last['close'] > prev['open'] and
                last_body > prev_body):
            return {
                "name":        "🌅 Bullish Engulfing",
                "type":        "BULLISH",
                "score":       38,
                "description": "STRONG CALL - bulls swallowed the bears!"
            }

        # Bearish Engulfing
        if (self._bullish(prev) and self._bearish(last) and
                last['open'] > prev['close'] and
                last['close'] < prev['open'] and
                last_body > prev_body):
            return {
                "name":        "🌆 Bearish Engulfing",
                "type":        "BEARISH",
                "score":       -38,
                "description": "STRONG PUT - bears swallowed the bulls!"
            }

        return None

    def _harami(self, last, prev) -> Optional[Dict]:
        prev_body = self._body(prev)
        last_body = self._body(last)

        if prev_body == 0:
            return None

        inside = (
            max(last['open'], last['close']) <
            max(prev['open'], prev['close']) and
            min(last['open'], last['close']) >
            min(prev['open'], prev['close'])
        )

        if last_body < prev_body * 0.5 and inside:
            if self._bearish(prev) and self._bullish(last):
                return {
                    "name":        "🔄 Bullish Harami",
                    "type":        "BULLISH",
                    "score":       22,
                    "description": "Possible CALL reversal forming"
                }
            elif self._bullish(prev) and self._bearish(last):
                return {
                    "name":        "🔄 Bearish Harami",
                    "type":        "BEARISH",
                    "score":       -22,
                    "description": "Possible PUT reversal forming"
                }
        return None

    def _piercing_line(self, last, prev) -> Optional[Dict]:
        if not (self._bearish(prev) and self._bullish(last)):
            return None

        mid_prev = (prev['open'] + prev['close']) / 2

        if (last['open'] < prev['close'] and
                last['close'] > mid_prev and
                last['close'] < prev['open']):
            return {
                "name":        "💉 Piercing Line",
                "type":        "BULLISH",
                "score":       24,
                "description": "CALL signal - bulls piercing downtrend"
            }
        return None

    def _dark_cloud(self, last, prev) -> Optional[Dict]:
        if not (self._bullish(prev) and self._bearish(last)):
            return None

        mid_prev = (prev['open'] + prev['close']) / 2

        if (last['open'] > prev['close'] and
                last['close'] < mid_prev and
                last['close'] > prev['open']):
            return {
                "name":        "☁️ Dark Cloud Cover",
                "type":        "BEARISH",
                "score":       -24,
                "description": "PUT signal - bears covering the bulls"
            }
        return None

    def _tweezer(self, last, prev) -> Optional[Dict]:
        tol = 0.0003

        if (abs(last['low'] - prev['low']) < tol and
                self._bearish(prev) and self._bullish(last)):
            return {
                "name":        "🔧 Tweezer Bottom",
                "type":        "BULLISH",
                "score":       20,
                "description": "Double bottom support - CALL signal"
            }

        if (abs(last['high'] - prev['high']) < tol and
                self._bullish(prev) and self._bearish(last)):
            return {
                "name":        "🔧 Tweezer Top",
                "type":        "BEARISH",
                "score":       -20,
                "description": "Double top resistance - PUT signal"
            }
        return None

    # ── THREE CANDLE PATTERNS ──────────────────────────────
    def _morning_star(self, last, prev, prev2) -> Optional[Dict]:
        if not (self._bearish(prev2) and self._bullish(last)):
            return None

        mid_prev2  = (prev2['open'] + prev2['close']) / 2
        prev_body  = self._body(prev)
        prev2_body = self._body(prev2)

        if (prev_body < prev2_body * 0.35 and
                last['close'] > mid_prev2):
            return {
                "name":        "🌟 Morning Star",
                "type":        "BULLISH",
                "score":       42,
                "description": "VERY STRONG CALL - bottom reversal pattern!"
            }
        return None

    def _evening_star(self, last, prev, prev2) -> Optional[Dict]:
        if not (self._bullish(prev2) and self._bearish(last)):
            return None

        mid_prev2  = (prev2['open'] + prev2['close']) / 2
        prev_body  = self._body(prev)
        prev2_body = self._body(prev2)

        if (prev_body < prev2_body * 0.35 and
                last['close'] < mid_prev2):
            return {
                "name":        "🌆 Evening Star",
                "type":        "BEARISH",
                "score":       -42,
                "description": "VERY STRONG PUT - top reversal pattern!"
            }
        return None

    def _three_soldiers(self, last, prev, prev2) -> Optional[Dict]:
        if not (self._bullish(last) and
                self._bullish(prev) and
                self._bullish(prev2)):
            return None

        if (last['close'] > prev['close'] > prev2['close'] and
                last['open'] > prev['open'] > prev2['open']):
            return {
                "name":        "💂 Three White Soldiers",
                "type":        "BULLISH",
                "score":       48,
                "description": "EXTREMELY STRONG CALL pattern!"
            }
        return None

    def _three_crows(self, last, prev, prev2) -> Optional[Dict]:
        if not (self._bearish(last) and
                self._bearish(prev) and
                self._bearish(prev2)):
            return None

        if (last['close'] < prev['close'] < prev2['close'] and
                last['open'] < prev['open'] < prev2['open']):
            return {
                "name":        "🦅 Three Black Crows",
                "type":        "BEARISH",
                "score":       -48,
                "description": "EXTREMELY STRONG PUT pattern!"
            }
        return None
