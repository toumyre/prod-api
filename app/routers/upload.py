import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.auth import get_current_user
from app.models.user import User
from app.config import UPLOAD_DIR, API_PUBLIC_URL

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"}
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50 Mo


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(400, "Type de fichier non autorisé. Formats acceptés : jpg, jpeg, png, gif, webp, svg")

    content = await file.read(MAX_IMAGE_SIZE + 1)
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Fichier trop volumineux. Taille maximum : 50 Mo")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    return {"filename": filename, "url": f"{API_PUBLIC_URL}/uploads/{filename}"}
