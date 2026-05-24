from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import SECRET_KEY, ALGORITHM
from app.database import get_db
from app.models.eclyps_user import EclypUser

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ECLYPS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours


# ── Schémas (structure des données attendues / retournées) ──────────────────

class LoginInput(BaseModel):
    username: str
    password: str

class PlayerMe(BaseModel):
    id: int
    username: str
    player_name: str | None
    eva_user_id: str | None


# ── Helpers ─────────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_eclyps_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ECLYPS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire, "type": "eclyps"}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_eclyps_user(request: Request, db: Session = Depends(get_db)) -> EclypUser:
    """Dépendance FastAPI : vérifie le cookie eclyps_token et retourne le joueur connecté."""
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non autorisé")
    token = request.cookies.get("eclyps_token")
    if not token:
        raise exc
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "eclyps":
            raise exc
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise exc
    user = db.query(EclypUser).filter(EclypUser.id == user_id, EclypUser.is_active == True).first()
    if not user:
        raise exc
    return user


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/login")
def login(body: LoginInput, response: Response, db: Session = Depends(get_db)):
    """Connexion d'un joueur ECLYPS → pose un cookie sécurisé."""
    user = db.query(EclypUser).filter(EclypUser.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    token = create_eclyps_token(user.id)
    response.set_cookie(
        key="eclyps_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 jours
    )
    return {"message": "Connecté", "username": user.username, "player_name": user.player_name}


@router.post("/logout")
def logout(response: Response):
    """Déconnexion : supprime le cookie."""
    response.delete_cookie("eclyps_token", samesite="lax", secure=True)
    return {"message": "Déconnecté"}


@router.get("/me", response_model=PlayerMe)
def me(current_user: EclypUser = Depends(get_current_eclyps_user)):
    """Retourne les infos du joueur actuellement connecté."""
    return current_user
