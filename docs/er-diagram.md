# CryptoSight ER Diagram

```mermaid
erDiagram
    USER ||--o{ SYSTEM_LOG : writes
    USER {
        int id PK
        string username
        string password_hash
        string role
        datetime created_at
    }
    CRYPTO_PRICE {
        int id PK
        string symbol
        string market
        datetime ts
        float open
        float high
        float low
        float close
        float volume
        float market_cap
        string source
    }
    MACRO_INDICATOR {
        int id PK
        string indicator_name
        datetime ts
        float value
        string unit
        string source
    }
    SENTIMENT_DATA {
        int id PK
        string platform
        string symbol
        datetime ts
        float positive
        float neutral
        float negative
        float sentiment_score
        string source
    }
    PREDICTION_RESULT {
        int id PK
        string symbol
        string model_name
        int horizon_days
        datetime ts
        float predicted_price
        float confidence_score
        json metrics
    }
    FEATURE_IMPORTANCE {
        int id PK
        string symbol
        string model_name
        string feature_name
        float importance
        int rank
        string analysis_type
        datetime ts
    }
    SYSTEM_LOG {
        int id PK
        int user_id FK
        string level
        string module
        string message
        json extra
        datetime created_at
    }
```

## Notes

- `crypto_price`, `macro_indicator`, and `sentiment_data` are time-series fact tables.
- `prediction_result` stores model outputs for each forecast horizon.
- `feature_importance` stores ranking results for thesis figures and reports.
- `system_log` records operational events and user actions.
