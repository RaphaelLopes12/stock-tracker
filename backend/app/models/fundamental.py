from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.stock import Stock


class Fundamental(Base):
    __tablename__ = "fundamentals"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_fundamental_stock_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Preço
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Indicadores de valuation
    pl: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # P/L
    pvp: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # P/VP
    psr: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # P/Receita
    ev_ebitda: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Indicadores de rentabilidade
    dividend_yield: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    roe: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    roic: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    margin_liquid: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    margin_ebit: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    # Indicadores de endividamento
    debt_ebitda: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    current_liquidity: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Valores absolutos
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    net_revenue: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    net_profit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    ebitda: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # Metadados
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    stock: Mapped[Stock] = relationship(back_populates="fundamentals")

    def __repr__(self) -> str:
        return f"<Fundamental {self.stock_id} @ {self.date}>"
