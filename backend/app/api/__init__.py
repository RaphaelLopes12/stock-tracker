from fastapi import APIRouter

from app.api.alerts import router as alerts_router
from app.api.fundamentals import router as fundamentals_router
from app.api.health import router as health_router
from app.api.news import router as news_router
from app.api.portfolio import router as portfolio_router
from app.api.quotes import router as quotes_router
from app.api.stocks import router as stocks_router

api_router = APIRouter(prefix="/api")

api_router.include_router(health_router)
api_router.include_router(stocks_router)
api_router.include_router(fundamentals_router)
api_router.include_router(quotes_router)
api_router.include_router(news_router)
api_router.include_router(alerts_router)
api_router.include_router(portfolio_router)
