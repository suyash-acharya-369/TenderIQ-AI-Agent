import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TenderIQ AI Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tenderiq-secret-key-change-in-production-32bytes-min")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tenderiq.db")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Encryption key for source credentials (32-byte base64 string or urlsafe string)
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "vXf6hP8q9L2mN5kR8wT1zY3uI6oP9aS2")
    
    # AI Providers
    DEFAULT_AI_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "openai")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY", "")
    
    # Notifications
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: Optional[str] = os.getenv("SENDER_EMAIL", "notifications@tenderiq.ai")
    
    WHATSAPP_PHONE_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_ACCOUNT_ID: Optional[str] = os.getenv("WHATSAPP_ACCOUNT_ID", "")
    WHATSAPP_ACCESS_TOKEN: Optional[str] = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    
    # Storage
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")  # local, s3, azure, gcp
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage")
    
    # Crawler Defaults
    DEFAULT_CRAWLER_FREQUENCY: str = "daily"
    MAX_CRAWL_DEPTH: int = 5
    MATCH_SCORE_THRESHOLD: float = 90.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

