"""Tests for CLI module."""

import logging
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from pydantic import ValidationError

from arrem_sync.arr_client import ArrClient
from arrem_sync.cli import cli, create_clients, setup_logging
from arrem_sync.config import Config
from arrem_sync.emby_client import EmbyClient


class TestCLIUtilities:
    """Test CLI utility functions."""

    def test_setup_logging(self, caplog):
        """Test logging setup."""
        with caplog.at_level(logging.DEBUG):
            setup_logging("DEBUG")

            # Test that logging is configured correctly
            logger = logging.getLogger("test_logger")
            logger.info("Test message")

            assert any("Test message" in record.message for record in caplog.records)

    def test_setup_logging_different_levels(self):
        """Test logging setup with different levels."""
        # Store original level to restore later
        original_level = logging.getLogger().level

        try:
            # Test INFO level
            setup_logging("INFO")
            root_logger = logging.getLogger()
            # Check that at least one handler has INFO level or below
            has_info_level = (
                any(handler.level <= logging.INFO for handler in root_logger.handlers)
                or root_logger.level <= logging.INFO
            )
            assert has_info_level

            # Test WARNING level
            setup_logging("WARNING")
            has_warning_level = (
                any(handler.level <= logging.WARNING for handler in root_logger.handlers)
                or root_logger.level <= logging.WARNING
            )
            assert has_warning_level

            # Test ERROR level
            setup_logging("ERROR")
            has_error_level = (
                any(handler.level <= logging.ERROR for handler in root_logger.handlers)
                or root_logger.level <= logging.ERROR
            )
            assert has_error_level
        finally:
            # Restore original logging level
            logging.getLogger().setLevel(original_level)

    def test_setup_logging_uses_stdout(self, caplog):
        """Test that logging outputs to stdout."""
        with caplog.at_level(logging.INFO):
            setup_logging("INFO")
            logger = logging.getLogger("test_cli")
            logger.info("Test output to stdout")

            # Check that the message appears in captured logs
            assert any("Test output to stdout" in record.message for record in caplog.records)

    def test_create_clients(self):
        """Test client creation from config."""
        config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_arr_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_emby_key",
        )

        arr_client, emby_client = create_clients(config)

        # Verify clients are created correctly
        assert isinstance(arr_client, ArrClient)
        assert isinstance(emby_client, EmbyClient)

        # Check that clients have correct configuration
        assert arr_client.base_url == "http://localhost:7878"
        assert arr_client.api_key == "test_arr_key"
        assert arr_client.arr_type == "radarr"

        assert emby_client.server_url == "http://localhost:8096"
        assert emby_client.api_key == "test_emby_key"

    @patch("arrem_sync.cli.ArrClient")
    @patch("arrem_sync.cli.EmbyClient")
    def test_create_clients_initialization_calls(self, mock_emby_client, mock_arr_client):
        """Test that clients are initialized with correct parameters."""
        config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_arr_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_emby_key",
        )

        create_clients(config)

        # Verify ArrClient was called with correct parameters
        mock_arr_client.assert_called_once_with(
            arr_type="radarr", base_url="http://localhost:7878", api_key="test_arr_key"
        )

        # Verify EmbyClient was called with correct parameters
        mock_emby_client.assert_called_once_with(server_url="http://localhost:8096", api_key="test_emby_key")


