"""
Sync les stats in-game de chaque joueur ECLYPS depuis api.eva.gg (GraphQL).
Nécessite que le champ eva_app_username soit renseigné dans eva_players
(format : "ECYxToumyre#586100")

Usage: uv run python scripts/sync_eva_app_stats.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import urllib.request
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models.eva_player import EvaPlayer

EVA_GRAPHQL = "https://api.eva.gg/graphql"
UA = "Mozilla/5.0 (compatible; ECLYPS-sync/1.0)"

STATS_QUERY = """
query GetPublicStats($username: String!) {
  getPublicPlayerByUsername(username: $username) {
    id
    user { id username }
    statistics {
      data {
        kills
        deaths
        assists
        gameCount
        gameVictoryCount
        gameDefeatCount
        gameDrawCount
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


def sync():
    db = SessionLocal()
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
            result = graphql(STATS_QUERY, {"username": player.eva_app_username})
            data = result.get("data", {}).get("getPublicPlayerByUsername")
            if not data:
                print(f"    ⚠ Joueur introuvable sur app.eva.gg")
                continue

            stats = (data.get("statistics") or {}).get("data") or {}
            kills  = stats.get("kills", 0)
            deaths = stats.get("deaths", 0)

            player.game_count       = stats.get("gameCount")
            player.game_victories   = stats.get("gameVictoryCount")
            player.game_defeats     = stats.get("gameDefeatCount")
            player.kills            = kills
            player.deaths           = deaths
            player.assists          = stats.get("assists")
            player.kd_ratio         = round(kills / deaths, 2) if deaths > 0 else float(kills)
            player.game_time        = stats.get("gameTime")
            player.best_kill_streak = stats.get("bestKillStreak")
            player.traveled_distance= stats.get("traveledDistance")
            player.synced_at        = now

            print(f"    ✅ {kills}K / {deaths}D / {player.kd_ratio}KD — {stats.get('gameCount')} parties")

        except Exception as e:
            print(f"    ❌ Erreur : {e}")

    db.commit()
    db.close()
    print("Sync terminé.")


if __name__ == "__main__":
    sync()
