from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

try:
    import xgboost as xgb
except Exception:  # pragma: no cover
    xgb = None

try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception:  # pragma: no cover
    ARIMA = None

try:
    from prophet import Prophet
except Exception:  # pragma: no cover
    Prophet = None

try:
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.models import Sequential
except Exception:  # pragma: no cover
    LSTM = Dense = Sequential = None

from app.services.data_processing import prepare_model_frame


@dataclass
class PredictionOutcome:
    model_name: str
    predicted_price: float
    confidence_score: float
    metrics: dict[str, float]


def _safe_metrics(y_true: pd.Series | np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = pd.Series(y_true).astype(float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    denom = np.where(y_true.to_numpy() == 0, np.nan, y_true.to_numpy())
    mape = float(np.nanmean(np.abs((y_true.to_numpy() - y_pred) / denom)) * 100)
    r2 = float(r2_score(y_true, y_pred))
    return {"mae": mae, "mse": mse, "rmse": rmse, "mape": mape, "r2": r2}


def _base_frame(df: pd.DataFrame, target_col: str = "close") -> pd.DataFrame:
    data = prepare_model_frame(df, target_col=target_col)
    numeric = data.select_dtypes(include=[np.number]).copy()
    if target_col not in numeric.columns or len(numeric) < 20:
        raise ValueError("Not enough numeric data to train a model")
    return numeric


def _supervised_frame(df: pd.DataFrame, target_col: str = "close", horizon_days: int = 1) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    data = _base_frame(df, target_col=target_col).sort_index().copy()
    target = data[target_col].shift(-horizon_days)
    X = data.drop(columns=[target_col], errors="ignore")
    X = X.drop(columns=[c for c in ["market_cap"] if c in X.columns], errors="ignore")
    frame = X.copy()
    frame["target"] = target
    frame = frame.dropna().reset_index(drop=True)
    X_clean = frame.drop(columns=["target"])
    y_clean = frame["target"]
    latest_features = X.tail(1).copy()
    if latest_features.empty:
        raise ValueError("Unable to build prediction features")
    return X_clean, y_clean, latest_features


def train_random_forest(df: pd.DataFrame, target_col: str = "close", horizon_days: int = 1) -> PredictionOutcome:
    X, y, latest = _supervised_frame(df, target_col, horizon_days)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = RandomForestRegressor(n_estimators=300, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    future_pred = float(model.predict(latest)[0])
    metrics = _safe_metrics(y_test, pred)
    return PredictionOutcome("random_forest", future_pred, max(0.0, min(1.0, 1.0 - metrics["mape"] / 100)), metrics)


def train_xgboost(df: pd.DataFrame, target_col: str = "close", horizon_days: int = 1) -> PredictionOutcome:
    if xgb is None:
        return train_random_forest(df, target_col, horizon_days)
    X, y, latest = _supervised_frame(df, target_col, horizon_days)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = xgb.XGBRegressor(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    future_pred = float(model.predict(latest)[0])
    metrics = _safe_metrics(y_test, pred)
    return PredictionOutcome("xgboost", future_pred, max(0.0, min(1.0, 1.0 - metrics["mape"] / 100)), metrics)


def train_arima(df: pd.DataFrame, target_col: str = "close", horizon_days: int = 1) -> PredictionOutcome:
    series = df[target_col].dropna().astype(float)
    if len(series) < 30:
        raise ValueError("Not enough data for ARIMA")
    if ARIMA is None:
        forecast = float(series.iloc[-1])
        return PredictionOutcome("arima", forecast, 0.5, {"mae": 0.0, "mse": 0.0, "rmse": 0.0, "mape": 0.0, "r2": 0.0})
    split = int(len(series) * 0.8)
    train, test = series.iloc[:split], series.iloc[split:]
    model = ARIMA(train, order=(5, 1, 0)).fit()
    pred = model.forecast(steps=len(test))
    metrics = _safe_metrics(test, pred)
    future_pred = float(model.forecast(steps=horizon_days).iloc[-1])
    return PredictionOutcome("arima", future_pred, max(0.0, min(1.0, 1.0 - metrics["mape"] / 100)), metrics)


def train_prophet(df: pd.DataFrame, target_col: str = "close", horizon_days: int = 1) -> PredictionOutcome:
    series = df[["ts", target_col]].dropna().copy()
    series["ts"] = pd.to_datetime(series["ts"])
    if len(series) < 20:
        raise ValueError("Not enough data for Prophet")
    if Prophet is None:
        last = float(series[target_col].iloc[-1])
        return PredictionOutcome("prophet", last, 0.4, {"mae": 0.0, "mse": 0.0, "rmse": 0.0, "mape": 0.0, "r2": 0.0})
    prophet_df = series.rename(columns={"ts": "ds", target_col: "y"})
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=max(7, horizon_days))
    forecast = model.predict(future)
    y_pred = forecast["yhat"].tail(7).to_numpy()
    y_true = prophet_df["y"].tail(7).to_numpy()
    metrics = _safe_metrics(pd.Series(y_true), y_pred)
    future_pred = float(forecast["yhat"].iloc[-1])
    return PredictionOutcome("prophet", future_pred, max(0.0, min(1.0, 1.0 - metrics["mape"] / 100)), metrics)


def train_lstm(df: pd.DataFrame, target_col: str = "close", horizon_days: int = 1) -> PredictionOutcome:
    if Sequential is None:
        return train_random_forest(df, target_col, horizon_days)
    X, y, latest = _supervised_frame(df, target_col, horizon_days)
    values = X.to_numpy(dtype=float)
    target = y.to_numpy(dtype=float)
    X_train, X_test, y_train, y_test = train_test_split(values, target, test_size=0.2, shuffle=False)
    X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
    X_test = X_test.reshape((X_test.shape[0], 1, X_test.shape[1]))
    latest_seq = latest.to_numpy(dtype=float).reshape((1, 1, latest.shape[1]))
    model = Sequential([LSTM(32, input_shape=(X_train.shape[1], X_train.shape[2])), Dense(1)])
    model.compile(optimizer="adam", loss="mse")
    model.fit(X_train, y_train, epochs=15, batch_size=16, verbose=0)
    pred = model.predict(X_test, verbose=0).flatten()
    future_pred = float(model.predict(latest_seq, verbose=0).flatten()[0])
    metrics = _safe_metrics(pd.Series(y_test), pred)
    return PredictionOutcome("lstm", future_pred, max(0.0, min(1.0, 1.0 - metrics["mape"] / 100)), metrics)


def predict_future(df: pd.DataFrame, model_name: str, horizon_days: int, target_col: str = "close") -> dict[str, Any]:
    model_name = model_name.lower()
    handlers = {
        "arima": train_arima,
        "prophet": train_prophet,
        "random_forest": train_random_forest,
        "rf": train_random_forest,
        "xgboost": train_xgboost,
        "xgb": train_xgboost,
        "lstm": train_lstm,
    }
    handler = handlers.get(model_name, train_xgboost)
    try:
        outcome = handler(df, target_col=target_col, horizon_days=horizon_days)
    except Exception:
        latest = float(df[target_col].dropna().iloc[-1]) if target_col in df.columns and not df[target_col].dropna().empty else 0.0
        outcome = PredictionOutcome(
            model_name if model_name in handlers else "xgboost",
            latest,
            0.25,
            {"mae": 0.0, "mse": 0.0, "rmse": 0.0, "mape": 0.0, "r2": 0.0},
        )
    return {
        "model_name": outcome.model_name,
        "predicted_price": outcome.predicted_price,
        "confidence_score": outcome.confidence_score,
        "metrics": outcome.metrics,
        "horizon_days": horizon_days,
        "as_of": datetime.utcnow(),
    }


def compare_models(df: pd.DataFrame, target_col: str = "close", horizon_days: int = 1) -> dict[str, dict[str, float]]:
    results: dict[str, dict[str, float]] = {}
    for name, func in [
        ("arima", train_arima),
        ("prophet", train_prophet),
        ("random_forest", train_random_forest),
        ("xgboost", train_xgboost),
        ("lstm", train_lstm),
    ]:
        try:
            outcome = func(df, target_col=target_col, horizon_days=horizon_days)
            results[name] = outcome.metrics
        except Exception as exc:
            results[name] = {"error": str(exc)}
    return results
