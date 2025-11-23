from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def resolved_admin_token(self) -> str:
        return self.admin_token or self.admin_password


settings = Settings()
