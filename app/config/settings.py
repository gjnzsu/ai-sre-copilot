from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    port: int = Field(default=8080, alias="PORT")
    window_size: str = Field(default="5m", alias="WINDOW_SIZE")
    min_error_count: int = Field(default=20, alias="MIN_ERROR_COUNT")
    min_spike_ratio: float = Field(default=3.0, alias="MIN_SPIKE_RATIO")
    robust_z_threshold: float = Field(default=3.5, alias="ROBUST_Z_THRESHOLD")
    enable_llm_summary: bool = Field(default=False, alias="ENABLE_LLM_SUMMARY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
