from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.entities import CryptoPrice, MacroIndicator, SentimentData


def seed_demo_data(db: Session, symbol: str = "BTC", days: int = 365) -> None:
    existing = db.query(CryptoPrice).filter(CryptoPrice.symbol == symbol).count()
    if existing:
        return
    base = 50000.0
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    rng = np.random.default_rng(42)
    prices = []
    macro_names = ["DXY", "GOLD", "NASDAQ", "SP500", "CPI", "FED_FUNDS", "VIX"]
    for i in range(days):
        ts = now - timedelta(days=days - i)
        drift = np.sin(i / 30.0) * 500 + i * 8
        close = base + drift + rng.normal(0, 1200)
        open_price = close + rng.normal(0, 250)
        high = max(open_price, close) + abs(rng.normal(0, 300))
        low = min(open_price, close) - abs(rng.normal(0, 300))
        volume = abs(rng.normal(8e8, 2e8))
        market_cap = close * 19_000_000
        prices.append(
            CryptoPrice(
                symbol=symbol,
                market="spot",
                ts=ts,
                open=float(open_price),
                high=float(high),
                low=float(low),
                close=float(close),
                volume=float(volume),
                market_cap=float(market_cap),
                source="demo",
            )
        )
        for name in macro_names:
            value = float(rng.normal(100, 20)) if name != "VIX" else float(abs(rng.normal(20, 5)))
            db.add(MacroIndicator(indicator_name=name, ts=ts, value=value, unit="index", source="demo"))
        for platform in ["twitter", "reddit", "news"]:
            positive = float(np.clip(rng.normal(0.4, 0.15), 0, 1))
            neutral = float(np.clip(rng.normal(0.4, 0.1), 0, 1))
            negative = float(np.clip(1 - positive - neutral, 0, 1))
            sentiment_score = positive - negative
            db.add(
                SentimentData(
                    platform=platform,
                    symbol=symbol,
                    ts=ts,
                    positive=positive,
                    neutral=neutral,
                    negative=negative,
                    sentiment_score=sentiment_score,
                    raw_text=f"Demo {platform} sentiment for {symbol}",
                    source="demo",
                )
            )
    db.add_all(prices)
    db.commit()


def get_price_history(db: Session, symbol: str = "BTC", limit: int = 365) -> list[dict]:
    seed_demo_data(db, symbol=symbol, days=max(limit, 365))
    rows = (
        db.query(CryptoPrice)
        .filter(CryptoPrice.symbol == symbol)
        .order_by(desc(CryptoPrice.ts))
        .limit(limit)
        .all()
    )
    rows = list(reversed(rows))
    return [
        {
            "ts": r.ts,
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
            "market_cap": r.market_cap,
        }
        for r in rows
    ]


def get_market_overview(db: Session, symbol: str = "BTC") -> dict:
    seed_demo_data(db, symbol=symbol, days=365)
    row = (
        db.query(CryptoPrice)
        .filter(CryptoPrice.symbol == symbol)
        .order_by(desc(CryptoPrice.ts))
        .first()
    )
    prev = (
        db.query(CryptoPrice)
        .filter(CryptoPrice.symbol == symbol)
        .order_by(desc(CryptoPrice.ts))
        .offset(1)
        .first()
    )
    change_24h = ((row.close - prev.close) / prev.close * 100) if row and prev else 0.0
    return {
        "symbol": symbol,
        "current_price": row.close,
        "change_24h": change_24h,
        "volume_24h": row.volume,
        "market_cap": row.market_cap,
        "as_of": row.ts,
    }


def get_macro_data(db: Session) -> list[dict]:
    seed_demo_data(db)
    rows = db.query(MacroIndicator).order_by(desc(MacroIndicator.ts)).limit(500).all()
    return [
        {"indicator_name": r.indicator_name, "ts": r.ts, "value": r.value, "unit": r.unit}
        for r in reversed(rows)
    ]


def get_sentiment_data(db: Session) -> list[dict]:
    seed_demo_data(db)
    rows = db.query(SentimentData).order_by(desc(SentimentData.ts)).limit(500).all()
    return [
        {
            "platform": r.platform,
            "ts": r.ts,
            "positive": r.positive,
            "neutral": r.neutral,
            "negative": r.negative,
            "sentiment_score": r.sentiment_score,
        }
        for r in reversed(rows)
    ]
