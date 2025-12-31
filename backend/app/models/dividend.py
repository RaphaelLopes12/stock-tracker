from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.stock import Stock


class Dividend(Base):
    __tablename__ = "dividends"
    __table_args__ = (
        UniqueConstraint("stock_id", "type", "ex_date", name="uq_dividend_stock_type_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    type: Mapped[str | None] = mapped_column(String(50))  # dividendo, jcp, bonificacao
    value_per_share: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    ex_date: Mapped[date | None] = mapped_column(Date)
    payment_date: Mapped[date | None] = mapped_column(Date)
    record_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    stock: Mapped[Stock] = relationship(back_populates="dividends")

    def __repr__(self) -> str:
        return f"<Dividend {self.stock_id} {self.type} @ {self.ex_date}>"
