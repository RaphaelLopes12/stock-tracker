"""add price targets and notes to stocks

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('stocks', sa.Column('target_buy_price', sa.Numeric(10, 2), nullable=True))
    op.add_column('stocks', sa.Column('target_sell_price', sa.Numeric(10, 2), nullable=True))
    op.add_column('stocks', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('stocks', 'notes')
    op.drop_column('stocks', 'target_sell_price')
    op.drop_column('stocks', 'target_buy_price')
