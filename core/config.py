from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECURITY_KEY: str
    SESSION_SECRET: str
    EXPOSE_DOCS: bool = False
    BASIC_AUTH_ENABLED: bool = False
    BASIC_AUTH_USERNAME: str = ""
    BASIC_AUTH_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
