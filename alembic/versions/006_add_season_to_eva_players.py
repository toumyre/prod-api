"""add season fields to eva_players

Revision ID: 006
Revises: 005
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('eva_players', sa.Column('season_id',     sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('season_number', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('eva_players', 'season_number')
    op.drop_column('eva_players', 'season_id')
