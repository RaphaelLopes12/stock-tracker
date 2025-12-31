from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Stock
from app.services.quote_service import get_quote, get_quotes_batch, analyze_stock
from app.services.history_service import get_history

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("")
async def get_all_quotes(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Busca cotações de todas as ações cadastradas."""
    # Buscar ações ativas
    result = await db.execute(
        select(Stock)
        .where(Stock.is_active == True)
        .order_by(Stock.ticker)
        .limit(limit)
    )
    stocks = result.scalars().all()

    if not stocks:
        return []

    # Buscar cotações
    tickers = [s.ticker for s in stocks]
    quotes = await get_quotes_batch(tickers)

    # Combinar dados
    response = []
    for stock in stocks:
        quote = quotes.get(stock.ticker)
        response.append({
            "id": stock.id,
            "ticker": stock.ticker,
            "name": stock.name,
            "sector": stock.sector,
            "quote": quote,
        })

    return response


@router.get("/sector/{sector}")
async def get_quotes_by_sector(
    sector: str,
    db: AsyncSession = Depends(get_db),
):
    """Busca cotações de ações de um setor específico."""
    result = await db.execute(
        select(Stock)
        .where(Stock.sector == sector, Stock.is_active == True)
        .order_by(Stock.ticker)
    )
    stocks = result.scalars().all()

    if not stocks:
        raise HTTPException(status_code=404, detail=f"Nenhuma ação encontrada no setor {sector}")

    tickers = [s.ticker for s in stocks]
    quotes = await get_quotes_batch(tickers)

    response = []
    for stock in stocks:
        quote = quotes.get(stock.ticker)
        if quote:
            analysis = analyze_stock(quote)
            response.append({
                "id": stock.id,
                "ticker": stock.ticker,
                "name": stock.name,
                "quote": quote,
                "analysis": analysis,
            })

    return response


@router.get("/{ticker}/history")
async def get_stock_history(ticker: str, period: str = "6mo"):
    """Busca histórico de preços de uma ação.

    Períodos válidos: 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    """
    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Período inválido. Use um dos: {', '.join(valid_periods)}"
        )

    history = await get_history(ticker.upper(), period)

    if not history:
        raise HTTPException(status_code=404, detail=f"Não foi possível obter histórico para {ticker}")

    return {
        "ticker": ticker.upper(),
        "period": period,
        "data": history,
        "count": len(history),
    }


@router.get("/{ticker}/analysis")
async def get_stock_analysis(ticker: str):
    """Busca cotação e análise se compensa comprar."""
    quote = await get_quote(ticker.upper())

    if not quote:
        raise HTTPException(status_code=404, detail=f"Não foi possível obter cotação para {ticker}")

    analysis = analyze_stock(quote)
    return {
        "quote": quote,
        "analysis": analysis,
    }


@router.get("/{ticker}")
async def get_stock_quote(ticker: str):
    """Busca cotação em tempo real de uma ação."""
    quote = await get_quote(ticker.upper())

    if not quote:
        raise HTTPException(status_code=404, detail=f"Não foi possível obter cotação para {ticker}")

    return quote
