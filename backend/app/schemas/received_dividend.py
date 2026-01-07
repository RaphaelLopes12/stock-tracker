import datetime as dt
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReceivedDividendCreate(BaseModel):
    ticker: str = Field(..., description="Ticker da acao")
    type: str = Field(..., pattern="^(dividendo|jcp|bonificacao)$", description="Tipo: dividendo, jcp ou bonificacao")
    amount: Decimal = Field(..., gt=0, description="Valor total recebido")
    shares: int = Field(..., gt=0, description="Quantidade de acoes na data-com")
    payment_date: dt.date = Field(..., description="Data do pagamento")
    ex_date: Optional[dt.date] = Field(default=None, description="Data-com (ex-dividendo)")
    notes: Optional[str] = Field(default=None, description="Observacoes")


class ReceivedDividendResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_id: int
    ticker: str
    stock_name: str
    type: str
    amount: Decimal
    shares: int
    per_share: Decimal
    payment_date: dt.date
    ex_date: Optional[dt.date]
    notes: Optional[str]
    created_at: dt.datetime


class DividendsByStock(BaseModel):
    ticker: str
    stock_name: str
    total_amount: Decimal
    count: int


class DividendsByYear(BaseModel):
    year: int
    total_amount: Decimal
    count: int


class DividendsSummary(BaseModel):
    total_amount: Decimal = Field(description="Total de dividendos recebidos")
    total_count: int = Field(description="Numero total de pagamentos")
    by_stock: list[DividendsByStock] = Field(description="Totais por acao")
    by_year: list[DividendsByYear] = Field(description="Totais por ano")
    by_type: dict[str, Decimal] = Field(description="Totais por tipo")
