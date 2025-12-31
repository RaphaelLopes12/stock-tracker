from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Stock
from app.schemas import StockCreate, StockResponse, StockUpdate

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockResponse])
async def list_stocks(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(Stock)
    if active_only:
        query = query.where(Stock.is_active == True)
    query = query.order_by(Stock.ticker)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{ticker}", response_model=StockResponse)
async def get_stock(ticker: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stock).where(Stock.ticker == ticker.upper()))
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    return stock


@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
async def create_stock(stock_in: StockCreate, db: AsyncSession = Depends(get_db)):
    # Check if already exists
    result = await db.execute(select(Stock).where(Stock.ticker == stock_in.ticker.upper()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Stock {stock_in.ticker} already exists")

    stock = Stock(
        ticker=stock_in.ticker.upper(),
        name=stock_in.name,
        sector=stock_in.sector,
        subsector=stock_in.subsector,
    )
    db.add(stock)
    await db.commit()
    await db.refresh(stock)

    return stock


@router.patch("/{ticker}", response_model=StockResponse)
async def update_stock(
    ticker: str,
    stock_in: StockUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Stock).where(Stock.ticker == ticker.upper()))
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    update_data = stock_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stock, field, value)

    await db.commit()
    await db.refresh(stock)

    return stock


@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock(ticker: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stock).where(Stock.ticker == ticker.upper()))
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    await db.delete(stock)
    await db.commit()
