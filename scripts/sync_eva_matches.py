"""
Sync ECLYPS matches from competitive.eva.gg into the local database.
Run manually or via systemd timer (every 6h).

Strategy:
  1. Fetch recent tournaments from EVA Caen (organization_id hardcoded)
  2. For each tournament, list participants and find ECLYPS by name
  3. Fetch all matches for ECLYPS's participant_id in that tournament
  4. Upsert into DB

Usage: uv run python scripts/sync_eva_matches.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import urllib.request
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models.match import Match

EVA_API = "https://competitive.eva.gg/api"
EVA_CAEN_ORG_ID = "2444249435255883775"
ECLYPS_NAME = "ECLYPS"
SITE_ID = 2


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
        data = json.loads(resp.read())
    # L'API EVA renvoie désormais un objet paginé {"items": [...], "range": ...}
    # au lieu d'une liste brute. On extrait "items" tout en restant rétro-compatible.
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def sync():
    db = SessionLocal()
    synced = 0
    errors = 0

    # 1. Fetch recent EVA Caen tournaments
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
        tournament_name = tournament.get("name") or "JARL League"

        if not tournament_id:
            continue

        # 2. List participants and find ECLYPS
        try:
            participants = eva_get(
                "/participants",
                params={"tournament_ids": tournament_id},
                range_header="participants=0-49",
            )
        except Exception as e:
            print(f"Erreur participants {tournament_name}: {e}")
            continue

        eclyps_participant = next(
            (p for p in participants if (p.get("name") or "").upper() == ECLYPS_NAME),
            None,
        )

        if not eclyps_participant:
            continue

        participant_id = str(eclyps_participant.get("id", ""))
        print(f"ECLYPS trouvé dans {tournament_name} (participant_id={participant_id})")

        # 3. Fetch matches for this participant
        try:
            matches = eva_get(
                "/matches",
                params={"participant_ids": participant_id},
                range_header="matches=0-49",
            )
        except Exception as e:
            print(f"Erreur matchs {tournament_name}: {e}")
            errors += 1
            continue

        for match in matches:
            try:
                eva_match_id = str(match.get("id", ""))
                if not eva_match_id:
                    continue

                opponents = match.get("opponents", [])
                eclyps_opp = None
                other_opp = None

                for opp in opponents:
                    p = opp.get("participant", {})
                    if str(p.get("id", "")) == participant_id:
                        eclyps_opp = opp
                    else:
                        other_opp = opp

                if not other_opp:
                    continue

                other_p = other_opp.get("participant", {})
                opponent_name = other_p.get("name") or "Adversaire inconnu"
                logo_fields = other_p.get("customFieldValues", {}).get("logo", {})
                opponent_logo_url = logo_fields.get("logo_medium") or logo_fields.get("icon_medium")

                score_eclyps = eclyps_opp.get("score") if eclyps_opp else None
                score_opponent = other_opp.get("score")

                result_raw = eclyps_opp.get("result") if eclyps_opp else None
                result = result_raw if result_raw in ("win", "loss", "draw") else None

                match_status = match.get("status", "pending")
                scheduled_at = parse_dt(match.get("scheduledDatetime"))
                if scheduled_at is None:
                    round_name = (match.get("round") or {}).get("name", "")
                    try:
                        scheduled_at = datetime.strptime(round_name, "%d/%m/%Y").replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        pass
                played_at = parse_dt(match.get("playedAt"))

                stage = match.get("stage") or {}
                division = stage.get("name") if isinstance(stage, dict) else str(stage) if stage else None

                existing = db.query(Match).filter(Match.eva_match_id == eva_match_id).first()
                if existing:
                    existing.tournament_name = tournament_name
                    existing.division = division
                    existing.opponent_name = opponent_name
                    existing.opponent_logo_url = opponent_logo_url
                    existing.scheduled_at = scheduled_at
                    existing.played_at = played_at
                    existing.status = match_status
                    existing.score_eclyps = score_eclyps
                    existing.score_opponent = score_opponent
                    existing.result = result
                    existing.synced_at = datetime.now(timezone.utc)
                else:
                    db.add(Match(
                        site_id=SITE_ID,
                        eva_match_id=eva_match_id,
                        tournament_id=tournament_id,
                        tournament_name=tournament_name,
                        division=division,
                        opponent_name=opponent_name,
                        opponent_logo_url=opponent_logo_url,
                        scheduled_at=scheduled_at,
                        played_at=played_at,
                        status=match_status,
                        score_eclyps=score_eclyps,
                        score_opponent=score_opponent,
                        result=result,
                    ))

                synced += 1

            except Exception as e:
                print(f"Erreur match {match.get('id')}: {e}")
                errors += 1

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Erreur commit tournoi {tournament_name}: {e}")

    db.close()
    print(f"Sync terminé — {synced} matchs traités, {errors} erreurs.")


if __name__ == "__main__":
    sync()
