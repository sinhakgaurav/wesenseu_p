from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Monitour"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql+asyncpg://monitour:password@localhost:5432/monitour_db"
    SYNC_DATABASE_URL: str = "postgresql://monitour:password@localhost:5432/monitour_db"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Set to "local" to force local disk storage (no S3 credentials needed).
    # Set to "s3" to use AWS S3 / MinIO / R2.
    STORAGE_BACKEND: str = "local"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = "monitour-media"
    AWS_REGION: str = "ap-south-1"
    S3_ENDPOINT_URL: str = ""

    WESENSEU_API_URL: str = "http://localhost:8001/api/v1"
    WESENSEU_API_KEY: str = "wesenseu-api-key-for-enterweu"

    # Public URL Monitour exposes for WesenseU callbacks
    MONITOUR_PUBLIC_URL: str = "http://localhost:8000"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
