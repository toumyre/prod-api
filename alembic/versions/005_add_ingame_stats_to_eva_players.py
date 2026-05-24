"""add ingame stats to eva_players

Revision ID: 005
Revises: 004
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('eva_players', sa.Column('eva_app_username', sa.String(), nullable=True))
    op.add_column('eva_players', sa.Column('game_count',       sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('game_victories',   sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('game_defeats',     sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('kills',            sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('deaths',           sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('assists',          sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('kd_ratio',         sa.Float(),   nullable=True))
    op.add_column('eva_players', sa.Column('game_time',        sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('best_kill_streak', sa.Integer(), nullable=True))
    op.add_column('eva_players', sa.Column('traveled_distance',sa.Float(),   nullable=True))


def downgrade():
    for col in ['eva_app_username','game_count','game_victories','game_defeats',
                'kills','deaths','assists','kd_ratio','game_time',
                'best_kill_streak','traveled_distance']:
        op.drop_column('eva_players', col)
