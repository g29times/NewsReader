"""Add vector_ids column to articles table"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('articles', sa.Column('vector_ids', sa.String, nullable=True))

def downgrade():
    op.drop_column('articles', 'vector_ids')
