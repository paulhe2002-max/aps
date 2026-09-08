from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "aps_user"
    DB_PASSWORD: str = "aps_password"
    DB_NAME: str = "aps_db_1"
    # Optional full SQLAlchemy URL override. When set (env DATABASE_URL), it
    # takes precedence over the DB_* parts — handy for local runs without MySQL
    # (e.g. DATABASE_URL=sqlite:///./aps_local.db). Default keeps MySQL.
    DATABASE_URL_OVERRIDE: str | None = None
    SECRET_KEY: str = "aps-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    @property
    def DATABASE_URL(self) -> str:
        import os
        env_url = os.environ.get("DATABASE_URL") or self.DATABASE_URL_OVERRIDE
        if env_url:
            return env_url
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"


settings = Settings()
