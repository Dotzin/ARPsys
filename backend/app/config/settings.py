from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path


class Settings(BaseSettings):
    # Database settings
    database_path: str = Field(default="database.db", env="DATABASE_PATH")

    # API settings
    api_session_token: str = Field(default="default_token", env="API_SESSION_TOKEN")

    # Application settings
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Background task settings
    report_update_interval: int = Field(default=3600, env="REPORT_UPDATE_INTERVAL")  # seconds

    # Authentication settings
    jwt_secret_key: str = Field(default="secret", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()
