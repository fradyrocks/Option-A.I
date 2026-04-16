"""
analyzer.py
-----------
The brain of the bot.
Calculates 15+ technical indicators
and decides if the market is going UP or DOWN.
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from loguru import logger
from typing import Dict
import warnings
warnings.filterwarnings('ignore')


class TechnicalAnalyzer:
    """
    Analyzes price charts using technical indicators.

    What are indicators?
    Think of them as different doctors giving opinions.
    RSI is one doctor, MACD is another.
    We ask all of them and take a vote!
    """

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to the price data.
        Like adding extra columns of information to a spreadsheet.
        """
        if len(df) < 20:
            return df

        try:
            close = df['close']
            high  = df['high']
            low   = df['low']

            # ── TREND (Which direction is the market going?) ──
            df['EMA_8']  = ta.ema(close, length=8)
            df['EMA_21'] = ta.ema(close, length=21)
            df['EMA_50'] = ta.ema(close, length=50)

            macd = ta.macd(close, fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty:
                df['MACD']        = macd.iloc[:, 0]
                df['MACD_Signal'] = macd.iloc[:, 2]
                df['MACD_Hist']   = macd.iloc[:, 1]

            adx_data = ta.adx(high, low, close, length=14)
            if adx_data is not None and not adx_data.empty:
                df['ADX']    = adx_data.iloc[:, 0]
                df['DI_pos'] = adx_data.iloc[:, 1]
                df['DI_neg'] = adx_data.iloc[:, 2]

            # ── MOMENTUM (How fast is price moving?) ──────────
            df['RSI']   = ta.rsi(close, length=14)
            df['RSI_7'] = ta.rsi(close, length=7)

            stoch = ta.stoch(high, low, close)
            if stoch is not None and not stoch.empty:
                df['Stoch_K'] = stoch.iloc[:, 0]
                df['Stoch_D'] = stoch.iloc[:, 1]

            df['Williams_R'] = ta.willr(high, low, close, length=14)
            df['CCI']        = ta.cci(high, low, close, length=14)

            # ── VOLATILITY (How much is price jumping?) ───────
            bb = ta.bbands(close, length=20, std=2)
            if bb is not None and not bb.empty:
                df['BB_Upper']  = bb.iloc[:, 0]
                df['BB_Middle'] = bb.iloc[:, 1]
                df['BB_Lower']  = bb.iloc[:, 2]
                df['BB_Width']  = bb.iloc[:, 3]
                df['BB_Pct']    = bb.iloc[:, 4]

            df['ATR'] = ta.atr(high, low, close, length=14)

            # ── PRICE ACTION (What does the candle look like?) ─
            df['Body']        = abs(close - df['open'])
            df['Upper_Wick']  = high - df[['open', 'close']].max(axis=1)
            df['Lower_Wick']  = df[['open', 'close']].min(axis=1) - low
            df['Is_Bullish']  = (close > df['open']).astype(int)
            df['Price_Chg']   = close.pct_change()
            df['ROC_5']       = ta.roc(close, length=5)
            df['ROC_10']      = ta.roc(close, length=10)

        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")

        return df

    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Check if market trend is UP or DOWN"""
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        score   = 0
        signals = []

        # EMA alignment check
        if all(c in df.columns for c in ['EMA_8', 'EMA_21', 'EMA_50']):
            if last['EMA_8'] > last['EMA_21'] > last['EMA_50']:
                score += 25
                signals.append("📈 All EMAs pointing UP (Bullish)")
            elif last['EMA_8'] < last['EMA_21'] < last['EMA_50']:
                score -= 25
                signals.append("📉 All EMAs pointing DOWN (Bearish)")

        # MACD check
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            if (last['MACD'] > last['MACD_Signal'] and
                    prev['MACD'] <= prev['MACD_Signal']):
                score += 20
                signals.append("⚡ MACD just crossed UP - Bullish!")
            elif (last['MACD'] < last['MACD_Signal'] and
                  prev['MACD'] >= prev['MACD_Signal']):
                score -= 20
                signals.append("⚡ MACD just crossed DOWN - Bearish!")
            elif last['MACD'] > last['MACD_Signal']:
                score += 8
            else:
                score -= 8

        # ADX strength check
        if 'ADX' in df.columns:
            if last['ADX'] > 25:
                if 'DI_pos' in df.columns:
                    if last['DI_pos'] > last['DI_neg']:
                        score += 15
                        signals.append(
                            f"💪 Strong uptrend (ADX={last['ADX']:.1f})"
                        )
                    else:
                        score -= 15
                        signals.append(
                            f"💪 Strong downtrend (ADX={last['ADX']:.1f})"
                        )

        direction  = "CALL" if score > 0 else "PUT"
        confidence = min(abs(score), 100)

        return {
            "direction":  direction,
            "score":      score,
            "confidence": confidence,
            "signals":    signals
        }

    def analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """Check how fast and strong the price move is"""
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        score   = 0
        signals = []

        # RSI check
        if 'RSI' in df.columns:
            rsi = last['RSI']

            if rsi < 25:
                score += 30
                signals.append(f"🔥 RSI extremely low ({rsi:.1f}) - Buy signal!")
            elif rsi < 35:
                score += 18
                signals.append(f"📊 RSI oversold ({rsi:.1f}) - Likely bounce up")
            elif rsi > 75:
                score -= 30
                signals.append(f"🔥 RSI extremely high ({rsi:.1f}) - Sell signal!")
            elif rsi > 65:
                score -= 18
                signals.append(f"📊 RSI overbought ({rsi:.1f}) - Likely drop")

        # Stochastic check
        if 'Stoch_K' in df.columns:
            sk = last['Stoch_K']
            sd = last['Stoch_D']

            if sk < 20 and sd < 20:
                score += 20
                signals.append("📉 Stochastic in oversold zone - CALL signal")
            elif sk > 80 and sd > 80:
                score -= 20
                signals.append("📈 Stochastic in overbought zone - PUT signal")

            # Stochastic cross
            if sk > sd and prev['Stoch_K'] <= prev['Stoch_D']:
                if sk < 40:
                    score += 15
                    signals.append("✅ Stochastic crossed UP from low level")
            elif sk < sd and prev['Stoch_K'] >= prev['Stoch_D']:
                if sk > 60:
                    score -= 15
                    signals.append("❌ Stochastic crossed DOWN from high level")

        # Williams %R check
        if 'Williams_R' in df.columns:
            wr = last['Williams_R']
            if wr < -80:
                score += 12
                signals.append(f"💡 Williams %R oversold ({wr:.0f})")
            elif wr > -20:
                score -= 12
                signals.append(f"💡 Williams %R overbought ({wr:.0f})")

        direction  = "CALL" if score > 0 else "PUT"
        confidence = min(abs(score), 100)

        return {
            "direction":  direction,
            "score":      score,
            "confidence": confidence,
            "signals":    signals
        }

    def analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """Check if conditions are good for trading"""
        last    = df.iloc[-1]
        score   = 0
        signals = []

        # Bollinger Bands check
        if all(c in df.columns for c in ['BB_Upper', 'BB_Lower']):
            price    = last['close']
            bb_upper = last['BB_Upper']
            bb_lower = last['BB_Lower']

            if price <= bb_lower:
                score += 25
                signals.append("🎯 Price hit LOWER Bollinger Band - CALL!")
            elif price >= bb_upper:
                score -= 25
                signals.append("🎯 Price hit UPPER Bollinger Band - PUT!")
            elif 'BB_Pct' in df.columns and last['BB_Pct'] < 0.15:
                score += 12
                signals.append("💎 Bollinger Band squeeze - breakout coming!")

        # ATR check (is volatility too high or low?)
        if 'ATR' in df.columns:
            atr      = last['ATR']
            atr_avg  = df['ATR'].tail(50).mean()

            if pd.notna(atr) and pd.notna(atr_avg) and atr_avg > 0:
                ratio = atr / atr_avg
                if ratio > 2.0:
                    signals.append("⚠️ Very high volatility - be careful!")
                    score = int(score * 0.7)
                elif ratio < 0.3:
                    signals.append("😴 Very low volatility - weak signal")
                    score = int(score * 0.5)
                else:
                    signals.append("✅ Good volatility for trading")

        direction  = "CALL" if score > 0 else "PUT"
        confidence = min(abs(score), 100)

        return {
            "direction":  direction,
            "score":      score,
            "confidence": confidence,
            "signals":    signals
          }
