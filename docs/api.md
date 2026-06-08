# CryptoSight API Documentation

Base path: `/api`

## Health

- `GET /api/health`
- Response: `{"message": "ok"}`

## Market Data

- `GET /api/btc/history?limit=365`
- `GET /api/market/overview`
- `GET /api/macro`
- `GET /api/sentiment`

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

## Response fields

- `predicted_price`
- `confidence_score`
- `metrics` with `mae`, `mse`, `rmse`, `mape`, `r2`
