"""Integration tests for multi-instance CLI functionality."""

import os
from unittest.mock import patch

from click.testing import CliRunner

from arrem_sync.cli import cli


class TestMultiInstanceCLI:
    """Test CLI with multi-instance configuration."""

    def test_test_command_with_single_numbered_instance(self):
        """Test the test command with single numbered instance configuration."""
        env_vars = {
            "ARREM_EMBY_URL": "http://localhost:8096",
            "ARREM_EMBY_API_KEY": "test_emby_key",
            "ARREM_ARR_1_TYPE": "radarr",
            "ARREM_ARR_1_URL": "http://localhost:7878",
            "ARREM_ARR_1_API_KEY": "test_arr_key",
            "ARREM_ARR_1_NAME": "Main Radarr",
        }

        with (
            patch.dict(os.environ, env_vars, clear=True),
            patch("arrem_sync.config.load_dotenv"),
            patch("arrem_sync.multi_sync_service.MultiTagSyncService.test_all_connections") as mock_test,
        ):
            # Mock successful connections
            mock_test.return_value = {
                "emby": True,
                "radarr_1": True,
            }

            runner = CliRunner()
            result = runner.invoke(cli, ["test"])

            assert result.exit_code == 0
            assert "All connections successful! (1 Arr instance(s) + Emby)" in result.output
            assert "Testing Emby connection... ✓ Success" in result.output
            assert "Testing Main Radarr (radarr)... ✓ Success" in result.output

    def test_test_command_with_multiple_numbered_instances(self):
        """Test the test command with multiple numbered instances."""
        env_vars = {
            "ARREM_EMBY_URL": "http://localhost:8096",
            "ARREM_EMBY_API_KEY": "test_emby_key",
            "ARREM_ARR_1_TYPE": "radarr",
            "ARREM_ARR_1_URL": "http://localhost:7878",
            "ARREM_ARR_1_API_KEY": "test_radarr_key",
            "ARREM_ARR_1_NAME": "Main Radarr",
            "ARREM_ARR_2_TYPE": "sonarr",
            "ARREM_ARR_2_URL": "http://localhost:8989",
            "ARREM_ARR_2_API_KEY": "test_sonarr_key",
            "ARREM_ARR_2_NAME": "Main Sonarr",
        }

        with (
            patch.dict(os.environ, env_vars, clear=True),
            patch("arrem_sync.config.load_dotenv"),
            patch("arrem_sync.multi_sync_service.MultiTagSyncService.test_all_connections") as mock_test,
        ):
            # Mock successful connections
            mock_test.return_value = {
                "emby": True,
                "radarr_1": True,
                "sonarr_2": True,
            }

            runner = CliRunner()
            result = runner.invoke(cli, ["test"])

            assert result.exit_code == 0
            assert "All connections successful! (2 Arr instance(s) + Emby)" in result.output
            assert "Testing Emby connection... ✓ Success" in result.output
            assert "Testing Main Radarr (radarr)... ✓ Success" in result.output
            assert "Testing Main Sonarr (sonarr)... ✓ Success" in result.output

    def test_test_command_with_partial_failures(self):
        """Test the test command when some connections fail."""
        env_vars = {
            "ARREM_EMBY_URL": "http://localhost:8096",
            "ARREM_EMBY_API_KEY": "test_emby_key",
            "ARREM_ARR_1_TYPE": "radarr",
            "ARREM_ARR_1_URL": "http://localhost:7878",
            "ARREM_ARR_1_API_KEY": "test_radarr_key",
            "ARREM_ARR_1_NAME": "Main Radarr",
            "ARREM_ARR_2_TYPE": "sonarr",
            "ARREM_ARR_2_URL": "http://bad-url:8989",
            "ARREM_ARR_2_API_KEY": "test_sonarr_key",
            "ARREM_ARR_2_NAME": "Broken Sonarr",
        }

        with (
            patch.dict(os.environ, env_vars, clear=True),
            patch("arrem_sync.config.load_dotenv"),
            patch("arrem_sync.multi_sync_service.MultiTagSyncService.test_all_connections") as mock_test,
        ):
            # Mock mixed connection results
            mock_test.return_value = {
                "emby": True,
                "radarr_1": True,
                "sonarr_2": False,  # This one fails
            }

            runner = CliRunner()
            result = runner.invoke(cli, ["test"])

            assert result.exit_code == 1
            assert "Some connections failed!" in result.output
            assert "Testing Emby connection... ✓ Success" in result.output
            assert "Testing Main Radarr (radarr)... ✓ Success" in result.output
            assert "Testing Broken Sonarr (sonarr)... ✗ Failed" in result.output
