"""
config.py
---------
Reads all your settings and secret keys.
Think of this as the bot's settings menu.
"""

import os
import yaml
from dotenv import load_dotenv
from loguru import logger

# Load .env file if it exists (for local testing)
load_dotenv()


class Config:
    """
    Holds all configuration for the bot.
    Settings come from two places:
    1. config.yaml  (general settings)
    2. Environment variables (secret keys)
    """

    _instance = None  # Singleton pattern

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if not self._loaded:
            self._load()
            self._loaded = True

    def _load(self):
        """Load config.yaml file"""
        try:
            config_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)
                    )
                ),
                'config.yaml'
            )

            with open(config_path, 'r') as f:
                content = f.read()

            # Replace ${VAR_NAME} with actual environment values
            for key, value in os.environ.items():
                content = content.replace(f'${{{key}}}', value)

            self._data = yaml.safe_load(content)
            logger.success("✅ Config loaded OK")

        except FileNotFoundError:
            logger.warning("config.yaml not found, using defaults")
            self._data = {}
        except Exception as e:
            logger.error(f"Config error: {e}")
            self._data = {}

    def _get(self, *keys, default=None):
        """Get nested config value safely"""
        val = self._data
        for key in keys:
            if isinstance(val, dict):
                val = val.get(key, default)
            else:
                return default
        return val

    # ── TELEGRAM SETTINGS ──────────────────────────────────
    @property
    def telegram_token(self) -> str:
        return os.getenv('TELEGRAM_BOT_TOKEN', '')

    @property
    def channel_id(self) -> str:
        return os.getenv('TELEGRAM_CHANNEL_ID', '')

    @property
    def admin_id(self) -> str:
        return os.getenv('ADMIN_TELEGRAM_ID', '')

    # ── TRADING PAIRS ───────────────────────────────────────
    @property
    def otc_pairs(self) -> list:
        return self._get('signals', 'otc_pairs', default=[
            "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC",
            "AUDUSD-OTC", "EURJPY-OTC"
        ])

    @property
    def forex_pairs(self) -> list:
        return self._get('signals', 'forex_pairs', default=[
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD"
        ])

    @property
    def timeframes(self) -> list:
        return self._get('signals', 'timeframes',
                         default=["1m", "5m", "10m"])

    # ── SIGNAL SETTINGS ─────────────────────────────────────
    @property
    def min_confidence(self) -> float:
        env_val = os.getenv('MIN_CONFIDENCE')
        if env_val:
            return float(env_val)
        return float(self._get('signals', 'min_confidence', default=75))

    # ── INTELLIGENCE WEIGHTS ────────────────────────────────
    @property
    def weights(self) -> dict:
        return self._get('intelligence', 'weights', default={
            'technical_analysis': 0.35,
            'pattern_recognition': 0.25,
            'ml_prediction': 0.30,
            'market_sentiment': 0.10
        })
