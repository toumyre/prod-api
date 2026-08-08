from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models.skill import Skill
from app.models.user import User
from app.uploads_cleanup import delete_upload_if_unused
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillPublic,
)

router = APIRouter()


# --- Public ---

@router.get("/public", response_model=list[SkillPublic])
async def get_public_skills(db: Session = Depends(get_db)):
    return (
        db.query(Skill)
        .filter(Skill.published == True, Skill.site_id == 1)
        .order_by(Skill.sort_order, Skill.name)
        .all()
    )


# --- Admin ---

@router.get("/", response_model=list[SkillResponse])
async def list_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Skill).order_by(Skill.sort_order, Skill.name).all()


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(
    data: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = Skill(**data.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    data: SkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Compétence non trouvée")
    old_logo = skill.logo_url
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(skill, key, value)
    db.commit()
    db.refresh(skill)
    if skill.logo_url != old_logo:
        delete_upload_if_unused(db, old_logo)
    return skill


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Compétence non trouvée")
    old_logo = skill.logo_url
    db.delete(skill)
    db.commit()
    delete_upload_if_unused(db, old_logo)
