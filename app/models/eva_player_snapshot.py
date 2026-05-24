from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class EvaPlayerSnapshot(Base):
    """
    Snapshot des stats in-game d'un joueur sauvegardé à chaque synchro
    où les stats ont changé (nouvelles parties jouées).
    Permet de tracer la progression dans le temps.
    """
    __tablename__ = "eva_player_snapshots"

    id          = Column(Integer, primary_key=True)
    player_id   = Column(Integer, ForeignKey("eva_players.id"), nullable=False)
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now())

    season_number   = Column(Integer, nullable=True)
    game_count      = Column(Integer, nullable=True)
    game_victories  = Column(Integer, nullable=True)
    game_defeats    = Column(Integer, nullable=True)
    kills           = Column(Integer, nullable=True)
    deaths          = Column(Integer, nullable=True)
    assists         = Column(Integer, nullable=True)
    kd_ratio        = Column(Float,   nullable=True)
    game_time       = Column(Integer, nullable=True)  # secondes
