from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.stock import Stock


class ReceivedDividend(Base):
    __tablename__ = "received_dividends"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    shares: Mapped[int] = mapped_column(Integer, nullable=False)
    per_share: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    ex_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stock: Mapped[Stock] = relationship(back_populates="received_dividends")

    def __repr__(self) -> str:
        return f"<ReceivedDividend {self.stock_id} {self.type} R${self.amount}>"
