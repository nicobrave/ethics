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
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "https://ethics.recomai.cl",
        "https://www.ethics.recomai.cl",
        "https://ethics-frontend.onrender.com"
    ]
    ALLOWED_HOSTS: List[str] = [
        "localhost", 
        "127.0.0.1", 
        "ethics.recomai.cl",
        "www.ethics.recomai.cl",
        "ethics-36kr.onrender.com"
    ]
    RATE_LIMIT_PER_MINUTE: int = 10
    MAX_CONCURRENT_ANALYSES: int = 5
    USER_AGENT: str = os.getenv("USER_AGENT", "EthicsDetector/1.0")
    SCRAPING_TIMEOUT: int = int(os.getenv("SCRAPING_TIMEOUT", "60"))
    MAX_PAGE_SIZE: str = os.getenv("MAX_PAGE_SIZE", "5MB")

settings = Settings() 