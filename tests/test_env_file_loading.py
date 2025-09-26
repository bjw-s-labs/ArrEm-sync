"""Tests for environment file loading."""

import os
import tempfile
from unittest.mock import patch

from arrem_sync.config import get_config


class TestEnvFileLoading:
    """Test cases for .env file loading."""

    def test_env_file_loading(self):
        """Test that .env file variables are loaded correctly."""
        # Create a temporary .env file
        env_content = """ARREM_LOG_LEVEL=DEBUG
ARREM_DRY_RUN=true
ARREM_BATCH_SIZE=25
ARREM_EMBY_URL=http://test-emby:8096
ARREM_EMBY_API_KEY=test-api-key
ARREM_ARR_1_TYPE=radarr
ARREM_ARR_1_URL=http://test-radarr:7878
ARREM_ARR_1_API_KEY=test-radarr-key
ARREM_ARR_1_NAME=Test Radarr
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_file_path = os.path.join(temp_dir, ".env")

            # Write .env file
            with open(env_file_path, "w") as f:
                f.write(env_content)

            # Mock load_dotenv to load from our specific file
            with patch("arrem_sync.config.load_dotenv") as mock_load_dotenv:

                def mock_dotenv(*args, **kwargs):
                    from dotenv import load_dotenv as real_load_dotenv

                    return real_load_dotenv(env_file_path)

                mock_load_dotenv.side_effect = mock_dotenv

                # Clear any existing ARREM_ environment variables
                with patch.dict(
                    os.environ,
                    {k: v for k, v in os.environ.items() if not k.startswith("ARREM_")},
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
                    assert len(config.arr_instances) == 1
                    assert config.arr_instances[0].type == "radarr"
                    assert config.arr_instances[0].url == "http://test-radarr:7878"
                    assert config.arr_instances[0].api_key == "test-radarr-key"
                    assert config.arr_instances[0].name == "Test Radarr"

    def test_env_variables_override_env_file(self):
        """Test that environment variables override .env file values."""
        # Create a temporary .env file
        env_content = """ARREM_LOG_LEVEL=INFO
ARREM_DRY_RUN=true
ARREM_EMBY_URL=http://env-file-emby:8096
ARREM_EMBY_API_KEY=env-file-api-key
ARREM_ARR_1_TYPE=radarr
ARREM_ARR_1_URL=http://env-file-radarr:7878
ARREM_ARR_1_API_KEY=env-file-radarr-key
ARREM_ARR_1_NAME=Env File Radarr
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_file_path = os.path.join(temp_dir, ".env")

            # Write .env file
            with open(env_file_path, "w") as f:
                f.write(env_content)

            # Set environment variables that should override .env file
            env_overrides = {
                "ARREM_LOG_LEVEL": "DEBUG",
                "ARREM_DRY_RUN": "true",
                "ARREM_EMBY_URL": "http://override-emby:8096",
                "ARREM_EMBY_API_KEY": "override-api-key",
                "ARREM_ARR_1_TYPE": "sonarr",
                "ARREM_ARR_1_URL": "http://override-sonarr:8989",
                "ARREM_ARR_1_API_KEY": "override-sonarr-key",
                "ARREM_ARR_1_NAME": "Override Sonarr",
            }

            # Mock load_dotenv to load from our specific file first
            with patch("arrem_sync.config.load_dotenv") as mock_load_dotenv:

                def mock_dotenv(*args, **kwargs):
                    from dotenv import load_dotenv as real_load_dotenv

                    return real_load_dotenv(env_file_path)

                mock_load_dotenv.side_effect = mock_dotenv

                # Clear existing ARREM_ vars and set our overrides
                clean_env = {k: v for k, v in os.environ.items() if not k.startswith("ARREM_")}
                clean_env.update(env_overrides)

                with patch.dict(os.environ, clean_env, clear=True):
                    # Load config (environment variables should override .env file)
                    config = get_config()

                    # Verify environment variables overrode .env file values
                    assert config.log_level == "DEBUG"
                    assert config.dry_run is True
                    assert config.emby_url == "http://override-emby:8096"
                    assert config.emby_api_key == "override-api-key"
                    assert len(config.arr_instances) == 1
                    assert config.arr_instances[0].type == "sonarr"
                    assert config.arr_instances[0].url == "http://override-sonarr:8989"
                    assert config.arr_instances[0].api_key == "override-sonarr-key"
                    assert config.arr_instances[0].name == "Override Sonarr"

    def test_config_without_env_file(self):
        """Test config works without .env file (using only env variables)."""
        # Set required environment variables
        env_vars = {
            "ARREM_EMBY_URL": "http://direct-emby:8096",
            "ARREM_EMBY_API_KEY": "direct-api-key",
            "ARREM_ARR_1_TYPE": "radarr",
            "ARREM_ARR_1_URL": "http://direct-radarr:7878",
            "ARREM_ARR_1_API_KEY": "direct-radarr-key",
            "ARREM_ARR_1_NAME": "Direct Radarr",
        }

        # Mock load_dotenv to do nothing (simulate no .env file)
        with (
            patch("arrem_sync.config.load_dotenv"),
            patch.dict(os.environ, env_vars, clear=True),
        ):
            # Load config (should work without .env file)
            config = get_config()

            # Verify values from environment variables
            assert config.emby_url == "http://direct-emby:8096"
            assert config.emby_api_key == "direct-api-key"
            assert len(config.arr_instances) == 1
            assert config.arr_instances[0].type == "radarr"
            assert config.arr_instances[0].url == "http://direct-radarr:7878"
            assert config.arr_instances[0].api_key == "direct-radarr-key"
            assert config.arr_instances[0].name == "Direct Radarr"
            # Verify defaults are used for optional values
            assert config.log_level == "INFO"
            assert config.dry_run is True
            assert config.batch_size == 50
