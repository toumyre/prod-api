"""add eclyps team tables

Revision ID: 004
Revises: 003_add_matches_table
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003_add_matches_table'
branch_labels = None
depends_on = None


def upgrade():
    # Table des comptes joueurs ECLYPS
    op.create_table(
        'eclyps_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('player_name', sa.String(), nullable=True),
        sa.Column('eva_user_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_eclyps_users_id', 'eclyps_users', ['id'])
    op.create_index('ix_eclyps_users_username', 'eclyps_users', ['username'], unique=True)
    op.create_index('ix_eclyps_users_eva_user_id', 'eclyps_users', ['eva_user_id'])

    # Table des stats joueurs (sync depuis API EVA)
    op.create_table(
        'eva_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_name', sa.String(), nullable=False),
        sa.Column('eva_user_id', sa.String(), nullable=True),
        sa.Column('tournaments_played', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('matches_played', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('wins', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('losses', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('win_rate', sa.Float(), nullable=True, server_default='0'),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_eva_players_id', 'eva_players', ['id'])
    op.create_index('ix_eva_players_player_name', 'eva_players', ['player_name'])
    op.create_index('ix_eva_players_eva_user_id', 'eva_players', ['eva_user_id'], unique=True)


def downgrade():
    op.drop_table('eva_players')
    op.drop_table('eclyps_users')
