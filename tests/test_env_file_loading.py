"""Tests for environment file loading."""

import os
import tempfile
from unittest.mock import patch

from arr_tagsync.config import get_config


class TestEnvFileLoading:
    """Test cases for .env file loading."""

    def test_env_file_loading(self):
        """Test that .env file variables are loaded correctly."""
        # Create a temporary .env file
        env_content = """TAGSYNC_LOG_LEVEL=DEBUG
TAGSYNC_DRY_RUN=true
TAGSYNC_BATCH_SIZE=25
TAGSYNC_EMBY_URL=http://test-emby:8096
TAGSYNC_EMBY_API_KEY=test-api-key
TAGSYNC_ARR_TYPE=radarr
TAGSYNC_ARR_URL=http://test-radarr:7878
TAGSYNC_ARR_API_KEY=test-radarr-key
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_file_path = os.path.join(temp_dir, ".env")

            # Write .env file
            with open(env_file_path, "w") as f:
                f.write(env_content)

            # Mock load_dotenv to load from our specific file
            with patch("arr_tagsync.config.load_dotenv") as mock_load_dotenv:

                def mock_dotenv(*args, **kwargs):
                    from dotenv import load_dotenv as real_load_dotenv

                    return real_load_dotenv(env_file_path)

                mock_load_dotenv.side_effect = mock_dotenv

                # Clear any existing TAGSYNC_ environment variables
                with patch.dict(
                    os.environ,
                    {k: v for k, v in os.environ.items() if not k.startswith("TAGSYNC_")},
                    clear=True,
                ):
                    # Load config (should load from .env file)
                    config = get_config()

                    # Verify values from .env file were loaded
                    assert config.log_level == "DEBUG"
                    assert config.dry_run is True
                    assert config.batch_size == 25
                    assert config.emby_url == "http://test-emby:8096"
                    assert config.emby_api_key == "test-api-key"
                    assert config.arr_type == "radarr"
                    assert config.arr_url == "http://test-radarr:7878"
                    assert config.arr_api_key == "test-radarr-key"

    def test_env_variables_override_env_file(self):
        """Test that environment variables override .env file values."""
        # Create a temporary .env file
        env_content = """TAGSYNC_LOG_LEVEL=INFO
TAGSYNC_DRY_RUN=false
TAGSYNC_EMBY_URL=http://env-file-emby:8096
TAGSYNC_EMBY_API_KEY=env-file-api-key
TAGSYNC_ARR_TYPE=radarr
TAGSYNC_ARR_URL=http://env-file-radarr:7878
TAGSYNC_ARR_API_KEY=env-file-radarr-key
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_file_path = os.path.join(temp_dir, ".env")

            # Write .env file
            with open(env_file_path, "w") as f:
                f.write(env_content)

            # Set environment variables that should override .env file
            env_overrides = {
                "TAGSYNC_LOG_LEVEL": "DEBUG",
                "TAGSYNC_DRY_RUN": "true",
                "TAGSYNC_EMBY_URL": "http://override-emby:8096",
                "TAGSYNC_EMBY_API_KEY": "override-api-key",
                "TAGSYNC_ARR_TYPE": "sonarr",
                "TAGSYNC_ARR_URL": "http://override-sonarr:8989",
                "TAGSYNC_ARR_API_KEY": "override-sonarr-key",
            }

            # Mock load_dotenv to load from our specific file first
            with patch("arr_tagsync.config.load_dotenv") as mock_load_dotenv:

                def mock_dotenv(*args, **kwargs):
                    from dotenv import load_dotenv as real_load_dotenv

                    return real_load_dotenv(env_file_path)

                mock_load_dotenv.side_effect = mock_dotenv

                # Clear existing TAGSYNC_ vars and set our overrides
                clean_env = {k: v for k, v in os.environ.items() if not k.startswith("TAGSYNC_")}
                clean_env.update(env_overrides)

                with patch.dict(os.environ, clean_env, clear=True):
                    # Load config (environment variables should override .env file)
                    config = get_config()

                    # Verify environment variables overrode .env file values
                    assert config.log_level == "DEBUG"
                    assert config.dry_run is True
                    assert config.emby_url == "http://override-emby:8096"
                    assert config.emby_api_key == "override-api-key"
                    assert config.arr_type == "sonarr"
                    assert config.arr_url == "http://override-sonarr:8989"
                    assert config.arr_api_key == "override-sonarr-key"

    def test_config_without_env_file(self):
        """Test config works without .env file (using only env variables)."""
        # Set required environment variables
        env_vars = {
            "TAGSYNC_EMBY_URL": "http://direct-emby:8096",
            "TAGSYNC_EMBY_API_KEY": "direct-api-key",
            "TAGSYNC_ARR_TYPE": "radarr",
            "TAGSYNC_ARR_URL": "http://direct-radarr:7878",
            "TAGSYNC_ARR_API_KEY": "direct-radarr-key",
        }

        # Mock load_dotenv to do nothing (simulate no .env file)
        with (
            patch("arr_tagsync.config.load_dotenv"),
            patch.dict(os.environ, env_vars, clear=True),
        ):
            # Load config (should work without .env file)
            config = get_config()

            # Verify values from environment variables
            assert config.emby_url == "http://direct-emby:8096"
            assert config.emby_api_key == "direct-api-key"
            assert config.arr_type == "radarr"
            assert config.arr_url == "http://direct-radarr:7878"
            assert config.arr_api_key == "direct-radarr-key"
            # Verify defaults are used for optional values
            assert config.log_level == "INFO"
            assert config.dry_run is False
            assert config.batch_size == 50
