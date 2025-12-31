from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Fundamental, Stock
from app.schemas import FundamentalResponse

router = APIRouter(prefix="/fundamentals", tags=["fundamentals"])


@router.get("/{ticker}", response_model=list[FundamentalResponse])
async def get_fundamentals(
    ticker: str,
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
):
    # Get stock
    result = await db.execute(select(Stock).where(Stock.ticker == ticker.upper()))
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Get fundamentals
    query = (
        select(Fundamental)
        .where(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.date.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{ticker}/latest", response_model=FundamentalResponse)
async def get_latest_fundamental(ticker: str, db: AsyncSession = Depends(get_db)):
    # Get stock
    result = await db.execute(select(Stock).where(Stock.ticker == ticker.upper()))
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Get latest fundamental
    query = (
        select(Fundamental)
        .where(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.date.desc())
        .limit(1)
    )

    result = await db.execute(query)
    fundamental = result.scalar_one_or_none()

    if not fundamental:
        raise HTTPException(status_code=404, detail=f"No fundamentals found for {ticker}")

    return fundamental


@router.get("/{ticker}/compare", response_model=dict)
async def compare_fundamentals(
    ticker: str,
    date1: date,
    date2: date,
    db: AsyncSession = Depends(get_db),
):
    """Compare fundamentals between two dates."""
    result = await db.execute(select(Stock).where(Stock.ticker == ticker.upper()))
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Get fundamentals for both dates
    result1 = await db.execute(
        select(Fundamental).where(Fundamental.stock_id == stock.id, Fundamental.date == date1)
    )
    result2 = await db.execute(
        select(Fundamental).where(Fundamental.stock_id == stock.id, Fundamental.date == date2)
    )

    fund1 = result1.scalar_one_or_none()
    fund2 = result2.scalar_one_or_none()

    if not fund1 or not fund2:
        raise HTTPException(status_code=404, detail="Fundamentals not found for one or both dates")

    # Calculate differences
    comparison = {
        "ticker": ticker,
        "date1": date1,
        "date2": date2,
        "metrics": {},
    }

    metrics = ["pl", "pvp", "dividend_yield", "roe", "roic", "debt_ebitda", "price"]
    for metric in metrics:
        val1 = getattr(fund1, metric)
        val2 = getattr(fund2, metric)
        if val1 is not None and val2 is not None:
            change = float(val2 - val1)
            change_pct = (change / float(val1) * 100) if float(val1) != 0 else None
            comparison["metrics"][metric] = {
                "date1_value": float(val1),
                "date2_value": float(val2),
                "change": change,
                "change_percent": change_pct,
            }

    return comparison
