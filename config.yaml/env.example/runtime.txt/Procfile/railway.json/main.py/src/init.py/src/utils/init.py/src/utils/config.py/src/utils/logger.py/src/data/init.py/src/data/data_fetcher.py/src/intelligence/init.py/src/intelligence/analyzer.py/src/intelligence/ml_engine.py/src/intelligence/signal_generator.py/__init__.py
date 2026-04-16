"""
signal_generator.py
-------------------
The MASTER BRAIN that combines everything:
- Technical Analysis (indicators)
- Pattern Detection (candlestick shapes)
- ML Prediction (AI models)

Then makes a final CALL or PUT decision.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
from loguru import logger
import pytz

from .analyzer import TechnicalAnalyzer
from .pattern_detector import PatternDetector
from .ml_engine import MLEngine


class SignalGenerator:
    """
    Combines all analysis methods into one final signal.
    Like a judge hearing from multiple experts, then
    making the final ruling.
    """

    def __init__(self, config):
        self.config    = config
        self.analyzer  = TechnicalAnalyzer()
        self.detector  = PatternDetector()
        self.ml        = MLEngine()
        self._trained  = False

    def generate_signal(self, pair: str, timeframe: str,
                         df: pd.DataFrame) -> Optional[Dict]:
        """
        Main function - generates a complete signal.
        Returns None if confidence is too low.
        """
        if df is None or len(df) < 30:
            return None

        try:
            # ── STEP 1: Add all indicators ─────────────────
            df = self.analyzer.calculate_all_indicators(df)

            # ── STEP 2: Run all analyses ───────────────────
            trend      = self.analyzer.analyze_trend(df)
            momentum   = self.analyzer.analyze_momentum(df)
            volatility = self.analyzer.analyze_volatility(df)
            patterns   = self.detector.detect_all_patterns(df)

            # ── STEP 3: Train/run ML if enough data ────────
            if not self._trained and len(df) >= 60:
                self.ml.train(df)
                self._trained = True

            ml_result = self.ml.predict(df)

            # ── STEP 4: Count votes ────────────────────────
            call_score = 0
            put_score  = 0

            # Technical analysis votes
            for analysis in [trend, momentum, volatility]:
                w = analysis.get('confidence', 50) / 100
                if analysis['direction'] == 'CALL':
                    call_score += w * 20
                else:
                    put_score  += w * 20

            # Pattern votes (double weight)
            if patterns['direction'] == 'CALL':
                call_score += patterns.get('confidence', 0) * 0.3
            elif patterns['direction'] == 'PUT':
                put_score  += patterns.get('confidence', 0) * 0.3

            # ML vote (double weight)
            if ml_result.get('ml_active'):
                ml_conf = ml_result.get('confidence', 0)
                if ml_result['direction'] == 'CALL':
                    call_score += ml_conf * 0.3
                else:
                    put_score  += ml_conf * 0.3

            # ── STEP 5: Determine direction ────────────────
            if call_score == put_score:
                return None  # No clear winner

            if call_score > put_score:
                direction  = "CALL"
                win_score  = call_score
                lose_score = put_score
            else:
                direction  = "PUT"
                win_score  = put_score
                lose_score = call_score

            total = win_score + lose_score
            if total == 0:
                return None

            # ── STEP 6: Calculate confidence ───────────────
            # Base: how dominant is the winning side?
            vote_ratio = win_score / total  # 0.5 to 1.0

            # Blend with average indicator confidence
            indicator_conf = (
                trend['confidence'] * 0.35 +
                momentum['confidence'] * 0.30 +
                volatility['confidence'] * 0.20 +
                patterns.get('confidence', 0) * 0.15
            )

            # Session bonus
            session_bonus = self._session_score()

            # Final blend
            confidence = (
                vote_ratio     * 100 * 0.40 +
                indicator_conf *       0.40 +
                session_bonus  *       0.20
            )

            # Pattern bonuses
            if patterns['pattern_count'] >= 2:
                confidence *= 1.08

            if (ml_result.get('ml_active') and
                    ml_result['direction'] == direction):
                confidence *= 1.05

            confidence = min(confidence, 99.9)

            # ── STEP 7: Apply minimum confidence filter ────
            if confidence < self.config.min_confidence:
                return None

            # ── STEP 8: Build final signal object ──────────
            price = df['close'].iloc[-1]

            return {
                "id":         f"{pair}_{timeframe}_{int(datetime.now().timestamp())}",
                "pair":       pair,
                "timeframe":  timeframe,
                "direction":  direction,
                "confidence": round(confidence, 1),
                "price":      price,
                "timestamp":  datetime.now(pytz.UTC),
                "market":     "OTC" if "OTC" in pair else "FOREX",
                "expiry":     self._expiry(timeframe),
                "risk":       self._risk_label(confidence),
                "analyses": {
                    "trend":      trend,
                    "momentum":   momentum,
                    "volatility": volatility,
                    "patterns":   patterns,
                    "ml":         ml_result
                },
                "votes": {
                    "call":      round(call_score, 1),
                    "put":       round(put_score, 1),
                    "direction": direction
                }
            }

        except Exception as e:
            logger.error(f"Signal error for {pair}: {e}")
            return None

    def _session_score(self) -> float:
        """Rate how good the current trading session is"""
        hour = datetime.now(pytz.UTC).hour
        best = [8, 9, 13, 14, 15, 16]
        good = [10, 11, 12, 17, 18]

        if hour in best:
            return 90.0
        elif hour in good:
            return 72.0
        elif hour in [0, 1, 2, 3]:
            return 35.0
        else:
            return 58.0

    def _risk_label(self, confidence: float) -> str:
        """Simple risk label based on confidence"""
        if confidence >= 88:
            return "🟢 LOW RISK"
        elif confidence >= 78:
            return "🟡 MEDIUM RISK"
        elif confidence >= 70:
            return "🟠 MODERATE RISK"
        else:
            return "🔴 HIGH RISK"

    def _expiry(self, timeframe: str) -> str:
        """Recommended expiry for each timeframe"""
        expiry = {
            "1m":  "⏱️ 1 - 2 minutes",
            "5m":  "⏱️ 5 - 10 minutes",
            "10m": "⏱️ 10 - 15 minutes",
            "15m": "⏱️ 15 - 20 minutes",
        }
        return expiry.get(timeframe, "⏱️ 1 - 5 minutes")
