from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path


class Settings(BaseSettings):
    # Database settings
    database_path: str = Field(default="database.db", env="DATABASE_PATH")

    # API settings
    api_session_token: str = Field(..., env="API_SESSION_TOKEN")

    # Application settings
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Background task settings
    report_update_interval: int = Field(default=3600, env="REPORT_UPDATE_INTERVAL")  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()
