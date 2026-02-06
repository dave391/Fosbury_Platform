from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECURITY_KEY: str
    SESSION_SECRET: str

    class Config:
        env_file = ".env"


settings = Settings()
