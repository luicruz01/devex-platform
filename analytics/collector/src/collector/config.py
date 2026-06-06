from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    table_name: str = Field(
        default="devex-events",
        validation_alias="DEVEX_EVENTS_TABLE",
    )
    aws_region: str = Field(
        default="us-east-1",
        validation_alias="AWS_REGION",
    )
    environment: str = Field(
        default="local",
        validation_alias="DEVEX_ENVIRONMENT",
    )
    github_token: Optional[str] = Field(
        default=None,
        validation_alias="GITHUB_TOKEN",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    return Settings()
