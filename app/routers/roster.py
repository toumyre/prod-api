from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models.roster import RosterMember
from app.models.user import User
from app.uploads_cleanup import delete_upload_if_unused
from app.schemas.roster import (
    RosterMemberCreate,
    RosterMemberUpdate,
    RosterMemberResponse,
    RosterMemberPublic,
)

router = APIRouter()


# --- Public ---

@router.get("/public", response_model=list[RosterMemberPublic])
async def get_public_roster(
    x_site_id: int = Header(default=2, alias="x-site-id"),
    db: Session = Depends(get_db),
):
    members = (
        db.query(RosterMember)
        .filter(RosterMember.site_id == x_site_id, RosterMember.published == True)
        .order_by(RosterMember.sort_order, RosterMember.name)
        .all()
    )
    return members


# --- Admin ---

@router.get("/", response_model=list[RosterMemberResponse])
async def list_roster(
    site_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(RosterMember)
    if site_id is not None:
        query = query.filter(RosterMember.site_id == site_id)
    return query.order_by(RosterMember.sort_order).all()


@router.post("/", response_model=RosterMemberResponse, status_code=201)
async def create_roster_member(
    data: RosterMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = RosterMember(**data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.put("/{member_id}", response_model=RosterMemberResponse)
async def update_roster_member(
    member_id: int,
    data: RosterMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = db.query(RosterMember).filter(RosterMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Membre non trouvé")
    old_photo = member.photo_url
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(member, key, value)
    db.commit()
    db.refresh(member)
    if member.photo_url != old_photo:
        delete_upload_if_unused(db, old_photo)
    return member


@router.delete("/{member_id}", status_code=204)
async def delete_roster_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = db.query(RosterMember).filter(RosterMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Membre non trouvé")
    old_photo = member.photo_url
    db.delete(member)
    db.commit()
    delete_upload_if_unused(db, old_photo)
