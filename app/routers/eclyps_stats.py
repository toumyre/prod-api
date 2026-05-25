import json
import urllib.request
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.eclyps_user import EclypUser
from app.models.eva_player import EvaPlayer
from app.models.eva_player_snapshot import EvaPlayerSnapshot
from app.routers.eclyps_auth import get_current_eclyps_user

EVA_GRAPHQL = "https://api.eva.gg/graphql"
EVA_UA = "Mozilla/5.0 (compatible; ECLYPS-sync/1.0)"

GAMES_QUERY = """
query GetHistory($userId: Int!, $seasonId: Int!) {
  listLastAfterhGameHistoriesByUserAndSeason(userId: $userId, seasonId: $seasonId) {
    id
    createdAt
    data {
      duration
      teamOne { score name }
      teamTwo { score name }
    }
    players {
      userId
      data { kills deaths assists outcome team score niceName }
    }
    map { name }
    mode { identifier }
  }
}
"""

def _fetch_eva_games(eva_user_id: int, season_id: int) -> list:
    payload = json.dumps({"query": GAMES_QUERY, "variables": {"userId": eva_user_id, "seasonId": season_id}}).encode()
    req = urllib.request.Request(EVA_GRAPHQL, data=payload, headers={
        "Content-Type": "application/json",
        "Origin": "https://app.eva.gg",
        "Referer": "https://app.eva.gg/",
        "User-Agent": EVA_UA,
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    return result.get("data", {}).get("listLastAfterhGameHistoriesByUserAndSeason") or []

router = APIRouter()


# ── Schémas Pydantic ──────────────────────────────────────────────────────────

class PlayerStats(BaseModel):
    id: int
    player_name: str
    eva_user_id: str | None
    eva_app_username: str | None
    eva_app_user_id: int | None

    # Stats compétitives
    tournaments_played: int
    matches_played: int
    wins: int
    losses: int
    win_rate: float

    # Stats in-game
    season_id: int | None
    season_number: int | None
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


class SnapshotOut(BaseModel):
    id: int
    snapshot_at: str
    season_number: int | None
    game_count: int | None
    game_victories: int | None
    game_defeats: int | None
    kills: int | None
    deaths: int | None
    assists: int | None
    kd_ratio: float | None
    game_time: int | None

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

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
            eva_app_user_id=p.eva_app_user_id,
            tournaments_played=p.tournaments_played,
            matches_played=p.matches_played,
            wins=p.wins,
            losses=p.losses,
            win_rate=round(p.win_rate, 1),
            season_id=p.season_id,
            season_number=p.season_number,
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


@router.get("/{player_id}/games")
def get_player_games(
    player_id: int,
    db: Session = Depends(get_db),
    _: EclypUser = Depends(get_current_eclyps_user),
):
    """Retourne les 10 dernières parties du joueur (proxy vers api.eva.gg)."""
    player = db.query(EvaPlayer).filter(EvaPlayer.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    if not player.eva_app_user_id or not player.season_id:
        raise HTTPException(status_code=404, detail="Historique non disponible (eva_app_user_id manquant)")

    try:
        games = _fetch_eva_games(player.eva_app_user_id, player.season_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur EVA API : {e}")

    result = []
    for g in games:
        # Trouver les stats du joueur dans cette partie
        me = next((p for p in g["players"] if p["userId"] == player.eva_app_user_id), None)
        d = me["data"] if me else {}
        result.append({
            "id":          g["id"],
            "date":        g["createdAt"],
            "map":         (g.get("map") or {}).get("name"),
            "mode":        (g.get("mode") or {}).get("identifier"),
            "nb_players":  len(g["players"]),
            "duration":    (g.get("data") or {}).get("duration"),
            "outcome":     d.get("outcome"),   # "Victory" / "Defeat" / "Draw"
            "kills":       d.get("kills"),
            "deaths":      d.get("deaths"),
            "assists":     d.get("assists"),
            "team":        d.get("team"),
            "score":       d.get("score"),
        })
    return result


@router.get("/{player_id}/history", response_model=list[SnapshotOut])
def get_player_history(
    player_id: int,
    db: Session = Depends(get_db),
    _: EclypUser = Depends(get_current_eclyps_user),
):
    """Retourne les 60 derniers snapshots d'un joueur (trié du plus récent au plus ancien)."""
    # Vérifier que le joueur existe
    player = db.query(EvaPlayer).filter(EvaPlayer.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Joueur introuvable")

    snapshots = (
        db.query(EvaPlayerSnapshot)
        .filter(EvaPlayerSnapshot.player_id == player_id)
        .order_by(EvaPlayerSnapshot.snapshot_at.desc())
        .limit(60)
        .all()
    )

    return [
        SnapshotOut(
            id=s.id,
            snapshot_at=s.snapshot_at.isoformat(),
            season_number=s.season_number,
            game_count=s.game_count,
            game_victories=s.game_victories,
            game_defeats=s.game_defeats,
            kills=s.kills,
            deaths=s.deaths,
            assists=s.assists,
            kd_ratio=round(s.kd_ratio, 2) if s.kd_ratio is not None else None,
            game_time=s.game_time,
        )
        for s in snapshots
    ]
