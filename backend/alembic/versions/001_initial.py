"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-12-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Stocks
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("subsector", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker"),
    )

    # Fundamentals
    op.create_table(
        "fundamentals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("pl", sa.Numeric(10, 2), nullable=True),
        sa.Column("pvp", sa.Numeric(10, 2), nullable=True),
        sa.Column("psr", sa.Numeric(10, 2), nullable=True),
        sa.Column("ev_ebitda", sa.Numeric(10, 2), nullable=True),
        sa.Column("dividend_yield", sa.Numeric(5, 2), nullable=True),
        sa.Column("roe", sa.Numeric(5, 2), nullable=True),
        sa.Column("roic", sa.Numeric(5, 2), nullable=True),
        sa.Column("margin_liquid", sa.Numeric(5, 2), nullable=True),
        sa.Column("margin_ebit", sa.Numeric(5, 2), nullable=True),
        sa.Column("debt_ebitda", sa.Numeric(10, 2), nullable=True),
        sa.Column("current_liquidity", sa.Numeric(10, 2), nullable=True),
        sa.Column("market_cap", sa.Numeric(15, 2), nullable=True),
        sa.Column("net_revenue", sa.Numeric(15, 2), nullable=True),
        sa.Column("net_profit", sa.Numeric(15, 2), nullable=True),
        sa.Column("ebitda", sa.Numeric(15, 2), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_id", "date", name="uq_fundamental_stock_date"),
    )

    # Quotes
    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("datetime", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Numeric(10, 2), nullable=True),
        sa.Column("high", sa.Numeric(10, 2), nullable=True),
        sa.Column("low", sa.Numeric(10, 2), nullable=True),
        sa.Column("close", sa.Numeric(10, 2), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_id", "datetime", name="uq_quote_stock_datetime"),
    )

    # News
    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("url", sa.String(1000), nullable=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("collected_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("sentiment_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("sentiment_label", sa.String(20), nullable=True),
        sa.Column("is_relevant", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )

    # News-Stocks (N:N)
    op.create_table(
        "news_stocks",
        sa.Column("news_id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), server_default="1.0", nullable=False),
        sa.ForeignKeyConstraint(["news_id"], ["news.id"]),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("news_id", "stock_id"),
    )

    # Relevant Facts
    op.create_table(
        "relevant_facts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("protocol", sa.String(100), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("document_url", sa.String(1000), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("collected_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("protocol"),
    )

    # Dividends
    op.create_table(
        "dividends",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("value_per_share", sa.Numeric(10, 4), nullable=True),
        sa.Column("ex_date", sa.Date(), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("record_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_id", "type", "ex_date", name="uq_dividend_stock_type_date"),
    )

    # Alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("condition", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(), nullable=True),
        sa.Column("trigger_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cooldown_hours", sa.Integer(), server_default="24", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Alert History
    op.create_table(
        "alert_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("delivered", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Portfolio
    op.create_table(
        "portfolio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("average_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("first_buy_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("fees", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index("idx_fundamentals_stock_date", "fundamentals", ["stock_id", "date"])
    op.create_index("idx_quotes_stock_datetime", "quotes", ["stock_id", "datetime"])
    op.create_index("idx_news_published", "news", ["published_at"])
    op.create_index("idx_news_source", "news", ["source"])
    op.create_index("idx_relevant_facts_stock", "relevant_facts", ["stock_id", "published_at"])
    op.create_index("idx_dividends_stock_ex", "dividends", ["stock_id", "ex_date"])


def downgrade() -> None:
    op.drop_index("idx_dividends_stock_ex")
    op.drop_index("idx_relevant_facts_stock")
    op.drop_index("idx_news_source")
    op.drop_index("idx_news_published")
    op.drop_index("idx_quotes_stock_datetime")
    op.drop_index("idx_fundamentals_stock_date")

    op.drop_table("transactions")
    op.drop_table("portfolio")
    op.drop_table("alert_history")
    op.drop_table("alerts")
    op.drop_table("dividends")
    op.drop_table("relevant_facts")
    op.drop_table("news_stocks")
    op.drop_table("news")
    op.drop_table("quotes")
    op.drop_table("fundamentals")
    op.drop_table("stocks")
