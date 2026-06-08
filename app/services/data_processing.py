from __future__ import annotations

import numpy as np
import pandas as pd


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
    df[numeric_cols] = df[numeric_cols].interpolate(method="linear", limit_direction="both")
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median(numeric_only=True))
    df = df.ffill().bfill()
    return df


def clip_outliers(df: pd.DataFrame, columns: list[str], lower_q: float = 0.01, upper_q: float = 0.99) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df:
            continue
        lo = df[col].quantile(lower_q)
        hi = df[col].quantile(upper_q)
        df[col] = df[col].clip(lo, hi)
    return df


def normalize_df(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df:
            min_v = df[col].min()
            max_v = df[col].max()
            span = max_v - min_v or 1.0
            df[col] = (df[col] - min_v) / span
    return df


def standardize_df(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df:
            mean = df[col].mean()
            std = df[col].std() or 1.0
            df[col] = (df[col] - mean) / std
    return df


def add_technical_features(df: pd.DataFrame, price_col: str = "close", volume_col: str = "volume") -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df = df.sort_values("ts") if "ts" in df.columns else df
    df["return_1d"] = df[price_col].pct_change()
    df["log_return"] = np.log(df[price_col]).diff()
    df["volatility_7d"] = df["return_1d"].rolling(7).std()
    df["ma_7"] = df[price_col].rolling(7).mean()
    df["ma_14"] = df[price_col].rolling(14).mean()
    df["rolling_std_7"] = df[price_col].rolling(7).std()
    df["momentum_7"] = df[price_col] - df[price_col].shift(7)
    df["volume_ma_7"] = df[volume_col].rolling(7).mean() if volume_col in df else np.nan
    df["lag_1"] = df[price_col].shift(1)
    df["lag_3"] = df[price_col].shift(3)
    df["lag_7"] = df[price_col].shift(7)
    delta = df[price_col].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    ema12 = df[price_col].ewm(span=12, adjust=False).mean()
    ema26 = df[price_col].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    return df


def prepare_model_frame(df: pd.DataFrame, target_col: str = "close") -> pd.DataFrame:
    df = fill_missing_values(df)
    df = clip_outliers(df, [c for c in df.columns if c not in {"ts", "symbol", "platform", "indicator_name"} and pd.api.types.is_numeric_dtype(df[c])])
    df = add_technical_features(df, price_col=target_col)
    df = df.dropna().reset_index(drop=True)
    return df
