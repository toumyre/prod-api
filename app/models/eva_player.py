from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class EvaPlayer(Base):
    """
    Stats par joueur ECLYPS, calculées depuis l'API EVA competitive.
    Mises à jour par le script scripts/sync_eva_players.py
    """
    __tablename__ = "eva_players"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, nullable=False, index=True)   # pseudo EVA (ex: "ECYxTitboyyy")
    eva_user_id = Column(String, unique=True, nullable=True)   # ID sur competitive.eva.gg
    tournaments_played = Column(Integer, default=0)            # Nb de tournois dans le roster
    matches_played = Column(Integer, default=0)                # Nb de matchs joués par l'équipe quand il était dans le roster
    wins = Column(Integer, default=0)                          # Victoires
    losses = Column(Integer, default=0)                        # Défaites
    win_rate = Column(Float, default=0.0)                      # Pourcentage de victoires (0.0 à 100.0)
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
