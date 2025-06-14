import os
from pydantic_settings import BaseSettings

print("ENV:", dict(os.environ))

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    TEST_VAR: str

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")

settings = Settings()
print("GOOGLE_API_KEY:", settings.GOOGLE_API_KEY)
print("TEST_VAR:", settings.TEST_VAR)
