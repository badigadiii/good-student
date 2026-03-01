from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LECTURE_BOT_", extra="ignore")

    headless: bool = True
    chat_poll_interval_ms: int = Field(default=3000, ge=0)
    post_join_delay_ms: int = Field(default=1000, ge=0)
    pre_goodbye_delay_ms: int = Field(default=1000, ge=0)
    pre_leave_delay_ms: int = Field(default=1000, ge=0)
    page_timeout_ms: int = Field(default=15000, ge=1)
    browser_slow_mo_ms: int = Field(default=0, ge=0)

    KEYPHRASE_MATCH_THRESHOLD: int = Field(default=3, ge=1)
    RECENT_MESSAGES_LIMIT: int = Field(default=10, ge=1)
