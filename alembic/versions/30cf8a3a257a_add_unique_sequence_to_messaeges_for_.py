"""add unique sequence to messaeges for comparison

Revision ID: 30cf8a3a257a
Revises: 4ac90ce6a332
Create Date: 2026-06-24 11:23:47.567664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30cf8a3a257a'
down_revision: Union[str, Sequence[str], None] = '4ac90ce6a332'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SEQUENCE message_seq")
    op.add_column('messages', sa.Column('sequence', sa.Integer(), server_default=sa.text("nextval('message_seq')"), nullable=False))
    op.create_unique_constraint('uq_messages_sequence', 'messages', ['sequence'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_messages_sequence', 'messages', type_='unique')
    op.drop_column('messages', 'sequence')
    op.execute("DROP SEQUENCE message_seq")
