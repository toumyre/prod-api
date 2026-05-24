from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class EclypUser(Base):
    """
    Comptes des joueurs de l'équipe ECLYPS.
    Séparés des comptes admin (table 'users') — accès limité aux stats uniquement.
    """
    __tablename__ = "eclyps_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)   # ex: "ECYxTitboyyy"
    hashed_password = Column(String, nullable=False)
    player_name = Column(String, nullable=True)                          # pseudo EVA affiché
    eva_user_id = Column(String, nullable=True, index=True)              # ID joueur sur competitive.eva.gg
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
