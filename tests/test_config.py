"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from arrem_sync.config import Config, get_config


class TestConfig:
    """Test configuration class."""

    def test_config_defaults(self):
        """Test default configuration values."""
        # Create minimal config with required fields
        from arrem_sync.config import ArrInstanceConfig

        config = Config(
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            arr_instances=[ArrInstanceConfig(type="radarr", url="http://localhost:7878", api_key="test_key")],
        )

        assert config.app_name == "ArrEm-sync"
        assert config.log_level == "INFO"
        assert config.dry_run is True
        assert config.batch_size == 50

    def test_config_validation_arr_type(self):
        """Test arr_type validation."""
        from arrem_sync.config import ArrInstanceConfig

        # Valid arr_type
        config = Config(
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            arr_instances=[
                ArrInstanceConfig(type="radarr", url="http://localhost:7878", api_key="test_key", name="Test Radarr")
            ],
        )
        assert len(config.arr_instances) == 1
        assert config.arr_instances[0].type == "radarr"

        # Invalid arr_type should raise ValidationError
        with pytest.raises(ValidationError):
            Config(
                emby_url="http://localhost:8096",
                emby_api_key="test_key",
                arr_instances=[
                    ArrInstanceConfig(
                        type="invalid", url="http://localhost:7878", api_key="test_key", name="Test Invalid"
                    )
                ],
            )

    def test_config_validation_log_level(self):
        """Test log_level validation."""
        # Valid log_level
        from arrem_sync.config import ArrInstanceConfig

        config = Config(
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            arr_instances=[ArrInstanceConfig(type="radarr", url="http://localhost:7878", api_key="test_key")],
            log_level="DEBUG",
        )
        assert config.log_level == "DEBUG"

        # Invalid log_level should raise ValidationError
        from arrem_sync.config import ArrInstanceConfig

        with pytest.raises(ValidationError):
            Config(
                emby_url="http://localhost:8096",
                emby_api_key="test_key",
                arr_instances=[
                    ArrInstanceConfig(
                        type="radarr", url="http://localhost:7878", api_key="test_key", name="Test Radarr"
                    )
                ],
                log_level="INVALID",
            )

    def test_config_case_insensitive(self):
        """Test case insensitive configuration."""
        from arrem_sync.config import ArrInstanceConfig

        config = Config(
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            arr_instances=[
                ArrInstanceConfig(
                    type="RADARR",  # Uppercase
                    url="http://localhost:7878",
                    api_key="test_key",
                    name="Test Radarr",
                )
            ],
            log_level="debug",  # Lowercase
        )

        assert config.arr_instances[0].type == "radarr"  # Should be normalized to lowercase
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
        monkeypatch.setenv("ARREM_ARR_1_TYPE", "sonarr")
        monkeypatch.setenv("ARREM_ARR_1_URL", "http://test-sonarr:8989")
        monkeypatch.setenv("ARREM_ARR_1_API_KEY", "test_sonarr_key")
        monkeypatch.setenv("ARREM_ARR_1_NAME", "Test Sonarr")
        monkeypatch.setenv("ARREM_DRY_RUN", "true")
        monkeypatch.setenv("ARREM_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("ARREM_BATCH_SIZE", "25")

        config = get_config()

        assert config.emby_url == "http://test-emby:8096"
        assert config.emby_api_key == "test_emby_key"
        assert len(config.arr_instances) == 1
        assert config.arr_instances[0].type == "sonarr"
        assert config.arr_instances[0].url == "http://test-sonarr:8989"
        assert config.arr_instances[0].api_key == "test_sonarr_key"
        assert config.arr_instances[0].name == "Test Sonarr"
        assert config.dry_run is True
        assert config.log_level == "DEBUG"
        assert config.batch_size == 25
