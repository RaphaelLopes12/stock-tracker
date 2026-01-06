from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.dividend import Dividend
    from app.models.fundamental import Fundamental
    from app.models.portfolio import Portfolio
    from app.models.quote import Quote


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100))
    subsector: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Price targets (user-defined)
    target_buy_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    target_sell_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Investment thesis / notes
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    fundamentals: Mapped[list[Fundamental]] = relationship(back_populates="stock")
    quotes: Mapped[list[Quote]] = relationship(back_populates="stock")
    dividends: Mapped[list[Dividend]] = relationship(back_populates="stock")
    alerts: Mapped[list[Alert]] = relationship(back_populates="stock")
    portfolio_items: Mapped[list[Portfolio]] = relationship(back_populates="stock")

    def __repr__(self) -> str:
        return f"<Stock {self.ticker}>"
