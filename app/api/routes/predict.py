from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from app.db.session import SessionLocal, init_db
from app.schemas.common import PredictionRequest, PredictionResponse, TrainResponse, ModelPerformanceItem
from app.services.data_service import get_price_history
from app.services.prediction import compare_models, predict_future

router = APIRouter(prefix="/api", tags=["prediction"])


def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest, db: Session = Depends(get_db)):
    prices = pd.DataFrame(get_price_history(db, symbol=payload.symbol, limit=365))
    if prices.empty:
        raise HTTPException(status_code=404, detail="No price data available")
    result = predict_future(prices, model_name=payload.model_name, horizon_days=payload.horizon_days)
    return {
        "symbol": payload.symbol,
        "model_name": result["model_name"],
        "horizon_days": payload.horizon_days,
        "predicted_price": result["predicted_price"],
        "confidence_score": result["confidence_score"],
        "metrics": result["metrics"],
        "as_of": result["as_of"],
    }


@router.post("/train", response_model=TrainResponse)
def train(payload: PredictionRequest, db: Session = Depends(get_db)):
    prices = pd.DataFrame(get_price_history(db, symbol=payload.symbol, limit=365))
    if prices.empty:
        raise HTTPException(status_code=404, detail="No price data available")
    metrics = compare_models(prices, horizon_days=payload.horizon_days)
    return {
        "trained_models": ["arima", "prophet", "random_forest", "xgboost", "lstm"],
        "metrics": metrics,
    }


@router.get("/model-performance", response_model=list[ModelPerformanceItem])
def model_performance(symbol: str = "BTC", horizon_days: int = 1, db: Session = Depends(get_db)):
    prices = pd.DataFrame(get_price_history(db, symbol=symbol, limit=365))
    metrics = compare_models(prices, horizon_days=horizon_days)
    items = []
    for model_name, metric in metrics.items():
        if "error" in metric:
            continue
        items.append(
            {
                "model_name": model_name,
                "mae": metric.get("mae", 0.0),
                "mse": metric.get("mse", 0.0),
                "rmse": metric.get("rmse", 0.0),
                "mape": metric.get("mape", 0.0),
                "r2": metric.get("r2", 0.0),
            }
        )
    return items
