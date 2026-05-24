from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.eclyps_user import EclypUser
from app.models.eva_player import EvaPlayer
from app.routers.eclyps_auth import get_current_eclyps_user

router = APIRouter()


class PlayerStats(BaseModel):
    id: int
    player_name: str
    eva_user_id: str | None
    eva_app_username: str | None

    # Stats compétitives
    tournaments_played: int
    matches_played: int
    wins: int
    losses: int
    win_rate: float

    # Stats in-game
    game_count: int | None
    game_victories: int | None
    game_defeats: int | None
    kills: int | None
    deaths: int | None
    assists: int | None
    kd_ratio: float | None
    game_time: int | None        # en secondes
    best_kill_streak: int | None
    traveled_distance: float | None

    synced_at: str | None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[PlayerStats])
def get_players_stats(
    db: Session = Depends(get_db),
    _: EclypUser = Depends(get_current_eclyps_user),
):
    players = db.query(EvaPlayer).order_by(EvaPlayer.kills.desc().nullslast(), EvaPlayer.wins.desc()).all()
    return [
        PlayerStats(
            id=p.id,
            player_name=p.player_name,
            eva_user_id=p.eva_user_id,
            eva_app_username=p.eva_app_username,
            tournaments_played=p.tournaments_played,
            matches_played=p.matches_played,
            wins=p.wins,
            losses=p.losses,
            win_rate=round(p.win_rate, 1),
            game_count=p.game_count,
            game_victories=p.game_victories,
            game_defeats=p.game_defeats,
            kills=p.kills,
            deaths=p.deaths,
            assists=p.assists,
            kd_ratio=round(p.kd_ratio, 2) if p.kd_ratio is not None else None,
            game_time=p.game_time,
            best_kill_streak=p.best_kill_streak,
            traveled_distance=round(p.traveled_distance) if p.traveled_distance else None,
            synced_at=p.synced_at.isoformat() if p.synced_at else None,
        )
        for p in players
    ]
