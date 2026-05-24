"""
Crée un compte joueur ECLYPS dans la base.
À lancer depuis ct-api pour chaque membre de l'équipe.

Usage:
  uv run python scripts/create_eclyps_user.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext
from app.database import SessionLocal
from app.models.eclyps_user import EclypUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user():
    print("=== Création d'un compte joueur ECLYPS ===\n")
    username = input("Pseudo (ex: ECYxTitboyyy) : ").strip()
    password = input("Mot de passe : ").strip()
    player_name = input("Nom affiché (laisser vide = même que le pseudo) : ").strip() or username
    eva_user_id = input("ID EVA competitive (laisser vide si inconnu) : ").strip() or None

    db = SessionLocal()
    existing = db.query(EclypUser).filter(EclypUser.username == username).first()
    if existing:
        print(f"\n❌ Le pseudo '{username}' existe déjà.")
        db.close()
        return

    user = EclypUser(
        username=username,
        hashed_password=pwd_context.hash(password),
        player_name=player_name,
        eva_user_id=eva_user_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    print(f"\n✅ Compte créé pour '{username}' (player_name='{player_name}')")
    db.close()


if __name__ == "__main__":
    create_user()
