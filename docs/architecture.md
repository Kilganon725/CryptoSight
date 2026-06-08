# CryptoSight System Architecture

```mermaid
flowchart TD
    A[Data Sources] --> B[Data Collection Layer]
    B --> C[Data Cleaning Layer]
    C --> D[Feature Engineering Layer]
    D --> E[Factor Analysis Layer]
    D --> F[Prediction Layer]
    E --> G[Visualization Dashboard]
    F --> G
    G --> H[Web Application]

    A1[BTC / ETH Market Data] --> A
    A2[Macro Indicators via FRED] --> A
    A3[Sentiment Data via NLP Models] --> A
```

## Layers

- Data Sources: Binance, CoinGecko, CoinMarketCap, FRED, news, Twitter/X, Reddit.
- Data Collection Layer: ETL jobs and API collectors.
- Data Cleaning Layer: missing values, outlier clipping, interpolation.
- Feature Engineering Layer: RSI, MACD, moving averages, volatility, lagged features.
- Factor Analysis Layer: correlation, Granger causality, feature importance, SHAP.
- Prediction Layer: ARIMA, Prophet, Random Forest, XGBoost, LSTM.
- Visualization Dashboard: market overview, macro trends, sentiment, factors, prediction center.
