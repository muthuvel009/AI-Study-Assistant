"""add_embedding_to_document_chunks

Revision ID: 821a53af3025
Revises: bad45ffcc776
Create Date: 2026-09-23 09:43:30.557066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = '821a53af3025'
down_revision: Union[str, Sequence[str], None] = 'bad45ffcc776'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.add_column('document_chunks', sa.Column('embedding', pgvector.sqlalchemy.Vector(768), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('document_chunks', 'embedding')
