from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    ADMIN_IDS: str = ""

    DB_USER: str = "datatap"
    DB_PASS: str = "secure_password"
    DB_NAME: str = "datatap"
    DATABASE_URL: str = "postgresql+asyncpg://datatap:secure_password@postgres:5432/datatap"

    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str
    WEBHOOK_URL: str = ""
    WEBHOOK_HOST: str = "0.0.0.0"
    WEBHOOK_PORT: int = 8080

    START_BALANCE: int = 500
    START_ENERGY: int = 1000
    MAX_ENERGY: int = 1000
    ENERGY_RESTORE_SEC: int = 3
    TAP_COOLDOWN_MS: int = 100
    TAP_POWER_BASE: int = 1
    REFERRAL_BONUS_FIXED: int = 50
    REFERRAL_BONUS_PERCENT: float = 0.05
    PASSIVE_INCOME_ENABLED: bool = True

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/logs/bot.log"

    @property
    def admin_ids_list(self) -> list[int]:
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
