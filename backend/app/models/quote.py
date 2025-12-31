from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.stock import Stock


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("stock_id", "datetime", name="uq_quote_stock_datetime"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    open: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    high: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    low: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    close: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    volume: Mapped[int | None] = mapped_column(BigInteger)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    stock: Mapped[Stock] = relationship(back_populates="quotes")

    def __repr__(self) -> str:
        return f"<Quote {self.stock_id} @ {self.datetime}>"
