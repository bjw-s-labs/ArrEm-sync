"""Tests for dry-run environment variable functionality."""

import os

import pytest

from arr_tagsync.config import Config, get_config


class TestDryRunEnvironmentVariable:
    """Test dry-run environment variable support."""

    def teardown_method(self):
        """Clean up environment variables after each test."""
        if "TAGSYNC_DRY_RUN" in os.environ:
            del os.environ["TAGSYNC_DRY_RUN"]

    def test_dry_run_env_var_true(self):
        """Test TAGSYNC_DRY_RUN=true sets dry_run to True."""
        os.environ.update(
            {
                "TAGSYNC_DRY_RUN": "true",
                "TAGSYNC_ARR_TYPE": "radarr",
                "TAGSYNC_ARR_URL": "http://localhost:7878",
                "TAGSYNC_ARR_API_KEY": "test_key",
                "TAGSYNC_EMBY_URL": "http://localhost:8096",
                "TAGSYNC_EMBY_API_KEY": "test_key",
            }
        )

        config = get_config()
        assert config.dry_run is True

    def test_dry_run_env_var_false(self):
        """Test TAGSYNC_DRY_RUN=false sets dry_run to False."""
        os.environ.update(
            {
                "TAGSYNC_DRY_RUN": "false",
                "TAGSYNC_ARR_TYPE": "radarr",
                "TAGSYNC_ARR_URL": "http://localhost:7878",
                "TAGSYNC_ARR_API_KEY": "test_key",
                "TAGSYNC_EMBY_URL": "http://localhost:8096",
                "TAGSYNC_EMBY_API_KEY": "test_key",
            }
        )

        config = get_config()
        assert config.dry_run is False

    def test_dry_run_env_var_not_set(self):
        """Test default dry_run value when TAGSYNC_DRY_RUN is not set."""
        # Ensure the environment variable is not set
        if "TAGSYNC_DRY_RUN" in os.environ:
            del os.environ["TAGSYNC_DRY_RUN"]

        os.environ.update(
            {
                "TAGSYNC_ARR_TYPE": "radarr",
                "TAGSYNC_ARR_URL": "http://localhost:7878",
                "TAGSYNC_ARR_API_KEY": "test_key",
                "TAGSYNC_EMBY_URL": "http://localhost:8096",
                "TAGSYNC_EMBY_API_KEY": "test_key",
            }
        )

        config = get_config()
        assert config.dry_run is False

    @pytest.mark.parametrize(
        "env_value,expected",
        [
            ("true", True),
            ("TRUE", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("YES", True),
            ("on", True),
            ("ON", True),
            ("false", False),
            ("FALSE", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("NO", False),
            ("off", False),
            ("OFF", False),
            ("invalid", False),  # Invalid values should default to False
            ("", False),  # Empty string should default to False
        ],
    )
    def test_dry_run_env_var_boolean_variations(self, env_value, expected):
        """Test various boolean representations for TAGSYNC_DRY_RUN."""
        os.environ.update(
            {
                "TAGSYNC_DRY_RUN": env_value,
                "TAGSYNC_ARR_TYPE": "radarr",
                "TAGSYNC_ARR_URL": "http://localhost:7878",
                "TAGSYNC_ARR_API_KEY": "test_key",
                "TAGSYNC_EMBY_URL": "http://localhost:8096",
                "TAGSYNC_EMBY_API_KEY": "test_key",
            }
        )

        config = get_config()
        assert config.dry_run is expected

    def test_dry_run_direct_config_creation(self):
        """Test dry_run parameter when creating Config directly."""
        # Test with dry_run=True
        config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            dry_run=True,
        )
        assert config.dry_run is True

        # Test with dry_run=False
        config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            dry_run=False,
        )
        assert config.dry_run is False

        # Test default value
        config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
        )
        assert config.dry_run is False  # Default should be False
