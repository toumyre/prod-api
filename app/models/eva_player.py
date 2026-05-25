from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class EvaPlayer(Base):
    """
    Stats par joueur ECLYPS.
    - Données compétitives : sync depuis competitive.eva.gg (API Toornament)
    - Données in-game     : sync depuis api.eva.gg (API GraphQL)
    """
    __tablename__ = "eva_players"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, nullable=False, index=True)   # pseudo affiché (ex: "ECYxTitboyyy")
    eva_user_id = Column(String, nullable=True)                # ID sur competitive.eva.gg (Toornament)
    eva_app_username = Column(String, nullable=True)           # Username app EVA (ex: "ECYxToumyre#586100")
    eva_app_user_id  = Column(Integer, nullable=True)          # user.id EVA app (pour l'historique des parties)

    # ── Stats compétitives (API Toornament) ──────────────────────────────────
    tournaments_played = Column(Integer, default=0)
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)

    # ── Stats in-game (API GraphQL eva.gg) ──────────────────────────────────
    season_id = Column(Integer, nullable=True)          # ID interne EVA de la saison synchro
    season_number = Column(Integer, nullable=True)      # Numéro de saison affiché (ex: 7)
    game_count = Column(Integer, nullable=True)         # Total parties jouées (saison courante)
    game_victories = Column(Integer, nullable=True)     # Victoires
    game_defeats = Column(Integer, nullable=True)       # Défaites
    kills = Column(Integer, nullable=True)              # Kills
    deaths = Column(Integer, nullable=True)             # Morts
    assists = Column(Integer, nullable=True)            # Assistances
    kd_ratio = Column(Float, nullable=True)             # K/D calculé (kills/deaths)
    game_time = Column(Integer, nullable=True)          # Temps de jeu (secondes)
    best_kill_streak = Column(Integer, nullable=True)   # Meilleure série d'éliminations
    traveled_distance = Column(Float, nullable=True)    # Distance totale parcourue (mètres)

    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
