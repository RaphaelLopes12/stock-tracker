from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import ReceivedDividend, Stock
from app.schemas.received_dividend import (
    DividendsByStock,
    DividendsByYear,
    DividendsSummary,
    ReceivedDividendCreate,
    ReceivedDividendResponse,
)

router = APIRouter(prefix="/dividends", tags=["dividends"])


@router.get("", response_model=list[ReceivedDividendResponse])
async def list_dividends(
    limit: int = 50,
    ticker: str | None = None,
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ReceivedDividend).options(selectinload(ReceivedDividend.stock))

    if ticker:
        query = query.join(Stock).where(Stock.ticker == ticker.upper())

    if year:
        query = query.where(func.extract('year', ReceivedDividend.payment_date) == year)

    query = query.order_by(ReceivedDividend.payment_date.desc()).limit(limit)

    result = await db.execute(query)
    dividends = result.scalars().all()

    return [
        ReceivedDividendResponse(
            id=d.id,
            stock_id=d.stock_id,
            ticker=d.stock.ticker,
            stock_name=d.stock.name,
            type=d.type,
            amount=d.amount,
            shares=d.shares,
            per_share=d.per_share,
            payment_date=d.payment_date,
            ex_date=d.ex_date,
            notes=d.notes,
            created_at=d.created_at,
        )
        for d in dividends
    ]


@router.post("", response_model=ReceivedDividendResponse, status_code=status.HTTP_201_CREATED)
async def create_dividend(
    dividend_in: ReceivedDividendCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Stock).where(Stock.ticker == dividend_in.ticker.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"Acao {dividend_in.ticker} nao encontrada",
        )

    per_share = dividend_in.amount / dividend_in.shares

    dividend = ReceivedDividend(
        stock_id=stock.id,
        type=dividend_in.type,
        amount=dividend_in.amount,
        shares=dividend_in.shares,
        per_share=per_share,
        payment_date=dividend_in.payment_date,
        ex_date=dividend_in.ex_date,
        notes=dividend_in.notes,
    )

    db.add(dividend)
    await db.commit()
    await db.refresh(dividend)

    return ReceivedDividendResponse(
        id=dividend.id,
        stock_id=dividend.stock_id,
        ticker=stock.ticker,
        stock_name=stock.name,
        type=dividend.type,
        amount=dividend.amount,
        shares=dividend.shares,
        per_share=dividend.per_share,
        payment_date=dividend.payment_date,
        ex_date=dividend.ex_date,
        notes=dividend.notes,
        created_at=dividend.created_at,
    )


@router.delete("/{dividend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dividend(
    dividend_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReceivedDividend).where(ReceivedDividend.id == dividend_id)
    )
    dividend = result.scalar_one_or_none()

    if not dividend:
        raise HTTPException(status_code=404, detail="Dividendo nao encontrado")

    await db.delete(dividend)
    await db.commit()


@router.get("/summary", response_model=DividendsSummary)
async def get_summary(
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    base_query = select(ReceivedDividend).options(selectinload(ReceivedDividend.stock))

    if year:
        base_query = base_query.where(func.extract('year', ReceivedDividend.payment_date) == year)

    result = await db.execute(base_query)
    dividends = result.scalars().all()

    total_amount = Decimal("0")
    by_stock_dict: dict[str, dict] = {}
    by_year_dict: dict[int, Decimal] = {}
    by_type_dict: dict[str, Decimal] = {}

    for d in dividends:
        total_amount += d.amount

        ticker = d.stock.ticker
        if ticker not in by_stock_dict:
            by_stock_dict[ticker] = {
                "ticker": ticker,
                "stock_name": d.stock.name,
                "total_amount": Decimal("0"),
                "count": 0,
            }
        by_stock_dict[ticker]["total_amount"] += d.amount
        by_stock_dict[ticker]["count"] += 1

        payment_year = d.payment_date.year
        by_year_dict[payment_year] = by_year_dict.get(payment_year, Decimal("0")) + d.amount

        by_type_dict[d.type] = by_type_dict.get(d.type, Decimal("0")) + d.amount

    by_stock = sorted(
        [DividendsByStock(**v) for v in by_stock_dict.values()],
        key=lambda x: x.total_amount,
        reverse=True,
    )

    by_year = sorted(
        [
            DividendsByYear(year=y, total_amount=amt, count=sum(1 for d in dividends if d.payment_date.year == y))
            for y, amt in by_year_dict.items()
        ],
        key=lambda x: x.year,
        reverse=True,
    )

    return DividendsSummary(
        total_amount=total_amount,
        total_count=len(dividends),
        by_stock=by_stock,
        by_year=by_year,
        by_type=by_type_dict,
    )
