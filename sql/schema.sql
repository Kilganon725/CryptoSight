CREATE TABLE IF NOT EXISTS user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'viewer',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_username (username)
);

CREATE TABLE IF NOT EXISTS crypto_price (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(16) NOT NULL,
    market VARCHAR(32) NOT NULL DEFAULT 'spot',
    ts DATETIME NOT NULL,
    open DOUBLE NOT NULL,
    high DOUBLE NOT NULL,
    low DOUBLE NOT NULL,
    close DOUBLE NOT NULL,
    volume DOUBLE NOT NULL DEFAULT 0,
    market_cap DOUBLE NULL,
    source VARCHAR(64) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_crypto_symbol_ts (symbol, ts),
    INDEX idx_crypto_symbol_market_ts (symbol, market, ts)
);

CREATE TABLE IF NOT EXISTS macro_indicator (
    id INT PRIMARY KEY AUTO_INCREMENT,
    indicator_name VARCHAR(64) NOT NULL,
    ts DATETIME NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR(32) NULL,
    source VARCHAR(64) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_macro_name_ts (indicator_name, ts)
);

CREATE TABLE IF NOT EXISTS sentiment_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    platform VARCHAR(32) NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    ts DATETIME NOT NULL,
    positive DOUBLE NOT NULL DEFAULT 0,
    neutral DOUBLE NOT NULL DEFAULT 0,
    negative DOUBLE NOT NULL DEFAULT 0,
    sentiment_score DOUBLE NOT NULL DEFAULT 0,
    raw_text TEXT NULL,
    source VARCHAR(64) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sentiment_symbol_ts (symbol, ts)
);

CREATE TABLE IF NOT EXISTS prediction_result (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(16) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    horizon_days INT NOT NULL,
    ts DATETIME NOT NULL,
    predicted_price DOUBLE NOT NULL,
    confidence_score DOUBLE NULL,
    metrics JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prediction_symbol_model_ts (symbol, model_name, ts)
);

CREATE TABLE IF NOT EXISTS feature_importance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(16) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    feature_name VARCHAR(128) NOT NULL,
    importance DOUBLE NOT NULL,
    `rank` INT NOT NULL,
    analysis_type VARCHAR(32) NOT NULL DEFAULT 'feature_importance',
    ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_feature_symbol_model_rank (symbol, model_name, `rank`)
);

CREATE TABLE IF NOT EXISTS system_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    level VARCHAR(16) NOT NULL DEFAULT 'INFO',
    module VARCHAR(64) NOT NULL DEFAULT 'system',
    message TEXT NOT NULL,
    extra JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_system_log_created_at (created_at),
    CONSTRAINT fk_system_log_user FOREIGN KEY (user_id) REFERENCES user(id)
);
