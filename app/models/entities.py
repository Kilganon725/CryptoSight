from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="viewer")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    logs = relationship("SystemLog", back_populates="user")


class CryptoPrice(Base):
    __tablename__ = "crypto_price"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), nullable=False, index=True)
    market = Column(String(32), nullable=False, default="spot", index=True)
    ts = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False, default=0.0)
    market_cap = Column(Float, nullable=True)
    source = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_crypto_symbol_ts", "symbol", "ts"),
        Index("idx_crypto_symbol_market_ts", "symbol", "market", "ts"),
    )


class MacroIndicator(Base):
    __tablename__ = "macro_indicator"

    id = Column(Integer, primary_key=True, index=True)
    indicator_name = Column(String(64), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=True)
    source = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_macro_name_ts", "indicator_name", "ts"),
    )


class SentimentData(Base):
    __tablename__ = "sentiment_data"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(32), nullable=False, index=True)
    symbol = Column(String(16), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    positive = Column(Float, nullable=False, default=0.0)
    neutral = Column(Float, nullable=False, default=0.0)
    negative = Column(Float, nullable=False, default=0.0)
    sentiment_score = Column(Float, nullable=False, default=0.0)
    raw_text = Column(Text, nullable=True)
    source = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_sentiment_symbol_ts", "symbol", "ts"),
    )


class PredictionResult(Base):
    __tablename__ = "prediction_result"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), nullable=False, index=True)
    model_name = Column(String(64), nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False)
    ts = Column(DateTime, nullable=False, index=True)
    predicted_price = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=True)
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_prediction_symbol_model_ts", "symbol", "model_name", "ts"),
    )


class FeatureImportance(Base):
    __tablename__ = "feature_importance"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), nullable=False, index=True)
    model_name = Column(String(64), nullable=False, index=True)
    feature_name = Column(String(128), nullable=False, index=True)
    importance = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    analysis_type = Column(String(32), nullable=False, default="feature_importance")
    ts = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_feature_symbol_model_rank", "symbol", "model_name", "rank"),
    )


class SystemLog(Base):
    __tablename__ = "system_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    level = Column(String(16), nullable=False, default="INFO")
    module = Column(String(64), nullable=False, default="system")
    message = Column(Text, nullable=False)
    extra = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="logs")
