"""Application configuration using Pydantic Settings"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App Config
    APP_ENV: str = "development"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    LOG_LEVEL: str = "INFO"
    
    # API Keys & LLM Settings
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None
    DEFAULT_MODEL: str = "antigravity"
    DEFAULT_PROVIDER: str = "openai"
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    MISTRAL_API_KEY: str | None = None
    TOGETHER_API_KEY: str | None = None
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/superagent"
    REDIS_URL: str = "redis://localhost:6379"
    QDRANT_URL: str = "http://localhost:6333"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origin_list(self) -> List[str]:
        """Comma-separated CORS origins parsed into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
