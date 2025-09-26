"""Configuration management for ArrEm-sync using pydantic-settings."""

import logging
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class ArrInstanceConfig(BaseModel):
    """Configuration for a single Arr instance."""

    type: str = Field(..., description="Type of Arr service (radarr or sonarr)")
    url: str = Field(..., description="Arr service URL")
    api_key: str = Field(..., description="Arr service API key")
    name: str | None = Field(None, description="Optional descriptive name for this instance")

    @field_validator("type")
    @classmethod
    def validate_arr_type(cls, v: str) -> str:
        """Validate that arr_type is either 'radarr' or 'sonarr'."""
        if v.lower() not in ["radarr", "sonarr"]:
            raise ValueError("arr_type must be either 'radarr' or 'sonarr'")
        return v.lower()


class Config(BaseSettings):
    """Application configuration loaded from environment variables and .env files."""

    # Application settings
    app_name: str = Field(default="ArrEm-sync", description="Application name")
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    dry_run: bool = Field(default=True, description="Run in dry-run mode without making changes")

    # Emby settings
    emby_url: str = Field(..., description="Emby server URL")
    emby_api_key: str = Field(..., description="Emby API key")

    # Multiple Arr instances support
    arr_instances: list[ArrInstanceConfig] = Field(default_factory=list, description="List of configured Arr instances")

    # Sync settings
    batch_size: int = Field(default=50, description="Batch size for processing items")

    # Settings model config
    model_config = SettingsConfigDict(
        env_prefix="ARREM_",
        case_sensitive=False,
        env_file=None,  # We call load_dotenv() explicitly to support custom paths in tests
        extra="ignore",
    )

    @field_validator("dry_run", mode="before")
    @classmethod
    def _coerce_dry_run(cls, v: Any) -> bool | Any:
        """Coerce string env values into booleans.

        - true/1/yes/on (case-insensitive) => True
        - false/0/no/off => False
        - invalid or empty strings => False
        - If value not provided (uses default), validator is skipped.
        """
        if isinstance(v, str):
            s = v.strip().lower()
            if s in {"true", "1", "yes", "on"}:
                return True
            if s in {"false", "0", "no", "off", ""}:
                return False
            return False
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()


def _collect_numbered_instances(env_get: Any) -> list[ArrInstanceConfig]:
    """Collect Arr instances from numbered env vars ARREM_ARR_N_*.

    We keep the existing numbering rule: stop at the first gap.
    """
    instances: list[ArrInstanceConfig] = []
    idx = 1
    while True:
        t = env_get(f"ARREM_ARR_{idx}_TYPE")
        u = env_get(f"ARREM_ARR_{idx}_URL")
        k = env_get(f"ARREM_ARR_{idx}_API_KEY")
        n = env_get(f"ARREM_ARR_{idx}_NAME")
        if t and u and k:
            instances.append(ArrInstanceConfig(type=t, url=u, api_key=k, name=n))
            logger.debug(f"Configured Arr instance {idx}: {t} ({n or 'Unnamed'})")
            idx += 1
        else:
            break
    return instances


def get_config() -> Config:
    """Load configuration using pydantic-settings and maintain friendly errors.

    - Loads a .env if present via python-dotenv (keeps tests that override path working).
    - Supports numbered Arr instances via ARREM_ARR_N_* variables.
    - Preserves human-readable error handling in callers.
    """
    # Load .env file if present (tests may monkeypatch this)
    load_dotenv()

    # Build settings, then inject numbered instances
    try:
        settings = Config()  # type: ignore[call-arg]
    except ValidationError as e:
        # Re-raise for the CLI error formatter to present nicely
        raise e

    # Merge numbered instances if any (pydantic-settings won't parse these by default)
    # We read from the environment via os.getenv semantics through dotenv already loaded.
    import os

    numbered = _collect_numbered_instances(os.getenv)
    if not numbered:
        # If there are no numbered instances, keep behavior identical to before: error out.
        raise ValueError(
            "No Arr instances configured. Please set numbered instances: "
            "ARREM_ARR_1_TYPE, ARREM_ARR_1_URL, ARREM_ARR_1_API_KEY, etc."
        )

    # Return a new settings object merging existing fields with numbered instances
    # Settings are immutable-like; construct a new object with arr_instances replaced
    data = settings.model_dump()
    data["arr_instances"] = numbered
    return Config.model_validate(data)
