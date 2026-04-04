# app/core/config.py

# pydantic-settings reads values from the .env file automatically
# If a variable is missing, it raises an error immediately on startup
# This is better than getting mysterious crashes later in the code

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "Healthcare Appointment System"
    VERSION: str = "1.0.0"
    
    # API prefix — all routes will be /api/v1/...
    API_V1_PREFIX: str = "/api/v1"
    
    # Database — we'll fill this in properly in Phase 2
    DATABASE_URL: str = "postgresql+asyncpg://postgres:1234@localhost:5432/healthcare"
    
    # Redis — for caching and task queue
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "change-this-to-a-long-random-string-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        # Tell pydantic to read from .env file
        env_file = ".env"
        case_sensitive = True

# Create a single instance — import this everywhere
settings = Settings()