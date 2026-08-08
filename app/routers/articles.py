from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.auth import get_current_user
from app.models.article import Article
from app.models.user import User
from app.uploads_cleanup import delete_upload_if_unused
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticlePublic,
)

router = APIRouter()


# --- Public ---

@router.get("/public", response_model=list[ArticlePublic])
async def get_public_articles(
    x_site_id: int = Header(default=1, alias="x-site-id"),
    db: Session = Depends(get_db),
):
    return (
        db.query(Article)
        .filter(Article.site_id == x_site_id, Article.published == True)
        .order_by(Article.created_at.desc())
        .all()
    )


# --- Admin ---

@router.get("/", response_model=list[ArticleResponse])
async def list_articles(
    site_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Article)
    if site_id is not None:
        query = query.filter(Article.site_id == site_id)
    return query.order_by(Article.created_at.desc()).all()


@router.post("/", response_model=ArticleResponse, status_code=201)
async def create_article(
    data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = Article(**data.model_dump())
    db.add(article)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce slug existe déjà, choisissez-en un autre.")
    db.refresh(article)
    return article


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    old_image = article.image_url
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(article, key, value)
    db.commit()
    db.refresh(article)
    if article.image_url != old_image:
        delete_upload_if_unused(db, old_image)
    return article


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    old_image = article.image_url
    db.delete(article)
    db.commit()
    delete_upload_if_unused(db, old_image)
