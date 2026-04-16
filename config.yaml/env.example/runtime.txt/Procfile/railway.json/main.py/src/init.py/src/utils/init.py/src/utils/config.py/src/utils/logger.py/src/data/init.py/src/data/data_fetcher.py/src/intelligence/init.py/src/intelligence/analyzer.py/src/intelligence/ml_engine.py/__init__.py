"""
ml_engine.py
------------
The Artificial Intelligence part of the bot.
Uses 3 machine learning models that vote together.
Think of it as 3 AI experts giving their opinion!

Models used:
1. Random Forest  - Like asking 200 decision trees
2. XGBoost        - Award-winning ML algorithm
3. Gradient Boost - Learns from past mistakes
"""

import numpy as np
import pandas as pd
import os
import joblib
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier
)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from loguru import logger
from typing import Dict, Tuple


class MLEngine:
    """
    Three AI models working together as a team.
    The majority vote wins!
    """

    def __init__(self):
        self.model_dir  = "models/trained_models"
        self.is_trained = False

        os.makedirs(self.model_dir, exist_ok=True)

        # Model 1: Random Forest
        self.rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )

        # Model 2: XGBoost
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42,
            verbosity=0
        )

        # Model 3: Gradient Boosting
        self.gb = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            random_state=42
        )

        # Scaler (normalizes data so models work better)
        self.scaler = StandardScaler()

        # Try to load pre-saved models
        self._load_models()

    def _feature_columns(self) -> list:
        """List of features we use for prediction"""
        return [
            'RSI', 'RSI_7', 'MACD', 'MACD_Signal', 'MACD_Hist',
            'Stoch_K', 'Stoch_D', 'Williams_R', 'CCI',
            'BB_Pct', 'BB_Width', 'ATR',
            'EMA_8', 'EMA_21', 'ADX',
            'Body', 'Upper_Wick', 'Lower_Wick', 'Is_Bullish',
            'Price_Chg', 'ROC_5', 'ROC_10'
        ]

    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Pull out the numbers the AI models need"""
        cols      = self._feature_columns()
        available = [c for c in cols if c in df.columns]

        if len(available) < 5:
            return np.array([])

        last_row = df[available].iloc[-1].fillna(0).values
        return last_row.reshape(1, -1)

    def train(self, df: pd.DataFrame) -> Dict:
        """
        Teach the AI models using historical data.
        Like showing a student thousands of examples
        so they can learn the pattern.
        """
        logger.info("🤖 Training AI models (this takes ~30 seconds)...")

        cols      = self._feature_columns()
        available = [c for c in cols if c in df.columns]

        if len(available) < 5:
            return {"status": "error", "msg": "Not enough data"}

        # Create training data
        df_train = df.copy()

        # Label: 1 = price went UP next candle, 0 = went DOWN
        df_train['label'] = (
            df_train['close'].shift(-1) > df_train['close']
        ).astype(int)

        df_train = df_train.dropna(subset=['label'])

        X = df_train[available].fillna(0).values[:-1]
        y = df_train['label'].values[:-1]

        if len(X) < 50:
            return {"status": "error", "msg": "Need at least 50 samples"}

        try:
            # Scale the data
            X_scaled = self.scaler.fit_transform(X)

            # Train all 3 models
            self.rf.fit(X_scaled, y)
            self.xgb_model.fit(X_scaled, y)
            self.gb.fit(X_scaled, y)

            self.is_trained = True
            self._save_models()

            logger.success(
                f"✅ AI models trained on {len(X)} samples!"
            )
            return {
                "status":  "success",
                "samples": len(X)
            }

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"status": "error", "msg": str(e)}

    def predict(self, df: pd.DataFrame) -> Dict:
        """
        Ask all 3 AI models for their prediction.
        Returns the majority vote.
        """
        if not self.is_trained:
            return {
                "direction":  "CALL",
                "confidence": 50,
                "ml_active":  False,
                "message":    "Models not trained yet"
            }

        features = self._extract_features(df)

        if features.size == 0:
            return {
                "direction":  "CALL",
                "confidence": 50,
                "ml_active":  False
            }

        try:
            # Adjust feature count if needed
            expected = self.scaler.n_features_in_
            current  = features.shape[1]

            if current < expected:
                pad      = np.zeros((1, expected - current))
                features = np.hstack([features, pad])
            elif current > expected:
                features = features[:, :expected]

            features_scaled = self.scaler.transform(features)

            # Get probabilities from each model
            # probability = chance of price going UP (0.0 to 1.0)
            rf_prob  = self.rf.predict_proba(features_scaled)[0][1]
            xgb_prob = self.xgb_model.predict_proba(
                features_scaled
            )[0][1]
            gb_prob  = self.gb.predict_proba(features_scaled)[0][1]

            # Weighted average (XGBoost is most reliable)
            avg_prob = (
                rf_prob  * 0.30 +
                xgb_prob * 0.40 +
                gb_prob  * 0.30
            )

            direction  = "CALL" if avg_prob > 0.5 else "PUT"
            confidence = abs(avg_prob - 0.5) * 200  # 0 to 100

            return {
                "direction":   direction,
                "confidence":  min(confidence, 100),
                "probability": avg_prob,
                "ml_active":   True,
                "model_votes": {
                    "random_forest":   "CALL" if rf_prob  > 0.5 else "PUT",
                    "xgboost":         "CALL" if xgb_prob > 0.5 else "PUT",
                    "gradient_boost":  "CALL" if gb_prob  > 0.5 else "PUT"
                }
            }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                "direction":  "CALL",
                "confidence": 50,
                "ml_active":  False,
                "error":      str(e)
            }

    def _save_models(self):
        """Save trained models to disk so we don't retrain every time"""
        try:
            joblib.dump(self.rf,        f"{self.model_dir}/rf.pkl")
            joblib.dump(self.xgb_model, f"{self.model_dir}/xgb.pkl")
            joblib.dump(self.gb,        f"{self.model_dir}/gb.pkl")
            joblib.dump(self.scaler,    f"{self.model_dir}/scaler.pkl")
            logger.info("💾 Models saved to disk")
        except Exception as e:
            logger.error(f"Save error: {e}")

    def _load_models(self) -> bool:
        """Load previously trained models from disk"""
        paths = [
            f"{self.model_dir}/rf.pkl",
            f"{self.model_dir}/xgb.pkl",
            f"{self.model_dir}/gb.pkl",
            f"{self.model_dir}/scaler.pkl"
        ]

        if all(os.path.exists(p) for p in paths):
            try:
                self.rf        = joblib.load(paths[0])
                self.xgb_model = joblib.load(paths[1])
                self.gb        = joblib.load(paths[2])
                self.scaler    = joblib.load(paths[3])
                self.is_trained = True
                logger.success("✅ Pre-trained AI models loaded!")
                return True
            except Exception as e:
                logger.warning(f"Could not load models: {e}")

        return False
