from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models.gallery import GalleryItem
from app.models.user import User
from app.uploads_cleanup import delete_upload_if_unused
from app.schemas.gallery import (
    GalleryItemCreate,
    GalleryItemUpdate,
    GalleryItemResponse,
    GalleryItemPublic,
)

router = APIRouter()


# --- Public ---

@router.get("/public", response_model=list[GalleryItemPublic])
async def get_public_gallery(
    x_site_id: int = Header(default=2, alias="x-site-id"),
    db: Session = Depends(get_db),
):
    items = (
        db.query(GalleryItem)
        .filter(GalleryItem.site_id == x_site_id, GalleryItem.published == True)
        .order_by(GalleryItem.sort_order, GalleryItem.created_at.desc())
        .all()
    )
    return items


# --- Admin ---

@router.get("/", response_model=list[GalleryItemResponse])
async def list_gallery(
    site_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(GalleryItem)
    if site_id is not None:
        query = query.filter(GalleryItem.site_id == site_id)
    return query.order_by(GalleryItem.created_at.desc()).all()


@router.post("/", response_model=GalleryItemResponse, status_code=201)
async def create_gallery_item(
    data: GalleryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = GalleryItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=GalleryItemResponse)
async def update_gallery_item(
    item_id: int,
    data: GalleryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Élément non trouvé")
    old_image, old_video = item.image_url, item.video_url
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    # Image remplacée : l'ancien fichier n'a plus de raison d'être
    if item.image_url != old_image:
        delete_upload_if_unused(db, old_image)
    if item.video_url != old_video:
        delete_upload_if_unused(db, old_video)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_gallery_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Élément non trouvé")
    old_image, old_video = item.image_url, item.video_url
    db.delete(item)
    db.commit()
    delete_upload_if_unused(db, old_image)
    delete_upload_if_unused(db, old_video)
