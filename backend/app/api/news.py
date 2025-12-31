"""API endpoints para noticias do mercado."""

from fastapi import APIRouter

from app.services.news_service import get_market_news, get_stock_news, get_market_summary

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
async def list_news(limit: int = 20):
    """Retorna noticias do mercado financeiro."""
    news = await get_market_news(limit)
    return {"news": news, "count": len(news)}


@router.get("/stock/{ticker}")
async def get_news_for_stock(ticker: str, limit: int = 5):
    """Retorna noticias relacionadas a uma acao especifica."""
    news = await get_stock_news(ticker, limit)
    return {"ticker": ticker, "news": news, "count": len(news)}


@router.get("/summary")
async def market_summary():
    """Retorna resumo do mercado (indices principais)."""
    return await get_market_summary()
