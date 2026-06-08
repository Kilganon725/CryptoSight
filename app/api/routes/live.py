from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.services.data_service import sync_okx_market_data, sync_social_sentiment

router = APIRouter(prefix="/api", tags=["live"])


def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/ingest/live")
def ingest_live(symbol: str = "BTC", db: Session = Depends(get_db)):
    market = sync_okx_market_data(db, symbol=symbol)
    sentiment = sync_social_sentiment(db, symbol=symbol)
    return {
        "symbol": symbol,
        "market": market,
        "sentiment": sentiment,
    }


@router.get("/live/okx/ticker")
def live_okx_ticker(symbol: str = "BTC", db: Session = Depends(get_db)):
    result = sync_okx_market_data(db, symbol=symbol)
    return result

