from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Pharmacy Supply Chain AI"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "development_secret_key"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Google Gemini
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_MAX_TOKENS: int = 2048
    
    # Business Logic
    INVENTORY_CHECK_INTERVAL_HOURS: int = 6
    REORDER_THRESHOLD_DAYS: int = 7
    CRITICAL_THRESHOLD_DAYS: int = 2
    HIGH_THRESHOLD_DAYS: int = 5
    MAX_NEGOTIATION_ROUNDS: int = 3
    AUTO_APPROVE_THRESHOLD: float = 1000.0

    class Config:
        env_file = ".env"

settings = Settings()
