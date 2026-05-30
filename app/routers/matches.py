import json
import time
import urllib.request
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.match import Match
from app.schemas.match import MatchPublic

router = APIRouter()

EVA_API = "https://competitive.eva.gg/api"
EVA_MEDIA = "https://competitive.eva.gg/media/file"
UA = "Mozilla/5.0 (compatible; ECLYPS-sync/1.0)"

# entity_id d'ECLYPS sur competitive.eva.gg (stable, ne change pas entre saisons)
ECLYPS_ENTITY_ID = "2448652881169059839"
JARL_LEAGUE_NAME = "JARL LEAGUE - CAEN"

# Labels des saisons connues — à compléter manuellement quand une nouvelle saison démarre
SEASON_LABELS: dict[str, str] = {
    "2441507312469446655": "S1 2026",
    "2489142894001680383": "S2 2026",
}

# Cache en mémoire pour éviter de spammer l'API EVA à chaque requête
_cache: dict = {"ranking_ids": [], "fetched_at": 0.0}
CACHE_TTL = 3600  # 1h


def _discover_ranking_ids() -> list[str]:
    """Découvre tous les ranking IDs JARL LEAGUE - CAEN via l'entity_id d'ECLYPS.
    Résultat trié par ID croissant = ordre chronologique (IDs EVA sont snowflake).
    """
    now = time.time()
    if _cache["ranking_ids"] and (now - _cache["fetched_at"]) < CACHE_TTL:
        return _cache["ranking_ids"]

    try:
        req = urllib.request.Request(
            f"{EVA_API}/circuit-ranking-items?entity_ids={ECLYPS_ENTITY_ID}",
            headers={"User-Agent": UA, "Accept": "application/json"},
        )
        req.add_header("Range", "items=0-99")
        with urllib.request.urlopen(req, timeout=10) as r:
            items = json.loads(r.read())

        seen: set[str] = set()
        ids: list[str] = []
        for item in items:
            rid = item["ranking"]["id"]
            rname = item["ranking"]["name"]
            if rname == JARL_LEAGUE_NAME and rid not in seen:
                seen.add(rid)
                ids.append(rid)

        ids.sort()  # snowflake → ordre chronologique

        if ids:
            _cache["ranking_ids"] = ids
            _cache["fetched_at"] = now
            return ids
    except Exception:
        pass

    # Fallback sur les IDs hardcodés si l'API est inaccessible
    return sorted(SEASON_LABELS.keys())


def _season_label(ranking_id: str, index: int) -> str:
    if ranking_id in SEASON_LABELS:
        return SEASON_LABELS[ranking_id]
    return f"S{index + 1} 2026"


def _fetch_season_standings(ranking_id: str) -> list[dict]:
    req = urllib.request.Request(
        f"{EVA_API}/circuit-ranking-items?ranking_ids={ranking_id}",
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    req.add_header("Range", "items=0-49")
    with urllib.request.urlopen(req, timeout=10) as r:
        items = json.loads(r.read())

    standings = []
    for item in items:
        entity = item.get("entity") or {}
        logo_obj = entity.get("logo") or {}
        logo_id = logo_obj.get("id") if isinstance(logo_obj, dict) else None
        logo_url = f"{EVA_MEDIA}/{logo_id}/logo_medium" if logo_id else None
        props = item.get("properties") or {}
        standings.append({
            "rank": item["rank"],
            "position": item["position"],
            "name": entity.get("name", "?"),
            "logo": logo_url,
            "points": item["points"],
            "played": props.get("played", 0),
        })
    return standings


@router.get("/public", response_model=list[MatchPublic])
async def get_public_matches(
    x_site_id: int = Header(default=2, alias="x-site-id"),
    db: Session = Depends(get_db),
):
    return (
        db.query(Match)
        .filter(Match.site_id == x_site_id)
        .order_by(Match.scheduled_at.desc().nullslast(), Match.played_at.desc().nullslast())
        .all()
    )


@router.get("/standings")
async def get_standings():
    ranking_ids = _discover_ranking_ids()

    seasons = []
    for i, ranking_id in enumerate(ranking_ids):
        try:
            standings = _fetch_season_standings(ranking_id)
            if standings:
                seasons.append({
                    "label": _season_label(ranking_id, i),
                    "ranking_id": ranking_id,
                    "tournament_name": JARL_LEAGUE_NAME,
                    "standings": standings,
                })
        except Exception:
            pass  # Saison inaccessible temporairement, on skip

    if not seasons:
        raise HTTPException(status_code=502, detail="Impossible de contacter l'API EVA")

    return {
        "seasons": seasons,
        "current_season": seasons[-1]["label"],  # La plus récente = la plus haute ID
    }
