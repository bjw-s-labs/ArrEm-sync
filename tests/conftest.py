"""Test configuration and fixtures for ArrEm-sync tests."""

import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def isolate_environment():
    """Automatically isolate environment variables for all tests.

    This fixture:
    1. Prevents loading of live .env files
    2. Clears all ARREM_* environment variables
    3. Restores original environment after test
    """
    # Store original environment variables
    original_env = dict(os.environ)

    # Clear all ARREM_* environment variables to ensure test isolation
    for key in list(os.environ.keys()):
        if key.startswith("ARREM_"):
            del os.environ[key]

    # Mock load_dotenv to prevent loading live .env files
    with patch("arrem_sync.config.load_dotenv") as mock_load_dotenv:
        # Make load_dotenv do nothing
        mock_load_dotenv.return_value = True

        try:
            yield
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


@pytest.fixture
def mock_arr_config():
    """Provide a basic Arr instance configuration for testing."""
    from arrem_sync.config import ArrInstanceConfig

    return ArrInstanceConfig(
        type="radarr", url="http://test-radarr:7878", api_key="test_radarr_api_key", name="Test Radarr"
    )


@pytest.fixture
def mock_config(mock_arr_config):
    """Provide a basic Config object for testing."""
    from arrem_sync.config import Config

    return Config(
        emby_url="http://test-emby:8096",
        emby_api_key="test_emby_api_key",
        arr_instances=[mock_arr_config],
        dry_run=True,
        log_level="INFO",
        batch_size=50,
    )


@pytest.fixture
def env_vars():
    """Provide a set of valid environment variables for testing."""
    return {
        "ARREM_ARR_1_TYPE": "radarr",
        "ARREM_ARR_1_URL": "http://test-radarr:7878",
        "ARREM_ARR_1_API_KEY": "test_radarr_api_key",
        "ARREM_ARR_1_NAME": "Test Radarr",
        "ARREM_EMBY_URL": "http://test-emby:8096",
        "ARREM_EMBY_API_KEY": "test_emby_api_key",
        "ARREM_DRY_RUN": "true",
        "ARREM_LOG_LEVEL": "INFO",
        "ARREM_BATCH_SIZE": "50",
    }
