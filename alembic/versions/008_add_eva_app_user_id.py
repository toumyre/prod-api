"""add eva_app_user_id to eva_players

Revision ID: 008
Revises: 007
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('eva_players', sa.Column('eva_app_user_id', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('eva_players', 'eva_app_user_id')
