from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.auth import get_current_user
from app.models.project import Project
from app.models.user import User
from app.uploads_cleanup import delete_upload_if_unused
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectPublic,
)

router = APIRouter()


# --- Public ---

@router.get("/public", response_model=list[ProjectPublic])
async def get_public_projects(db: Session = Depends(get_db)):
    return (
        db.query(Project)
        .filter(Project.published == True, Project.site_id == 1)
        .order_by(Project.sort_order, Project.created_at.desc())
        .all()
    )


@router.get("/public/{project_id}", response_model=ProjectPublic)
async def get_public_project(project_id: int, db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.published == True)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


# --- Admin ---

@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Project).order_by(Project.sort_order).all()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(**data.model_dump())
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce slug existe déjà, choisissez-en un autre.")
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    old_image = project.image_url
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    if project.image_url != old_image:
        delete_upload_if_unused(db, old_image)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    old_image = project.image_url
    db.delete(project)
    db.commit()
    delete_upload_if_unused(db, old_image)
