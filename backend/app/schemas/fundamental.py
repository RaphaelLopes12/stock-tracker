from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FundamentalBase(BaseModel):
    price: Decimal | None = None
    pl: Decimal | None = None
    pvp: Decimal | None = None
    psr: Decimal | None = None
    dividend_yield: Decimal | None = None
    roe: Decimal | None = None
    roic: Decimal | None = None
    margin_liquid: Decimal | None = None
    margin_ebit: Decimal | None = None
    debt_ebitda: Decimal | None = None
    current_liquidity: Decimal | None = None
    ev_ebitda: Decimal | None = None
    market_cap: Decimal | None = None
    net_revenue: Decimal | None = None
    net_profit: Decimal | None = None
    ebitda: Decimal | None = None


class FundamentalCreate(FundamentalBase):
    stock_id: int
    date: date
    source: str | None = None
    raw_data: dict | None = None


class FundamentalResponse(FundamentalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_id: int
    date: date
    source: str | None
    created_at: datetime


class FundamentalWithStock(FundamentalResponse):
    ticker: str
    stock_name: str
