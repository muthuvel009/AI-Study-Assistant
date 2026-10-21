"""add_phase4_learning_models

Revision ID: c19a53bf9100
Revises: 821a53af3025
Create Date: 2026-09-23 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c19a53bf9100'
down_revision: Union[str, Sequence[str], None] = '821a53af3025'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Quizzes table updates
    op.add_column('quizzes', sa.Column('document_id', sa.String(length=36), nullable=True))
    op.add_column('quizzes', sa.Column('difficulty', sa.String(length=50), server_default='Medium', nullable=False))
    op.create_foreign_key('fk_quizzes_document_id', 'quizzes', 'documents', ['document_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_quizzes_document_id'), 'quizzes', ['document_id'], unique=False)

    # Questions table updates
    op.add_column('questions', sa.Column('topic', sa.String(length=255), nullable=True))

    # Progress table updates
    op.add_column('progress', sa.Column('quiz_attempts', sa.Integer(), server_default='0', nullable=False))
    op.add_column('progress', sa.Column('latest_score', sa.Float(), nullable=True))
    op.add_column('progress', sa.Column('average_score', sa.Float(), nullable=True))
    op.add_column('progress', sa.Column('last_studied_at', sa.DateTime(timezone=True), nullable=True))

    # Recommendations table updates
    op.add_column('recommendations', sa.Column('recommendation_type', sa.String(length=50), server_default='Revision', nullable=False))
    op.add_column('recommendations', sa.Column('reason', sa.Text(), nullable=True))
    op.add_column('recommendations', sa.Column('action_label', sa.String(length=100), server_default='Practice Now', nullable=False))


def downgrade() -> None:
    op.drop_column('recommendations', 'action_label')
    op.drop_column('recommendations', 'reason')
    op.drop_column('recommendations', 'recommendation_type')

    op.drop_column('progress', 'last_studied_at')
    op.drop_column('progress', 'average_score')
    op.drop_column('progress', 'latest_score')
    op.drop_column('progress', 'quiz_attempts')

    op.drop_column('questions', 'topic')

    op.drop_index(op.f('ix_quizzes_document_id'), table_name='quizzes')
    op.drop_constraint('fk_quizzes_document_id', 'quizzes', type_='foreignkey')
    op.drop_column('quizzes', 'difficulty')
    op.drop_column('quizzes', 'document_id')
