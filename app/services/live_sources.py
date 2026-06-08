from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from app.core.config import get_settings


settings = get_settings()


def _utc_from_ms(value: str | int | float) -> datetime:
    return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc).replace(tzinfo=None)


def _sentiment_from_text(text: str) -> dict[str, float]:
    positive_words = {
        "bull", "bullish", "rally", "uptrend", "surge", "gain", "breakout", "pump", "buy", "strong", "positive",
        "optimistic", "support", "moon", "growth", "higher", "profit", "green",
    }
    negative_words = {
        "bear", "bearish", "dump", "crash", "sell", "weak", "negative", "fear", "panic", "loss", "downtrend",
        "drop", "fall", "liquidation", "red", "risk", "collapse", "scam",
    }
    tokens = [token.strip(".,!?:;()[]{}\"'").lower() for token in text.split()]
    pos = sum(1 for token in tokens if token in positive_words)
    neg = sum(1 for token in tokens if token in negative_words)
    total = max(len(tokens), 1)
    neutral = max(total - pos - neg, 0)
    denom = max(pos + neg + neutral, 1)
    positive = pos / denom
    negative = neg / denom
    neutral_ratio = neutral / denom
    return {
        "positive": float(positive),
        "neutral": float(neutral_ratio),
        "negative": float(negative),
        "sentiment_score": float(positive - negative),
    }


def fetch_okx_candles(inst_id: str | None = None, bar: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    inst_id = inst_id or settings.okx_instrument_id
    bar = bar or settings.okx_bar
    url = f"{settings.okx_base_url.rstrip('/')}/api/v5/market/candles"
    params = {"instId": inst_id, "bar": bar, "limit": str(limit)}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data", [])
    records = []
    for row in data:
        # OKX returns rows in reverse chronological order.
        ts, open_, high, low, close, volume, *rest = row
        records.append(
            {
                "ts": _utc_from_ms(ts),
                "open": float(open_),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume),
                "market_cap": None,
                "source": "okx",
            }
        )
    records.sort(key=lambda item: item["ts"])
    return records


def fetch_okx_ticker(inst_id: str | None = None) -> dict[str, Any]:
    inst_id = inst_id or settings.okx_instrument_id
    url = f"{settings.okx_base_url.rstrip('/')}/api/v5/market/ticker"
    response = requests.get(url, params={"instId": inst_id}, timeout=15)
    response.raise_for_status()
    data = response.json().get("data", [])
    if not data:
        raise ValueError("OKX ticker response did not include data")
    row = data[0]
    return {
        "inst_id": row.get("instId", inst_id),
        "last": float(row.get("last", 0.0)),
        "open24h": float(row.get("open24h", 0.0)),
        "high24h": float(row.get("high24h", 0.0)),
        "low24h": float(row.get("low24h", 0.0)),
        "vol24h": float(row.get("vol24h", 0.0)),
        "volCcy24h": float(row.get("volCcy24h", 0.0)) if row.get("volCcy24h") is not None else None,
        "ts": _utc_from_ms(row.get("ts")),
        "source": "okx",
    }


def fetch_x_recent_posts(query: str | None = None, max_results: int | None = None) -> list[dict[str, Any]]:
    if not settings.x_bearer_token:
        return []
    query = query or settings.x_search_query
    max_results = max_results or settings.x_search_limit
    url = "https://api.x.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {settings.x_bearer_token}"}
    params = {
        "query": query,
        "max_results": max(10, min(int(max_results), 100)),
        "tweet.fields": "created_at,author_id,lang,public_metrics",
    }
    response = requests.get(url, headers=headers, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    records: list[dict[str, Any]] = []
    for item in payload.get("data", []):
        metrics = item.get("public_metrics", {}) or {}
        records.append(
            {
                "platform": "twitter",
                "ts": datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).replace(tzinfo=None),
                "text": item.get("text", ""),
                "author_id": item.get("author_id"),
                "score_hint": float(metrics.get("like_count", 0) + metrics.get("retweet_count", 0)),
            }
        )
    return records


def _reddit_access_token() -> str | None:
    if not (settings.reddit_client_id and settings.reddit_client_secret):
        return None
    response = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(settings.reddit_client_id, settings.reddit_client_secret),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": settings.reddit_user_agent},
        timeout=20,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    return token


def fetch_reddit_posts(query: str | None = None, subreddit: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    token = _reddit_access_token()
    if not token:
        return []
    query = query or settings.reddit_search_query
    subreddit = subreddit or settings.reddit_search_subreddit
    limit = limit or settings.reddit_search_limit
    url = "https://oauth.reddit.com/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": settings.reddit_user_agent,
    }
    params = {
        "q": query,
        "limit": max(10, min(int(limit), 100)),
        "sort": "new",
        "t": "week",
        "restrict_sr": True,
        "sr_detail": False,
        "type": "link",
    }
    if subreddit:
        # Search within the configured subreddit to keep the signal relevant.
        url = f"https://oauth.reddit.com/r/{subreddit}/search"
    response = requests.get(url, headers=headers, params=params, timeout=20)
    response.raise_for_status()
    children = response.json().get("data", {}).get("children", [])
    records: list[dict[str, Any]] = []
    for child in children:
        data = child.get("data", {}) or {}
        created_utc = data.get("created_utc")
        ts = datetime.fromtimestamp(float(created_utc), tz=timezone.utc).replace(tzinfo=None) if created_utc else datetime.utcnow()
        title = data.get("title", "")
        selftext = data.get("selftext", "")
        text = (title + " " + selftext).strip()
        records.append(
            {
                "platform": "reddit",
                "ts": ts,
                "text": text,
                "author_id": data.get("author"),
                "score_hint": float(data.get("score", 0)),
            }
        )
    return records


def analyze_text_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    analyzed: list[dict[str, Any]] = []
    for record in records:
        sentiment = _sentiment_from_text(record.get("text", ""))
        analyzed.append({**record, **sentiment})
    return analyzed
