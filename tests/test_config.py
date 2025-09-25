"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from arrem_sync.config import Config, get_config


class TestConfig:
    """Test configuration class."""

    def test_config_defaults(self):
        """Test default configuration values."""
        # Create minimal config with required fields
        config = Config(
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
        )

        assert config.app_name == "ArrEm-sync"
        assert config.log_level == "INFO"
        assert config.dry_run is True
        assert config.batch_size == 50

    def test_config_validation_arr_type(self):
        """Test arr_type validation."""
        # Valid arr_type
        config = Config(
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
        )
        assert config.arr_type == "radarr"

        # Invalid arr_type should raise ValidationError
        with pytest.raises(ValidationError):
            Config(
                emby_url="http://localhost:8096",
                emby_api_key="test_key",
                arr_type="invalid",
                arr_url="http://localhost:7878",
                arr_api_key="test_key",
            )

    def test_config_validation_log_level(self):
        """Test log_level validation."""
        # Valid log_level
        config = Config(
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            log_level="DEBUG",
        )
        assert config.log_level == "DEBUG"

        # Invalid log_level should raise ValidationError
        with pytest.raises(ValidationError):
            Config(
                emby_url="http://localhost:8096",
                emby_api_key="test_key",
                arr_type="radarr",
                arr_url="http://localhost:7878",
                arr_api_key="test_key",
                log_level="INVALID",
            )

    def test_config_case_insensitive(self):
        """Test case insensitive configuration."""
        config = Config(
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            arr_type="RADARR",  # Uppercase
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            log_level="debug",  # Lowercase
        )

        assert config.arr_type == "radarr"  # Should be normalized to lowercase
        assert config.log_level == "DEBUG"  # Should be normalized to uppercase

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Config()  # Missing all required fields

    def test_get_config_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("ARREM_EMBY_URL", "http://test-emby:8096")
        monkeypatch.setenv("ARREM_EMBY_API_KEY", "test_emby_key")
        monkeypatch.setenv("ARREM_ARR_TYPE", "sonarr")
        monkeypatch.setenv("ARREM_ARR_URL", "http://test-sonarr:8989")
        monkeypatch.setenv("ARREM_ARR_API_KEY", "test_sonarr_key")
        monkeypatch.setenv("ARREM_DRY_RUN", "true")
        monkeypatch.setenv("ARREM_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("ARREM_BATCH_SIZE", "25")

        config = get_config()

        assert config.emby_url == "http://test-emby:8096"
        assert config.emby_api_key == "test_emby_key"
        assert config.arr_type == "sonarr"
        assert config.arr_url == "http://test-sonarr:8989"
        assert config.arr_api_key == "test_sonarr_key"
        assert config.dry_run is True
        assert config.log_level == "DEBUG"
        assert config.batch_size == 25
