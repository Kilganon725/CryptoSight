from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.schemas.common import HistoryPoint, MacroPoint, MarketOverview, SentimentPoint
from app.services.data_service import get_macro_data, get_market_overview, get_price_history, get_sentiment_data

router = APIRouter(prefix="/api", tags=["market"])


def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/btc/history", response_model=list[HistoryPoint])
def btc_history(limit: int = 365, bar: str = "1D", db: Session = Depends(get_db)):
    return get_price_history(db, symbol="BTC", limit=limit, bar=bar)


@router.get("/market/overview", response_model=MarketOverview)
def market_overview(db: Session = Depends(get_db)):
    return get_market_overview(db, symbol="BTC")


@router.get("/macro", response_model=list[MacroPoint])
def macro(db: Session = Depends(get_db)):
    return get_macro_data(db)


@router.get("/sentiment", response_model=list[SentimentPoint])
def sentiment(db: Session = Depends(get_db)):
    return get_sentiment_data(db)
