from __future__ import annotations

import os
from urllib.parse import quote_plus, urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    redis_url: str
    telegram_bot_token: str
    secret_key: str
    access_token_expire_minutes: int = 43_200
    backend_base_url: str
    miniapp_url: str
    admin_username: str
    admin_password: str
    admin_token: str | None = None

    @staticmethod
    def build_render_postgres_url() -> str:
        host = os.getenv("RENDER_EXTERNAL_HOSTNAME") or os.getenv("DATABASE_HOST")
        user = os.getenv("DATABASE_USER")
        password = os.getenv("DATABASE_PASSWORD")
        port = os.getenv("DATABASE_PORT")
        dbname = os.getenv("DATABASE_NAME")
        if not all((host, user, password, port, dbname)):
            raise ValueError("Render database information incomplete")
        return (
            f"postgresql+asyncpg://{quote_plus(user)}:{quote_plus(password)}"
            f"@{host}:{int(port)}/{dbname}"
        )

    @property
    def resolved_database_url(self) -> str:
        raw = self.database_url
        if raw.startswith("postgresql+asyncpg://"):
            return raw
        parsed = urlparse(raw)
        if "HOST" in raw or "PORT" in raw or parsed.scheme == "":
            return self.build_render_postgres_url()
        return raw

    @model_validator(mode="after")
    def replace_database_url(self) -> "Settings":
        object.__setattr__(self, "database_url", self.resolved_database_url)
        return self

    @property
    def resolved_admin_token(self) -> str:
        return self.admin_token or self.admin_password


settings = Settings(database_url=os.getenv("DATABASE_URL", ""))
