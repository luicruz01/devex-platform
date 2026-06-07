from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str = Field(validation_alias="ANTHROPIC_API_KEY")
    table_name: str = Field(
        default="devex-events",
        validation_alias="DEVEX_EVENTS_TABLE",
    )
    aws_region: str = Field(
        default="us-east-1",
        validation_alias="AWS_REGION",
    )
    model: str = Field(
        default="claude-sonnet-4-20250514",
        validation_alias="DEVEX_ANALYST_MODEL",
    )
    window_days: int = Field(
        default=30,
        validation_alias="DEVEX_ANALYST_WINDOW_DAYS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )
