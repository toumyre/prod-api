from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models.about import About
from app.models.user import User
from app.uploads_cleanup import delete_upload_if_unused
from app.schemas.about import AboutCreate, AboutUpdate, AboutResponse, AboutPublic

router = APIRouter()


# --- Public ---

@router.get("/public", response_model=AboutPublic)
async def get_public_about(db: Session = Depends(get_db)):
    about = db.query(About).filter(About.site_id == 1, About.published == True).first()
    if not about:
        raise HTTPException(status_code=404, detail="Page À propos non trouvée")
    return about


# --- Admin ---

@router.get("/", response_model=AboutResponse | None)
async def get_about(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(About).filter(About.site_id == 1).first()


@router.post("/", response_model=AboutResponse, status_code=201)
async def create_about(
    data: AboutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    about = About(**data.model_dump())
    db.add(about)
    db.commit()
    db.refresh(about)
    return about


@router.put("/{about_id}", response_model=AboutResponse)
async def update_about(
    about_id: int,
    data: AboutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    about = db.query(About).filter(About.id == about_id).first()
    if not about:
        raise HTTPException(status_code=404, detail="Non trouvé")
    old_photo = about.photo_url
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(about, key, value)
    db.commit()
    db.refresh(about)
    if about.photo_url != old_photo:
        delete_upload_if_unused(db, old_photo)
    return about
