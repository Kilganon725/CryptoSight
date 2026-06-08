# CryptoSight API Documentation

Base path: `/api`

## Health

- `GET /api/health`
- Response: `{"message": "ok"}`

## Market Data

- `GET /api/btc/history?inst_id=BTC-USDT&limit=365&bar=1H`
- `GET /api/market/overview?inst_id=BTC-USDT`
- `GET /api/macro`
- `GET /api/sentiment`
- `GET /api/market/instrument?inst_id=BTC-USDT`
- `GET /api/market/orderbook?inst_id=BTC-USDT&depth=20`
- `GET /api/market/trades?inst_id=BTC-USDT&limit=20`

Supported `bar` values for OKX K-line requests include:

- `1m`
- `5m`
- `15m`
- `1H`
- `4H`
- `1D`
- `1W`
- `1M`

## Factor Analysis

- `GET /api/factors`
- Returns:
- Pearson correlation matrix
- Spearman correlation matrix
- Granger causality summary
- Random Forest feature importance
- SHAP summary when available

## Prediction

- `POST /api/predict`
- Body:
```json
{
  "symbol": "BTC",
  "model_name": "xgboost",
  "horizon_days": 7
}
```

- `POST /api/train`
- Body: same as above
- `GET /api/model-performance?symbol=BTC&horizon_days=7`

## Live Ingestion

- `POST /api/ingest/live`
- `GET /api/live/okx/ticker`

These endpoints pull live OKX market data into the database and optionally ingest X / Reddit search results when the required credentials are configured.

## Response fields

- `predicted_price`
- `confidence_score`
- `metrics` with `mae`, `mse`, `rmse`, `mape`, `r2`
