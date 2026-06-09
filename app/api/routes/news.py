from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.schemas.common import NewsItem
from app.services.data_service import get_news_data

router = APIRouter(prefix="/api", tags=["news"])


def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/news", response_model=list[NewsItem])
def news(limit: int = 25, db: Session = Depends(get_db)):
    return get_news_data(limit=limit)

