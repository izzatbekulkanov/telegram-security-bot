from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Telegram API
    API_ID: int = Field(default=0, alias="API_ID")
    API_HASH: str = Field(default="", alias="API_HASH")
    BOT_TOKEN: str = Field(..., alias="BOT_TOKEN")

    # Security APIs
    VT_API_KEY: str = Field(default="", alias="VT_API_KEY")
    SAFE_BROWSING_KEY: str = Field(default="", alias="SAFE_BROWSING_KEY")

    # Payment
    PAYMENT_PROVIDER_TOKEN: str = Field(default="", alias="PAYMENT_TOKEN")

    # Admins
    ADMINS_STR: str = Field(default="", alias="ADMINS")

    # Channel for Logs
    LOG_CHANNEL_ID: int = Field(default=0, alias="LOG_CHANNEL_ID")

    # Database
    DB_URL: str = Field(default="sqlite+aiosqlite:///data/security_bot.db", alias="DB_URL")

    @property
    def ADMINS(self) -> List[int]:
        if not self.ADMINS_STR:
            return []
        return [int(x.strip()) for x in self.ADMINS_STR.split(",") if x.strip().isdigit()]

    # Validation
    @property
    def is_payment_enabled(self) -> bool:
        return bool(self.PAYMENT_PROVIDER_TOKEN)

    @property
    def is_vt_enabled(self) -> bool:
        return bool(self.VT_API_KEY)

settings = Settings()