from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import CryptoPrice, MacroIndicator, SentimentData
from app.services.live_sources import (
    analyze_text_records,
    fetch_okx_candles,
    fetch_okx_instrument,
    fetch_okx_orderbook,
    fetch_okx_ticker,
    fetch_okx_trades,
    fetch_reddit_posts,
    fetch_x_recent_posts,
)

settings = get_settings()


def _symbol_from_inst_id(inst_id: str | None, fallback: str = "BTC") -> str:
    if not inst_id:
        return fallback
    return inst_id.split("-")[0].upper()


def _store_crypto_rows(db: Session, symbol: str, rows: list[dict]) -> int:
    inserted = 0
    for row in rows:
        exists = (
            db.query(CryptoPrice)
            .filter(CryptoPrice.symbol == symbol, CryptoPrice.ts == row["ts"])
            .first()
        )
        if exists:
            continue
        db.add(
            CryptoPrice(
                symbol=symbol,
                market="spot",
                ts=row["ts"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                market_cap=row.get("market_cap"),
                source=row.get("source", "okx"),
            )
        )
        inserted += 1
    if inserted:
        db.commit()
    return inserted


def _store_sentiment_rows(db: Session, symbol: str, rows: list[dict]) -> int:
    inserted = 0
    for row in rows:
        exists = (
            db.query(SentimentData)
            .filter(
                SentimentData.platform == row["platform"],
                SentimentData.symbol == symbol,
                SentimentData.ts == row["ts"],
                SentimentData.raw_text == row.get("text", ""),
            )
            .first()
        )
        if exists:
            continue
        db.add(
            SentimentData(
                platform=row["platform"],
                symbol=symbol,
                ts=row["ts"],
                positive=row["positive"],
                neutral=row["neutral"],
                negative=row["negative"],
                sentiment_score=row["sentiment_score"],
                raw_text=row.get("text", ""),
                source=row.get("source", row["platform"]),
            )
        )
        inserted += 1
    if inserted:
        db.commit()
    return inserted


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


def sync_okx_market_data(db: Session, symbol: str = "BTC", inst_id: str | None = None, limit: int = 365) -> dict:
    inst_id = inst_id or f"{symbol.upper()}-USDT"
    try:
        candles = fetch_okx_candles(inst_id=inst_id, bar=settings.okx_bar, limit=limit)
        inserted = _store_crypto_rows(db, symbol=symbol, rows=candles)
        ticker = fetch_okx_ticker(inst_id=inst_id)
        return {
            "ok": True,
            "source": "okx",
            "inst_id": ticker["inst_id"],
            "candles_fetched": len(candles),
            "candles_inserted": inserted,
            "ticker": ticker,
        }
    except Exception as exc:
        return {"ok": False, "source": "okx", "error": str(exc)}


def fetch_okx_history(symbol: str = "BTC", inst_id: str | None = None, bar: str | None = None, limit: int = 365) -> list[dict]:
    try:
        candles = fetch_okx_candles(inst_id=inst_id or f"{symbol.upper()}-USDT", bar=bar or settings.okx_bar, limit=limit)
        return [
            {
                "ts": row["ts"],
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
                "market_cap": row.get("market_cap"),
            }
            for row in candles
        ]
    except Exception:
        return []


def get_okx_instrument(inst_id: str) -> dict:
    try:
        return fetch_okx_instrument(inst_id=inst_id)
    except Exception as exc:
        return {"inst_id": inst_id, "error": str(exc)}


def get_okx_orderbook(inst_id: str, depth: int = 20) -> dict:
    try:
        return fetch_okx_orderbook(inst_id=inst_id, depth=depth)
    except Exception as exc:
        return {"inst_id": inst_id, "error": str(exc), "asks": [], "bids": []}


def get_okx_trades(inst_id: str, limit: int = 20) -> list[dict]:
    try:
        return fetch_okx_trades(inst_id=inst_id, limit=limit)
    except Exception:
        return []


def sync_social_sentiment(db: Session, symbol: str = "BTC") -> dict:
    results: dict[str, dict] = {}
    twitter_records = fetch_x_recent_posts()
    twitter_analyzed = analyze_text_records([{**record, "source": "x"} for record in twitter_records])
    results["twitter"] = {
        "fetched": len(twitter_analyzed),
        "inserted": _store_sentiment_rows(db, symbol, twitter_analyzed),
    }

    reddit_records = fetch_reddit_posts()
    reddit_analyzed = analyze_text_records([{**record, "source": "reddit"} for record in reddit_records])
    results["reddit"] = {
        "fetched": len(reddit_analyzed),
        "inserted": _store_sentiment_rows(db, symbol, reddit_analyzed),
    }
    return results


def get_price_history(db: Session, symbol: str = "BTC", limit: int = 365, bar: str | None = None, inst_id: str | None = None) -> list[dict]:
    bar = bar or settings.okx_bar
    inst_id = inst_id or f"{symbol.upper()}-USDT"
    if settings.live_data_enabled:
        live_rows = fetch_okx_history(symbol=symbol, inst_id=inst_id, bar=bar, limit=limit)
        if live_rows:
            if bar == settings.okx_bar:
                # Keep the default daily series persisted for model training and thesis figures.
                sync_okx_market_data(db, symbol=symbol, limit=max(limit, 365), inst_id=inst_id)
            return live_rows
    if db.query(CryptoPrice).filter(CryptoPrice.symbol == symbol).count() == 0:
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


def get_market_overview(db: Session, symbol: str = "BTC", inst_id: str | None = None) -> dict:
    inst_id = inst_id or f"{symbol.upper()}-USDT"
    live_snapshot = sync_okx_market_data(db, symbol=symbol, limit=10, inst_id=inst_id) if settings.live_data_enabled else {"ok": False}
    if db.query(CryptoPrice).filter(CryptoPrice.symbol == symbol).count() == 0:
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
    if live_snapshot.get("ok") and live_snapshot.get("ticker"):
        ticker = live_snapshot["ticker"]
        current_price = ticker["last"]
        change_24h = ((ticker["last"] - ticker["open24h"]) / ticker["open24h"] * 100) if ticker["open24h"] else change_24h
        volume_24h = ticker["vol24h"]
        market_cap = row.market_cap if row else None
        as_of = ticker["ts"]
        return {
        "symbol": symbol,
        "current_price": current_price,
            "change_24h": change_24h,
            "volume_24h": volume_24h,
            "market_cap": market_cap,
            "as_of": as_of,
        }
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
    if settings.live_data_enabled:
        sync_social_sentiment(db)
    if db.query(SentimentData).count() == 0:
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
            "raw_text": r.raw_text,
        }
        for r in reversed(rows)
    ]


def get_market_terminal_snapshot(inst_id: str) -> dict:
    return {
        "instrument": get_okx_instrument(inst_id),
        "orderbook": get_okx_orderbook(inst_id),
        "trades": get_okx_trades(inst_id),
    }
