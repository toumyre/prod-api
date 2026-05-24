import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL doit être défini dans le fichier .env")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY doit être défini dans le fichier .env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

ALLOWED_ORIGINS = [
    "https://eclyps-esport.fr",
    "https://stats.eclyps-esport.fr",
    "https://portfolio.t-etendard.fr",
    "https://admin.t-etendard.fr",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:5174",
]

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
API_PUBLIC_URL = os.getenv("API_PUBLIC_URL", "https://api.t-etendard.fr")
