"""add eva_player_snapshots table

Revision ID: 007
Revises: 006
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'eva_player_snapshots',
        sa.Column('id',             sa.Integer(),   primary_key=True),
        sa.Column('player_id',      sa.Integer(),   sa.ForeignKey('eva_players.id'), nullable=False),
        sa.Column('snapshot_at',    sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('season_number',  sa.Integer(),   nullable=True),
        sa.Column('game_count',     sa.Integer(),   nullable=True),
        sa.Column('game_victories', sa.Integer(),   nullable=True),
        sa.Column('game_defeats',   sa.Integer(),   nullable=True),
        sa.Column('kills',          sa.Integer(),   nullable=True),
        sa.Column('deaths',         sa.Integer(),   nullable=True),
        sa.Column('assists',        sa.Integer(),   nullable=True),
        sa.Column('kd_ratio',       sa.Float(),     nullable=True),
        sa.Column('game_time',      sa.Integer(),   nullable=True),
    )
    op.create_index('ix_eva_player_snapshots_player_id', 'eva_player_snapshots', ['player_id'])


def downgrade():
    op.drop_index('ix_eva_player_snapshots_player_id')
    op.drop_table('eva_player_snapshots')
