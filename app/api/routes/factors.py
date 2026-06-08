from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.schemas.common import FactorResult
from app.services.analysis import correlation_analysis, granger_causality_analysis, random_forest_feature_importance, shap_summary
from app.services.data_service import get_macro_data, get_price_history, get_sentiment_data
from app.services.data_processing import add_technical_features
import pandas as pd

router = APIRouter(prefix="/api", tags=["factors"])


def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/factors")
def factors(db: Session = Depends(get_db)):
    prices = pd.DataFrame(get_price_history(db, symbol="BTC", limit=365))
    macro = pd.DataFrame(get_macro_data(db))
    sentiment = pd.DataFrame(get_sentiment_data(db))

    if not prices.empty:
        prices = add_technical_features(prices)
        prices = prices.dropna().reset_index(drop=True)
    if not macro.empty:
        macro_pivot = macro.pivot_table(index="ts", columns="indicator_name", values="value", aggfunc="mean")
    else:
        macro_pivot = pd.DataFrame()
    if not sentiment.empty:
        sentiment_pivot = sentiment.groupby("ts")["sentiment_score"].mean().to_frame("sentiment_score")
    else:
        sentiment_pivot = pd.DataFrame()

    merged = prices.copy()
    if not macro_pivot.empty:
        merged = merged.merge(macro_pivot.reset_index(), on="ts", how="left")
    if not sentiment_pivot.empty:
        merged = merged.merge(sentiment_pivot.reset_index(), on="ts", how="left")
    merged = merged.ffill().bfill()

    columns = [c for c in merged.columns if c not in {"ts"}]
    correlations = correlation_analysis(merged, columns)
    causality = granger_causality_analysis(merged, target="close", candidates=[c for c in columns if c != "close"])
    fi = random_forest_feature_importance(merged, target="close")
    shap_data = shap_summary(merged, target="close")
    return {
        "correlations": correlations,
        "causality": causality,
        "feature_importance": fi,
        "shap_summary": shap_data,
    }
