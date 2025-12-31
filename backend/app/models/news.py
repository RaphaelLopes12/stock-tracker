from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.stock import Stock


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1000), unique=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    collected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Campos de IA (opcionais)
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    sentiment_label: Mapped[str | None] = mapped_column(String(20))
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=True)

    raw_data: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    stocks: Mapped[list[NewsStock]] = relationship(back_populates="news")

    def __repr__(self) -> str:
        return f"<News {self.id}: {self.title[:50]}>"


class NewsStock(Base):
    __tablename__ = "news_stocks"

    news_id: Mapped[int] = mapped_column(ForeignKey("news.id"), primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), primary_key=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.0)

    # Relationships
    news: Mapped[News] = relationship(back_populates="stocks")
    stock: Mapped[Stock] = relationship()


class RelevantFact(Base):
    __tablename__ = "relevant_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    protocol: Mapped[str | None] = mapped_column(String(100), unique=True)
    category: Mapped[str | None] = mapped_column(String(100))
    subject: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    document_url: Mapped[str | None] = mapped_column(String(1000))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    collected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    raw_data: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    stock: Mapped[Stock] = relationship()

    def __repr__(self) -> str:
        return f"<RelevantFact {self.protocol}>"
