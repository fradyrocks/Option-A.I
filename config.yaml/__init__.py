telegram:
  token: "${TELEGRAM_BOT_TOKEN}"
  channel_id: "${TELEGRAM_CHANNEL_ID}"
  admin_id: "${ADMIN_TELEGRAM_ID}"

signals:
  timeframes:
    - "1m"
    - "5m"
    - "10m"
  min_confidence: 75
  otc_pairs:
    - "EURUSD-OTC"
    - "GBPUSD-OTC"
    - "USDJPY-OTC"
    - "AUDUSD-OTC"
    - "EURJPY-OTC"
    - "GBPJPY-OTC"
    - "USDCHF-OTC"
    - "NZDUSD-OTC"
    - "EURGBP-OTC"
    - "USDCAD-OTC"
  forex_pairs:
    - "EURUSD"
    - "GBPUSD"
    - "USDJPY"
    - "AUDUSD"
    - "EURJPY"
    - "GBPJPY"

intelligence:
  weights:
    technical_analysis: 0.35
    pattern_recognition: 0.25
    ml_prediction: 0.30
    market_sentiment: 0.10

data:
  primary: "yahoo_finance"

sessions:
  best_hours: [8, 9, 10, 13, 14, 15, 16]

database:
  type: "tinydb"
  path: "data/signals.json"

logging:
  level: "INFO"
  file: "logs/bot.log"
