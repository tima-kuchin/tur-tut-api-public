from pydantic_settings import BaseSettings
from datetime import timedelta

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    DATABASE_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    AVATAR_UPLOAD_DIR: str = "static/avatars"
    BASE_STATIC_URL: str = "https://testdomain.com/static"

    ROUTE_TYPE_UUID: str
    POST_TYPE_UUID: str
    NEWS_TYPE_UUID: str

    class Config:
        env_file = ".env"

    @property
    def token_expiration(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_token_expiration(self) -> timedelta:
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

settings = Settings()