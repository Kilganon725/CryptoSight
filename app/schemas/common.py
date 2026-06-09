from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class HistoryPoint(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    market_cap: float | None = None


class MarketOverview(BaseModel):
    symbol: str
    current_price: float
    change_24h: float
    volume_24h: float
    market_cap: float | None = None
    as_of: datetime


class MacroPoint(BaseModel):
    indicator_name: str
    ts: datetime
    value: float
    unit: str | None = None


class SentimentPoint(BaseModel):
    platform: str
    ts: datetime
    positive: float
    neutral: float
    negative: float
    sentiment_score: float


class NewsItem(BaseModel):
    platform: str
    ts: datetime
    title: str
    url: str
    source_name: str | None = None
    summary: str | None = None
    text: str | None = None
    positive: float
    neutral: float
    negative: float
    sentiment_score: float


class FactorResult(BaseModel):
    correlations: dict[str, Any]
    causality: dict[str, Any]
    feature_importance: list[dict[str, Any]]
    shap_summary: list[dict[str, Any]]


class PredictionRequest(BaseModel):
    symbol: str = "BTC"
    inst_id: str | None = None
    model_name: str = Field(default="xgboost")
    horizon_days: int = Field(default=7, ge=1, le=30)


class PredictionResponse(BaseModel):
    symbol: str
    model_name: str
    horizon_days: int
    predicted_price: float
    confidence_score: float
    metrics: dict[str, float]
    as_of: datetime


class TrainResponse(BaseModel):
    trained_models: list[str]
    metrics: dict[str, dict[str, float]]


class ModelPerformanceItem(BaseModel):
    model_name: str
    mae: float
    mse: float
    rmse: float
    mape: float
    r2: float
