import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "slb_coliving_jwt_secret_dev_key_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    ADMIN_DEFAULT_EMAIL: str = os.getenv("ADMIN_DEFAULT_EMAIL", "admin@slbcoliving.com")
    ADMIN_DEFAULT_PASSWORD: str = os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123")
    ADMIN_DEFAULT_NAME: str = os.getenv("ADMIN_DEFAULT_NAME", "SLB Admin")

    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

settings = Settings()
