from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.stock import Stock


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int | None] = mapped_column(ForeignKey("stocks.id"))
    name: Mapped[str | None] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    cooldown_hours: Mapped[int] = mapped_column(Integer, default=24)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    stock: Mapped[Stock | None] = relationship(back_populates="alerts")
    history: Mapped[list[AlertHistory]] = relationship(back_populates="alert")

    def __repr__(self) -> str:
        return f"<Alert {self.id}: {self.type}>"


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    message: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict | None] = mapped_column(JSONB)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    alert: Mapped[Alert] = relationship(back_populates="history")

    def __repr__(self) -> str:
        return f"<AlertHistory {self.id} @ {self.triggered_at}>"
