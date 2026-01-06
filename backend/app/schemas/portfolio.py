import datetime as dt
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ============ Transaction Schemas ============


class TransactionCreate(BaseModel):
    """Schema para criar uma nova transação."""

    ticker: str = Field(..., description="Ticker da ação (ex: WEGE3)")
    type: str = Field(..., pattern="^(buy|sell)$", description="Tipo: buy ou sell")
    quantity: int = Field(..., gt=0, description="Quantidade de ações")
    price: Decimal = Field(..., gt=0, description="Preço unitário")
    date: dt.date = Field(..., description="Data da operação")
    fees: Decimal = Field(default=Decimal("0"), ge=0, description="Taxas/corretagem")
    notes: Optional[str] = Field(default=None, description="Observações")


class TransactionResponse(BaseModel):
    """Schema de resposta para transação."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_id: int
    ticker: str
    stock_name: str
    type: str
    quantity: int
    price: Decimal
    total_value: Decimal
    date: dt.date
    fees: Decimal
    notes: Optional[str]
    created_at: dt.datetime


# ============ Portfolio Schemas ============


class PortfolioHolding(BaseModel):
    """Schema para um holding no portfolio."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_id: int
    ticker: str
    stock_name: str
    sector: Optional[str]
    quantity: int
    average_price: Decimal
    first_buy_date: Optional[dt.date]
    notes: Optional[str]

    # Dados calculados com cotação atual
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    total_invested: Optional[Decimal] = None
    gain_loss: Optional[Decimal] = None
    gain_loss_percent: Optional[float] = None
    change_today: Optional[float] = None


class PortfolioSummary(BaseModel):
    """Schema para resumo geral do portfolio."""

    total_invested: Decimal = Field(description="Total investido (preço médio * quantidade)")
    current_value: Decimal = Field(description="Valor atual de mercado")
    total_gain_loss: Decimal = Field(description="Lucro/Prejuízo total em R$")
    total_gain_loss_percent: float = Field(description="Lucro/Prejuízo total em %")
    holdings_count: int = Field(description="Número de ativos na carteira")
    best_performer: Optional[str] = Field(default=None, description="Ativo com maior valorização")
    worst_performer: Optional[str] = Field(default=None, description="Ativo com maior desvalorização")


class PortfolioResponse(BaseModel):
    """Schema de resposta completa do portfolio."""

    holdings: list[PortfolioHolding]
    summary: PortfolioSummary


# ============ Import Schemas ============


class ImportResultResponse(BaseModel):
    """Schema de resposta da importação de transações."""

    success_count: int = Field(description="Número de transações importadas com sucesso")
    error_count: int = Field(description="Número de linhas com erro")
    skipped_count: int = Field(description="Número de linhas ignoradas (duplicatas)")
    errors: list[str] = Field(default=[], description="Lista de erros encontrados")
    warnings: list[str] = Field(default=[], description="Avisos e informações")
    created_stocks: list[str] = Field(default=[], description="Ações criadas automaticamente")