class TestCLICommands:
    """Test CLI commands using Click's test runner."""

    @patch("arrem_sync.cli.get_config")
    @patch("arrem_sync.cli.create_clients")
    @patch("arrem_sync.cli.TagSyncService")
    def test_sync_command_success(self, mock_sync_service, mock_create_clients, mock_get_config):
        """Test successful sync command execution."""

        # Mock configuration
        mock_config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            dry_run=False,
            log_level="INFO",
            batch_size=10,
            app_name="ArrEm-sync",
        )
        mock_get_config.return_value = mock_config

        # Mock clients
        mock_arr_client = MagicMock()
        mock_emby_client = MagicMock()
        mock_create_clients.return_value = (mock_arr_client, mock_emby_client)

        # Mock sync service
        mock_service_instance = MagicMock()
        mock_sync_service.return_value = mock_service_instance
        mock_service_instance.sync_all_tags.return_value = {
            "total_items": 100,
            "processed_items": 100,
            "successful_syncs": 80,
            "already_synced": 15,
            "no_tags_to_sync": 5,
            "not_in_emby": 0,
            "failed_syncs": 0,
            "errors": [],
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["sync"])

        # Should exit successfully
        assert result.exit_code == 0
        assert "SYNCHRONIZATION SUMMARY" in result.output
        assert "Total items: 100" in result.output
        assert "Successful syncs: 80" in result.output

        # Verify service was called correctly
        mock_sync_service.assert_called_once_with(
            arr_client=mock_arr_client, emby_client=mock_emby_client, dry_run=False
        )
        mock_service_instance.sync_all_tags.assert_called_once_with(batch_size=10)

    @patch("arrem_sync.cli.get_config")
    @patch("arrem_sync.cli.create_clients")
    @patch("arrem_sync.cli.TagSyncService")
    def test_sync_command_with_dry_run_flag(self, mock_sync_service, mock_create_clients, mock_get_config):
        """Test sync command with --dry-run flag."""

        mock_config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            dry_run=False,  # Initially false
            log_level="INFO",
            batch_size=10,
            app_name="ArrEm-sync",
        )
        mock_get_config.return_value = mock_config

        mock_arr_client = MagicMock()
        mock_emby_client = MagicMock()
        mock_create_clients.return_value = (mock_arr_client, mock_emby_client)

        mock_service_instance = MagicMock()
        mock_sync_service.return_value = mock_service_instance
        mock_service_instance.sync_all_tags.return_value = {
            "total_items": 10,
            "processed_items": 10,
            "successful_syncs": 0,
            "already_synced": 0,
            "no_tags_to_sync": 0,
            "not_in_emby": 0,
            "failed_syncs": 0,
            "errors": [],
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["sync", "--dry-run"])

        assert result.exit_code == 0
        # Config should be modified to have dry_run=True
        assert mock_config.dry_run is True

        # Service should be created with dry_run=True
        mock_sync_service.assert_called_once_with(
            arr_client=mock_arr_client, emby_client=mock_emby_client, dry_run=True
        )

    @patch("arrem_sync.cli.get_config")
    @patch("arrem_sync.cli.create_clients")
    @patch("arrem_sync.cli.TagSyncService")
    def test_sync_command_with_failures(self, mock_sync_service, mock_create_clients, mock_get_config):
        """Test sync command when there are failures."""

        mock_config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            dry_run=False,
            log_level="INFO",
            batch_size=10,
            app_name="ArrEm-sync",
        )
        mock_get_config.return_value = mock_config

        mock_arr_client = MagicMock()
        mock_emby_client = MagicMock()
        mock_create_clients.return_value = (mock_arr_client, mock_emby_client)

        mock_service_instance = MagicMock()
        mock_sync_service.return_value = mock_service_instance
        mock_service_instance.sync_all_tags.return_value = {
            "total_items": 50,
            "processed_items": 50,
            "successful_syncs": 40,
            "already_synced": 5,
            "no_tags_to_sync": 0,
            "not_in_emby": 2,
            "failed_syncs": 3,
            "errors": ["Error 1", "Error 2", "Error 3"],
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["sync"])

        # Should exit with code 1 due to failures
        assert result.exit_code == 1
        assert "Failed syncs: 3" in result.output
        assert "Errors (3):" in result.output
        assert "Error 1" in result.output

    @patch("arrem_sync.cli.get_config")
    def test_sync_command_config_error(self, mock_get_config):
        """Test sync command with configuration error."""

        # Mock a ValidationError
        mock_get_config.side_effect = ValidationError.from_exception_data(
            "test", [{"type": "missing", "loc": ("arr_api_key",), "msg": "Field required"}]
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["sync"])

        assert result.exit_code == 1
        assert "Configuration Error:" in result.output

    @patch("arrem_sync.cli.get_config")
    @patch("arrem_sync.cli.create_clients")
    def test_test_command_success(self, mock_create_clients, mock_get_config):
        """Test successful test command execution."""

        mock_config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            log_level="INFO",
        )
        mock_get_config.return_value = mock_config

        mock_arr_client = MagicMock()
        mock_arr_client.test_connection.return_value = True
        mock_emby_client = MagicMock()
        mock_emby_client.test_connection.return_value = True
        mock_create_clients.return_value = (mock_arr_client, mock_emby_client)

        runner = CliRunner()
        result = runner.invoke(cli, ["test"])

        assert result.exit_code == 0
        assert "Testing radarr connection... ✓ Success" in result.output
        assert "Testing Emby connection... ✓ Success" in result.output
        assert "All connections successful!" in result.output

    @patch("arrem_sync.cli.get_config")
    @patch("arrem_sync.cli.create_clients")
    def test_test_command_arr_failure(self, mock_create_clients, mock_get_config):
        """Test test command with Arr connection failure."""

        mock_config = Config(
            arr_type="sonarr",
            arr_url="http://localhost:8989",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            log_level="INFO",
        )
        mock_get_config.return_value = mock_config

        mock_arr_client = MagicMock()
        mock_arr_client.test_connection.return_value = False  # Connection fails
        mock_emby_client = MagicMock()
        mock_create_clients.return_value = (mock_arr_client, mock_emby_client)

        runner = CliRunner()
        result = runner.invoke(cli, ["test"])

        assert result.exit_code == 1
        assert "Testing sonarr connection... ✗ Failed" in result.output

    @patch("arrem_sync.cli.get_config")
    @patch("arrem_sync.cli.create_clients")
    def test_test_command_emby_failure(self, mock_create_clients, mock_get_config):
        """Test test command with Emby connection failure."""

        mock_config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            log_level="INFO",
        )
        mock_get_config.return_value = mock_config

        mock_arr_client = MagicMock()
        mock_arr_client.test_connection.return_value = True
        mock_emby_client = MagicMock()
        mock_emby_client.test_connection.return_value = False  # Emby connection fails
        mock_create_clients.return_value = (mock_arr_client, mock_emby_client)

        runner = CliRunner()
        result = runner.invoke(cli, ["test"])

        assert result.exit_code == 1
        assert "Testing radarr connection... ✓ Success" in result.output
        assert "Testing Emby connection... ✗ Failed" in result.output

    @patch("arrem_sync.cli.get_config")
    def test_test_command_config_error(self, mock_get_config):
        """Test test command with configuration error."""

        mock_get_config.side_effect = ValidationError.from_exception_data(
            "test", [{"type": "missing", "loc": ("emby_api_key",), "msg": "Field required"}]
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["test"])

        assert result.exit_code == 1
        assert "Configuration Error:" in result.output

    @patch("arrem_sync.cli.get_config")
    @patch("arrem_sync.cli.create_clients")
    @patch("arrem_sync.cli.TagSyncService")
    def test_sync_command_unexpected_error(self, mock_sync_service, mock_create_clients, mock_get_config):
        """Test sync command with unexpected error."""
        from click.testing import CliRunner

        mock_config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            dry_run=False,
            log_level="INFO",
            batch_size=10,
            app_name="ArrEm-sync",
        )
        mock_get_config.return_value = mock_config

        mock_arr_client = MagicMock()
        mock_emby_client = MagicMock()
        mock_create_clients.return_value = (mock_arr_client, mock_emby_client)

        # Mock an unexpected exception
        mock_sync_service.side_effect = RuntimeError("Unexpected error occurred")

        runner = CliRunner()
        result = runner.invoke(cli, ["sync"])

        assert result.exit_code == 1
        assert "Unexpected error: Unexpected error occurred" in result.output

    @patch("arrem_sync.cli.get_config")
    @patch("arrem_sync.cli.create_clients")
    def test_test_command_unexpected_error(self, mock_create_clients, mock_get_config):
        """Test test command with unexpected error."""

        mock_config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            log_level="INFO",
        )
        mock_get_config.return_value = mock_config

        # Mock an unexpected exception during client creation
        mock_create_clients.side_effect = RuntimeError("Connection setup failed")

        runner = CliRunner()
        result = runner.invoke(cli, ["test"])

        assert result.exit_code == 1
        assert "Unexpected error: Connection setup failed" in result.output

    def test_cli_version(self):
        """Test CLI version option."""

        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_sync_no_dry_run_option(self):
        """Test that --no-dry-run option is available and works."""
        runner = CliRunner()

        # Test that --no-dry-run appears in help
        result = runner.invoke(cli, ["sync", "--help"])
        assert result.exit_code == 0
        assert "--no-dry-run" in result.output
        assert "Disable dry-run mode to make actual changes" in result.output

    def test_sync_conflicting_dry_run_options(self):
        """Test that --dry-run and --no-dry-run cannot be used together."""
        runner = CliRunner()

        result = runner.invoke(cli, ["sync", "--dry-run", "--no-dry-run"])
        assert result.exit_code != 0
        assert "Cannot specify both --dry-run and --no-dry-run" in result.output

    @patch("arrem_sync.cli.get_config")
    def test_sync_no_dry_run_overrides_config(self, mock_get_config):
        """Test that --no-dry-run overrides config default."""
        # Mock configuration with default dry_run=True
        mock_config = Config(
            arr_type="radarr",
            arr_url="http://localhost:7878",
            arr_api_key="test_key",
            emby_url="http://localhost:8096",
            emby_api_key="test_key",
            dry_run=True,  # Default is now True
        )
        mock_get_config.return_value = mock_config

        runner = CliRunner()

        # This should fail due to missing configuration, but we just want to test
        # that the option parsing works and dry_run gets set to False
        with patch("arrem_sync.cli.create_clients") as mock_create_clients:
            mock_create_clients.side_effect = Exception("Expected test exception")

            result = runner.invoke(cli, ["sync", "--no-dry-run"])
            # The command should fail due to our mock exception, not option parsing
            assert "Expected test exception" in result.output

            # Verify that dry_run was set to False by the --no-dry-run flag
            assert mock_config.dry_run is False
