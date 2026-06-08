from app.api.routes.factors import router as factors_router
from app.api.routes.market import router as market_router
from app.api.routes.predict import router as predict_router
from app.api.routes.system import router as system_router

routers = [market_router, factors_router, predict_router, system_router]
