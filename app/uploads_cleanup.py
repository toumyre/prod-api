"""Nettoyage des fichiers uploadés devenus inutiles.

`/api/upload/` écrit un fichier dans UPLOAD_DIR et renvoie son URL, qui est ensuite
stockée dans une colonne (image_url, photo_url, logo_url…). Jusqu'ici, supprimer une
entrée ou remplacer son image laissait le fichier sur le disque pour toujours :
62 fichiers orphelins (51 Mo) avaient été accumulés entre avril et août 2026.

Règle appliquée ici : un fichier n'est supprimé que si plus AUCUNE ligne de la base
ne le référence — deux entrées peuvent parfaitement pointer vers la même image.
"""
import os

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR

# Fichiers servis par des routes qui les nomment en dur (app/routers/cv.py et
# synthesis.py). Ils n'apparaissent dans AUCUNE colonne : sans cette liste, ils
# passeraient pour des orphelins et seraient supprimés à tort.
PROTECTED_FILES = {"cv.pdf", "tableau_synthese.pdf"}

# Toutes les colonnes susceptibles de contenir une URL /uploads/.
# À compléter si une nouvelle entité avec image apparaît.
URL_COLUMNS = [
    ("about", "photo_url"),
    ("about", "cv_url"),
    ("articles", "image_url"),
    ("gallery_items", "image_url"),
    ("gallery_items", "video_url"),
    ("projects", "image_url"),
    ("roster_members", "photo_url"),
    ("skills", "logo_url"),
]


def upload_filename(url: str | None) -> str | None:
    """Nom du fichier si l'URL désigne un de nos uploads, sinon None.

    On ne conserve que le nom de base : une URL bricolée du type
    « …/uploads/../../etc/passwd » ne peut donc pas sortir du dossier.
    """
    if not url or "/uploads/" not in url:
        return None
    name = os.path.basename(url.split("?")[0].split("#")[0].strip())
    if not name or name in {".", ".."}:
        return None
    return name


def _is_still_referenced(db: Session, filename: str) -> bool:
    """True si au moins une ligne de la base pointe encore vers ce fichier."""
    for table, column in URL_COLUMNS:
        # Noms de table/colonne issus de la constante ci-dessus (jamais de l'utilisateur) ;
        # seule la valeur recherchée est passée en paramètre lié.
        query = text(f"SELECT 1 FROM {table} WHERE {column} LIKE :pattern LIMIT 1")
        if db.execute(query, {"pattern": f"%/{filename}"}).first():
            return True
    return False


def delete_upload_if_unused(db: Session, url: str | None) -> bool:
    """Supprime le fichier pointé par `url` si plus rien ne le référence.

    À appeler APRÈS le commit qui retire la référence, sinon l'entrée en cours de
    suppression se compte elle-même et le fichier n'est jamais nettoyé.

    Ne lève jamais d'exception : un échec de ménage ne doit pas faire échouer la
    requête HTTP de l'utilisateur, qui a bien été traitée.
    """
    filename = upload_filename(url)
    if not filename or filename in PROTECTED_FILES:
        return False
    try:
        if _is_still_referenced(db, filename):
            return False
        path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(path):
            os.remove(path)
            return True
    except Exception:
        pass
    return False
