from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.schemas.common import HistoryPoint, MacroPoint, MarketOverview, SentimentPoint
from app.services.data_service import (
    get_macro_data,
    get_market_overview,
    get_okx_instrument,
    get_okx_orderbook,
    get_okx_trades,
    get_price_history,
    get_sentiment_data,
)

router = APIRouter(prefix="/api", tags=["market"])


def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/btc/history", response_model=list[HistoryPoint])
def btc_history(limit: int = 365, bar: str = "1D", inst_id: str = "BTC-USDT", db: Session = Depends(get_db)):
    symbol = inst_id.split("-")[0].upper()
    return get_price_history(db, symbol=symbol, limit=limit, bar=bar, inst_id=inst_id)


@router.get("/market/overview", response_model=MarketOverview)
def market_overview(inst_id: str = "BTC-USDT", db: Session = Depends(get_db)):
    symbol = inst_id.split("-")[0].upper()
    return get_market_overview(db, symbol=symbol, inst_id=inst_id)


@router.get("/macro", response_model=list[MacroPoint])
def macro(db: Session = Depends(get_db)):
    return get_macro_data(db)


@router.get("/sentiment", response_model=list[SentimentPoint])
def sentiment(db: Session = Depends(get_db)):
    return get_sentiment_data(db)


@router.get("/market/instrument")
def market_instrument(inst_id: str = "BTC-USDT", db: Session = Depends(get_db)):
    return get_okx_instrument(inst_id)


@router.get("/market/orderbook")
def market_orderbook(inst_id: str = "BTC-USDT", depth: int = 20, db: Session = Depends(get_db)):
    return get_okx_orderbook(inst_id, depth=depth)


@router.get("/market/trades")
def market_trades(inst_id: str = "BTC-USDT", limit: int = 20, db: Session = Depends(get_db)):
    return get_okx_trades(inst_id, limit=limit)
