"""add received dividends table

Revision ID: 004_received_dividends
Revises: 003_push_subscriptions
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '004_received_dividends'
down_revision: Union[str, None] = '003_push_subscriptions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'received_dividends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('shares', sa.Integer(), nullable=False),
        sa.Column('per_share', sa.Numeric(10, 4), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('ex_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_received_dividends_stock_id', 'received_dividends', ['stock_id'])
    op.create_index('ix_received_dividends_payment_date', 'received_dividends', ['payment_date'])


def downgrade() -> None:
    op.drop_index('ix_received_dividends_payment_date', table_name='received_dividends')
    op.drop_index('ix_received_dividends_stock_id', table_name='received_dividends')
    op.drop_table('received_dividends')
