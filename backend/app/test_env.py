from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
print("GOOGLE_API_KEY:", settings.GOOGLE_API_KEY) 