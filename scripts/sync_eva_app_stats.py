"""
Sync les stats in-game de chaque joueur ECLYPS depuis api.eva.gg (GraphQL).
- Récupère la saison active dynamiquement
- Filtre les stats sur la saison en cours (pas all-time)
- Nécessite que le champ eva_app_username soit renseigné dans eva_players
  (format : "ECYxToumyre#586100")

Usage: uv run python scripts/sync_eva_app_stats.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import urllib.request
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models.eva_player import EvaPlayer
from app.models.eva_player_snapshot import EvaPlayerSnapshot

EVA_GRAPHQL = "https://api.eva.gg/graphql"
UA = "Mozilla/5.0 (compatible; ECLYPS-sync/1.0)"

SEASON_QUERY = """
query getActiveSeason {
  seasonActive {
    id
    seasonNumber
    active
    status
  }
}
"""

STATS_QUERY = """
query GetPublicStats($username: String!, $seasonId: Int) {
  getPublicPlayerByUsername(username: $username) {
    id
    statistics(seasonId: $seasonId) {
      gameId
      seasonId
      data {
        kills
        deaths
        assists
        gameCount
        gameVictoryCount
        gameDefeatCount
        gameTime
        bestKillStreak
        traveledDistance
      }
    }
  }
}
"""


def graphql(query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        EVA_GRAPHQL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Origin": "https://app.eva.gg",
            "Referer": "https://app.eva.gg/",
            "User-Agent": UA,
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_active_season() -> tuple[int, int]:
    """Retourne (season_id, season_number) de la saison active."""
    result = graphql(SEASON_QUERY, {})
    season = result.get("data", {}).get("seasonActive")
    if not season:
        raise RuntimeError("Impossible de récupérer la saison active depuis api.eva.gg")
    return season["id"], season["seasonNumber"]


def sync():
    db = SessionLocal()

    # 1. Récupérer la saison active
    print("Récupération de la saison active…")
    season_id, season_number = get_active_season()
    print(f"  → Saison {season_number} (id interne: {season_id})")

    # 2. Joueurs à synchroniser
    players = db.query(EvaPlayer).filter(EvaPlayer.eva_app_username.isnot(None)).all()

    if not players:
        print("Aucun joueur avec eva_app_username renseigné.")
        db.close()
        return

    print(f"{len(players)} joueur(s) à synchroniser.")
    now = datetime.now(timezone.utc)

    for player in players:
        print(f"  Sync {player.player_name} ({player.eva_app_username})…")
        try:
            result = graphql(STATS_QUERY, {
                "username": player.eva_app_username,
                "seasonId": season_id,
            })
            data = result.get("data", {}).get("getPublicPlayerByUsername")
            if not data:
                print(f"    ⚠ Joueur introuvable sur app.eva.gg")
                continue

            stats_obj = data.get("statistics") or {}
            # Vérifier si profil privé (statistics peut être None)
            if not stats_obj:
                print(f"    ⚠ Profil privé ou aucune stats pour cette saison")
                continue

            stats = stats_obj.get("data") or {}
            kills  = stats.get("kills") or 0
            deaths = stats.get("deaths") or 0

            new_game_count = stats.get("gameCount") or 0
            new_kd = round(kills / deaths, 2) if deaths > 0 else float(kills)

            # Sauvegarder un snapshot si de nouvelles parties ont été jouées
            old_game_count = player.game_count or 0
            if new_game_count > old_game_count:
                snapshot = EvaPlayerSnapshot(
                    player_id      = player.id,
                    snapshot_at    = now,
                    season_number  = season_number,
                    game_count     = new_game_count,
                    game_victories = stats.get("gameVictoryCount"),
                    game_defeats   = stats.get("gameDefeatCount"),
                    kills          = kills,
                    deaths         = deaths,
                    assists        = stats.get("assists"),
                    kd_ratio       = new_kd,
                    game_time      = stats.get("gameTime"),
                )
                db.add(snapshot)
                new_games = new_game_count - old_game_count
                print(f"    📸 Snapshot sauvegardé (+{new_games} parties depuis le dernier sync)")

            player.season_id         = season_id
            player.season_number     = season_number
            player.game_count        = new_game_count
            player.game_victories    = stats.get("gameVictoryCount")
            player.game_defeats      = stats.get("gameDefeatCount")
            player.kills             = kills
            player.deaths            = deaths
            player.assists           = stats.get("assists")
            player.kd_ratio          = new_kd
            player.game_time         = stats.get("gameTime")
            player.best_kill_streak  = stats.get("bestKillStreak")
            player.traveled_distance = stats.get("traveledDistance")
            player.synced_at         = now

            print(f"    ✅ {kills}K / {deaths}D / {new_kd}KD — {new_game_count} parties")

        except Exception as e:
            print(f"    ❌ Erreur : {e}")

        time.sleep(2)  # Éviter le rate limit EVA

    db.commit()
    db.close()
    print("Sync terminé.")


if __name__ == "__main__":
    sync()
