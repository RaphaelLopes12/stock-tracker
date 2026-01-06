from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StockBase(BaseModel):
    ticker: str
    name: str
    sector: str | None = None
    subsector: str | None = None


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    name: str | None = None
    sector: str | None = None
    subsector: str | None = None
    is_active: bool | None = None
    target_buy_price: Decimal | None = None
    target_sell_price: Decimal | None = None
    notes: str | None = None


class StockResponse(StockBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    target_buy_price: Decimal | None = None
    target_sell_price: Decimal | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class StockWithPrice(StockResponse):
    current_price: float | None = None
    price_change: float | None = None
    price_change_percent: float | None = None
