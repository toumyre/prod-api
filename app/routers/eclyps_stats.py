from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.eclyps_user import EclypUser
from app.models.eva_player import EvaPlayer
from app.routers.eclyps_auth import get_current_eclyps_user

router = APIRouter()


# ── Schéma de réponse ────────────────────────────────────────────────────────

class PlayerStats(BaseModel):
    id: int
    player_name: str
    eva_user_id: str | None
    tournaments_played: int
    matches_played: int
    wins: int
    losses: int
    win_rate: float
    synced_at: str | None

    class Config:
        from_attributes = True


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[PlayerStats])
def get_players_stats(
    db: Session = Depends(get_db),
    _: EclypUser = Depends(get_current_eclyps_user),  # ← protégé : il faut être connecté
):
    """
    Retourne les stats de tous les joueurs ECLYPS.
    Accessible uniquement aux membres de l'équipe connectés.
    """
    players = db.query(EvaPlayer).order_by(EvaPlayer.wins.desc()).all()
    return [
        PlayerStats(
            id=p.id,
            player_name=p.player_name,
            eva_user_id=p.eva_user_id,
            tournaments_played=p.tournaments_played,
            matches_played=p.matches_played,
            wins=p.wins,
            losses=p.losses,
            win_rate=round(p.win_rate, 1),
            synced_at=p.synced_at.isoformat() if p.synced_at else None,
        )
        for p in players
    ]
