"""
Sync les joueurs ECLYPS depuis l'API EVA competitive.
Pour chaque tournoi où ECLYPS participe, on récupère le lineup (liste des joueurs)
et on calcule leur bilan V/D à partir des matchs déjà en base.

Usage: uv run python scripts/sync_eva_players.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import urllib.request
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models.match import Match
from app.models.eva_player import EvaPlayer

EVA_API = "https://competitive.eva.gg/api"
EVA_CAEN_ORG_ID = "2444249435255883775"
ECLYPS_NAME = "ECLYPS"
UA = "Mozilla/5.0 (compatible; ECLYPS-sync/1.0)"


def eva_get(path, params=None, range_header=None):
    url = f"{EVA_API}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    if range_header:
        req.add_header("Range", range_header)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def sync():
    db = SessionLocal()

    # Dictionnaire : eva_user_id → {player_name, tournois, matches, wins, losses}
    players: dict[str, dict] = {}

    # 1. Récupérer tous les tournois EVA Caen
    try:
        tournaments = eva_get(
            "/tournaments",
            params={"organization_ids": EVA_CAEN_ORG_ID},
            range_header="tournaments=0-299",
        )
    except Exception as e:
        print(f"Erreur fetch tournois: {e}")
        db.close()
        return

    print(f"{len(tournaments)} tournois trouvés pour EVA Caen.")

    for tournament in tournaments:
        tournament_id = str(tournament.get("id", ""))
        tournament_name = tournament.get("name", "?")
        if not tournament_id:
            continue

        # 2. Trouver ECLYPS dans ce tournoi
        try:
            participants = eva_get(
                "/participants",
                params={"tournament_ids": tournament_id},
                range_header="participants=0-49",
            )
        except Exception as e:
            print(f"  Erreur participants {tournament_name}: {e}")
            continue

        eclyps_participant = next(
            (p for p in participants if (p.get("name") or "").upper() == ECLYPS_NAME),
            None,
        )
        if not eclyps_participant:
            continue

        participant_id = str(eclyps_participant.get("id", ""))
        lineup = eclyps_participant.get("lineup") or []
        print(f"  ECLYPS dans {tournament_name} — {len(lineup)} joueurs dans le lineup")

        # 3. Récupérer les matchs de ce participant pour calculer V/D
        try:
            matches = eva_get(
                "/matches",
                params={"participant_ids": participant_id},
                range_header="matches=0-49",
            )
        except Exception as e:
            print(f"  Erreur matchs {tournament_name}: {e}")
            continue

        # Compter V/D pour ce tournoi
        tournament_wins = 0
        tournament_losses = 0
        tournament_matches = 0
        for match in matches:
            if match.get("status") != "completed":
                continue
            for opp in match.get("opponents", []):
                if str((opp.get("participant") or {}).get("id", "")) == participant_id:
                    result = opp.get("result")
                    if result == "win":
                        tournament_wins += 1
                    elif result == "loss":
                        tournament_losses += 1
                    tournament_matches += 1

        # 4. Ajouter chaque joueur du lineup
        for member in lineup:
            player_user = member.get("playerUser") or {}
            eva_user_id = str(player_user.get("id", "")) or None
            player_name = member.get("name", "Joueur inconnu")
            key = eva_user_id or player_name

            if key not in players:
                players[key] = {
                    "player_name": player_name,
                    "eva_user_id": eva_user_id,
                    "tournaments_played": 0,
                    "matches_played": 0,
                    "wins": 0,
                    "losses": 0,
                }

            players[key]["tournaments_played"] += 1
            players[key]["matches_played"] += tournament_matches
            players[key]["wins"] += tournament_wins
            players[key]["losses"] += tournament_losses

    # 5. Upsert dans la base de données
    now = datetime.now(timezone.utc)
    upserted = 0
    for key, data in players.items():
        total = data["wins"] + data["losses"]
        win_rate = (data["wins"] / total * 100) if total > 0 else 0.0

        existing = db.query(EvaPlayer).filter(
            EvaPlayer.eva_user_id == data["eva_user_id"]
            if data["eva_user_id"]
            else EvaPlayer.player_name == data["player_name"]
        ).first()

        if existing:
            existing.player_name = data["player_name"]
            existing.tournaments_played = data["tournaments_played"]
            existing.matches_played = data["matches_played"]
            existing.wins = data["wins"]
            existing.losses = data["losses"]
            existing.win_rate = win_rate
            existing.synced_at = now
        else:
            db.add(EvaPlayer(
                player_name=data["player_name"],
                eva_user_id=data["eva_user_id"],
                tournaments_played=data["tournaments_played"],
                matches_played=data["matches_played"],
                wins=data["wins"],
                losses=data["losses"],
                win_rate=win_rate,
                synced_at=now,
            ))
        upserted += 1

    try:
        db.commit()
        print(f"\nSync terminé — {upserted} joueurs mis à jour.")
    except Exception as e:
        db.rollback()
        print(f"Erreur commit: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    sync()
