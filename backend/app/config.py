from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import List

print("USANDO ENV FILE:", os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        case_sensitive=False,
    )

    GOOGLE_API_KEY: str
    DATABASE_URL: str = "sqlite:///./ethics_detector.db"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-this"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://ethics.recomai.cl"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "ethics.recomai.cl"]
    RATE_LIMIT_PER_MINUTE: int = 10
    MAX_CONCURRENT_ANALYSES: int = 5
    USER_AGENT: str = "EthicsDetector/1.0"
    SCRAPING_TIMEOUT: int = 30
    MAX_PAGE_SIZE: str = "5MB"

settings = Settings() 