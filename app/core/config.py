from functools import lru_cache
from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "CryptoSight"
    api_prefix: str = "/api"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./cryptosight.db",
    )
    cors_origins: list[str] = ["*"]
    default_history_limit: int = 365


@lru_cache
def get_settings() -> Settings:
    return Settings()
