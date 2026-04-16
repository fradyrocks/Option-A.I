"""
data_fetcher.py
---------------
Gets live price data from Yahoo Finance (FREE).
Think of this as the bot's eyes - it watches
the markets and collects price information.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from loguru import logger


class DataFetcher:
    """
    Downloads price candles for all currency pairs.
    Uses Yahoo Finance which is 100% FREE.
    """

    # Maps our pair names to Yahoo Finance symbols
    SYMBOL_MAP = {
        "EURUSD-OTC":  "EURUSD=X",
        "GBPUSD-OTC":  "GBPUSD=X",
        "USDJPY-OTC":  "USDJPY=X",
        "AUDUSD-OTC":  "AUDUSD=X",
        "EURJPY-OTC":  "EURJPY=X",
        "GBPJPY-OTC":  "GBPJPY=X",
        "USDCHF-OTC":  "USDCHF=X",
        "NZDUSD-OTC":  "NZDUSD=X",
        "EURGBP-OTC":  "EURGBP=X",
        "USDCAD-OTC":  "USDCAD=X",
        "EURUSD":      "EURUSD=X",
        "GBPUSD":      "GBPUSD=X",
        "USDJPY":      "USDJPY=X",
        "AUDUSD":      "AUDUSD=X",
        "EURJPY":      "EURJPY=X",
        "GBPJPY":      "GBPJPY=X",
        "USDCHF":      "USDCHF=X",
        "NZDUSD":      "NZDUSD=X",
    }

    # Base prices for generating OTC-style data
    BASE_PRICES = {
        "EURUSD": 1.0850, "GBPUSD": 1.2650,
        "USDJPY": 149.50, "AUDUSD": 0.6550,
        "EURJPY": 162.00, "GBPJPY": 189.00,
        "USDCHF": 0.8900, "NZDUSD": 0.6100,
        "EURGBP": 0.8600, "USDCAD": 1.3600,
    }

    def __init__(self):
        # Simple cache to avoid too many requests
        self._cache = {}
        self._cache_seconds = 45  # cache data for 45 seconds

    def get_candles(self, pair: str, timeframe: str = "1m",
                    count: int = 150) -> pd.DataFrame:
        """
        Get price candles for a currency pair.

        Returns a table with columns:
        open, high, low, close, volume
        (just like a candle chart!)
        """
        cache_key = f"{pair}_{timeframe}"
        now = time.time()

        # Return cached data if still fresh
        if cache_key in self._cache:
            cached_at, cached_df = self._cache[cache_key]
            if now - cached_at < self._cache_seconds:
                return cached_df

        # Get Yahoo Finance symbol
        yf_symbol = self.SYMBOL_MAP.get(pair, f"{pair}=X")

        try:
            df = self._fetch_from_yahoo(yf_symbol, timeframe, count)

            if df is not None and len(df) >= 20:
                self._cache[cache_key] = (now, df)
                return df

        except Exception as e:
            logger.warning(f"Yahoo Finance error for {pair}: {e}")

        # If Yahoo fails, generate synthetic data
        logger.info(f"Using synthetic data for {pair}")
        df = self._make_synthetic_data(pair, count)
        self._cache[cache_key] = (now, df)
        return df

    def _fetch_from_yahoo(self, symbol: str, timeframe: str,
                           count: int) -> pd.DataFrame:
        """Download data from Yahoo Finance"""

        # Map our timeframes to Yahoo Finance format
        yf_interval_map = {
            "1m":  ("1m",  "1d"),
            "5m":  ("5m",  "5d"),
            "10m": ("15m", "5d"),
            "15m": ("15m", "5d"),
            "1h":  ("1h",  "30d"),
        }

        yf_interval, period = yf_interval_map.get(
            timeframe, ("5m", "5d")
        )

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=yf_interval)

        if df.empty:
            return None

        # Rename columns to our format
        df = df.rename(columns={
            'Open':   'open',
            'High':   'high',
            'Low':    'low',
            'Close':  'close',
            'Volume': 'volume'
        })

        df = df[['open', 'high', 'low', 'close', 'volume']]
        df = df.dropna()
        df = df.tail(count)

        return df

    def _make_synthetic_data(self, pair: str,
                              count: int = 150) -> pd.DataFrame:
        """
        Creates realistic fake price data when live data fails.
        Uses math (Geometric Brownian Motion) to look realistic.
        """
        # Get base price for this pair
        base_pair = pair.replace("-OTC", "")
        base_price = self.BASE_PRICES.get(base_pair, 1.0000)

        # Generate price path using random walk
        np.random.seed(int(time.time()) % 1000)

        returns = np.random.normal(0.0001, 0.0008, count)
        prices = base_price * np.exp(np.cumsum(returns))

        candles = []
        for i in range(count):
            open_p = prices[i]
            noise = np.random.uniform(0.0001, 0.0006)

            high_p  = open_p + abs(np.random.normal(0, noise))
            low_p   = open_p - abs(np.random.normal(0, noise))
            close_p = np.random.uniform(low_p, high_p)
            volume  = np.random.randint(5000, 100000)

            candles.append({
                'open':   round(open_p,  5),
                'high':   round(high_p,  5),
                'low':    round(low_p,   5),
                'close':  round(close_p, 5),
                'volume': volume
            })

        df = pd.DataFrame(candles)
        df.index = pd.date_range(
            end=datetime.now(),
            periods=count,
            freq='1min'
        )

        return df
