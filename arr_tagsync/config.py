"""Configuration management for arr-tagsync."""

import contextlib
import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class Config(BaseModel):
    """Application configuration loaded from environment variables."""

    # Application settings
    app_name: str = Field(default="arr-tagsync", description="Application name")
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    dry_run: bool = Field(default=False, description="Run in dry-run mode without making changes")

    # Emby settings
    emby_url: str = Field(..., description="Emby server URL")
    emby_api_key: str = Field(..., description="Emby API key")
    emby_user_id: str | None = Field(default=None, description="Emby user ID (optional)")

    # Arr service settings (Radarr/Sonarr)
    arr_type: str = Field(..., description="Type of Arr service (radarr or sonarr)")
    arr_url: str = Field(..., description="Arr service URL")
    arr_api_key: str = Field(..., description="Arr service API key")

    # Sync settings
    batch_size: int = Field(default=50, description="Batch size for processing items")

    @field_validator("arr_type")
    @classmethod
    def validate_arr_type(cls, v: str) -> str:
        """Validate that arr_type is either 'radarr' or 'sonarr'."""
        if v.lower() not in ["radarr", "sonarr"]:
            raise ValueError("arr_type must be either 'radarr' or 'sonarr'")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    class Config:
        env_prefix = "TAGSYNC_"
        case_sensitive = False


def get_config() -> Config:
    """Get application configuration from environment variables."""
    # Load .env file if it exists
    load_dotenv()

    env_vars: dict[str, Any] = {}

    # Load environment variables with TAGSYNC_ prefix
    for key, value in os.environ.items():
        if key.startswith("TAGSYNC_"):
            # Remove prefix and convert to lowercase
            config_key = key[8:].lower()  # Remove "TAGSYNC_" prefix

            # Handle boolean values
            if config_key in ["dry_run"]:
                env_vars[config_key] = value.lower() in ["true", "1", "yes", "on"]
            # Handle integer values
            elif config_key in ["batch_size"]:
                with contextlib.suppress(ValueError):
                    env_vars[config_key] = int(value)
            else:
                env_vars[config_key] = value

    return Config(**env_vars)
