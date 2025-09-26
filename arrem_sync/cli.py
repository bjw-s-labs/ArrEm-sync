"""Main CLI application for ArrEm-sync."""

import logging
import sys
from contextlib import ExitStack
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable

import click
from pydantic import ValidationError

from .client_factory import create_clients
from .config import get_config
from .errors import handle_config_error
from .multi_sync_service import MultiTagSyncService
from .version import __version__


class DefaultGroup(click.Group):
    """Click Group with a default subcommand (sync).

    If no subcommand is given, or the first token is an option (e.g. "--dry-run"),
    this group will insert the default command so those options apply to it.
    Group-level help/version flags are respected and will not trigger the default.
    """

    default_command = "sync"

    def parse_args(self, ctx: click.Context, args: list[str]) -> None:  # type: ignore[override]
        if self.default_command:
            if not args:
                args.insert(0, self.default_command)
            elif args[0].startswith("-"):
                special = {"--help", "-h", "--version", "-V"}
                if not special.intersection(args):
                    args.insert(0, self.default_command)
        super().parse_args(ctx, args)


def setup_logging(log_level: str) -> None:
    """Setup logging configuration without disrupting test capture.

    Configures a StreamHandler to stdout and sets the root logger level,
    but avoids forcefully resetting existing handlers so pytest's caplog
    (and other handlers) continue to work.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    level = getattr(logging, log_level, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Find existing stdout stream handler if present to avoid duplicates
    stdout_handler: logging.Handler | None = None
    for h in root_logger.handlers:
        if isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stdout:
            stdout_handler = h
            break

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    if stdout_handler is None:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(level)
        stdout_handler.setFormatter(fmt)
        root_logger.addHandler(stdout_handler)
    else:
        stdout_handler.setLevel(level)
        stdout_handler.setFormatter(fmt)


@click.group(cls=DefaultGroup)
@click.version_option(version=__version__)
def cli() -> None:
    """ArrEm-sync: Sync tags between Radarr/Sonarr and Emby."""
    pass


@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help=("Run in dry-run mode without making changes (can also be set via ARREM_DRY_RUN)"),
)
@click.option(
    "--no-dry-run",
    is_flag=True,
    help=("Disable dry-run mode to make actual changes"),
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default=None,
    help="Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def sync(dry_run: bool, no_dry_run: bool, log_level: str | None) -> None:
    """Sync tags from Radarr/Sonarr to Emby."""
    try:
        # Validate conflicting options
        if dry_run and no_dry_run:
            click.echo("Error: Cannot specify both --dry-run and --no-dry-run", err=True)
            raise click.Abort()

        # Load configuration
        config = get_config()

        # Override config with CLI options
        if dry_run:
            config.dry_run = True
        elif no_dry_run:
            config.dry_run = False

        if log_level:
            config.log_level = log_level.upper()

        # Setup logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)

        # Log configuration (without sensitive data)
        logger.info(f"Starting {config.app_name}")
        logger.info(f"Configured {len(config.arr_instances)} Arr instance(s)")
        for i, instance in enumerate(config.arr_instances, 1):
            logger.info(f"  Instance {i}: {instance.type} at {instance.url} ({instance.name or 'Unnamed'})")
        logger.info(f"Emby URL: {config.emby_url}")
        logger.info(f"Dry run mode: {config.dry_run}")
        logger.info(f"Batch size: {config.batch_size}")

        # Create clients and ensure cleanup
        with ExitStack() as stack:
            arr_clients, emby_client = create_clients(config)

            # Register cleanup if clients expose close(); mocks in tests are fine
            for c in arr_clients:
                close = getattr(c, "close", None)
                if callable(close):
                    stack.callback(cast("Callable[[], object]", close))
            if hasattr(emby_client, "close") and callable(emby_client.close):
                stack.callback(cast("Callable[[], object]", emby_client.close))

            # Create multi-instance sync service
            sync_service = MultiTagSyncService(arr_clients=arr_clients, emby_client=emby_client, dry_run=config.dry_run)

            # Perform synchronization
            stats = sync_service.sync_all_instances(batch_size=config.batch_size)

        # Print summary
        click.echo("\n" + "=" * 50)
        click.echo("SYNCHRONIZATION SUMMARY")
        click.echo("=" * 50)

        # Show per-instance results
        for instance_result in stats["instance_results"]:
            click.echo(f"\n{instance_result['instance_name']}:")
            if "error" in instance_result["stats"]:
                click.echo(f"  ERROR: {instance_result['stats']['error']}")
            else:
                inst_stats = instance_result["stats"]
                click.echo(f"  Total items: {inst_stats['total_items']}")
                click.echo(f"  Processed: {inst_stats['processed_items']}")
                click.echo(f"  Successful syncs: {inst_stats['successful_syncs']}")
                click.echo(f"  Already synced: {inst_stats['already_synced']}")
                click.echo(f"  No tags to sync: {inst_stats['no_tags_to_sync']}")
                click.echo(f"  Not found in Emby: {inst_stats['not_in_emby']}")
                click.echo(f"  Failed syncs: {inst_stats['failed_syncs']}")

        # Show overall totals
        click.echo("\nOVERALL TOTALS:")
        click.echo(f"Total instances: {stats['total_instances']}")
        click.echo(f"Total items: {stats['total_items']}")
        click.echo(f"Processed: {stats['processed_items']}")
        click.echo(f"Successful syncs: {stats['successful_syncs']}")
        click.echo(f"Already synced: {stats['already_synced']}")
        click.echo(f"No tags to sync: {stats['no_tags_to_sync']}")
        click.echo(f"Not found in Emby: {stats['not_in_emby']}")
        click.echo(f"Failed syncs: {stats['failed_syncs']}")

        if stats["errors"]:
            click.echo(f"\nErrors ({len(stats['errors'])}):")
            for error in stats["errors"][:10]:  # Show first 10 errors
                click.echo(f"  {error}")
            if len(stats["errors"]) > 10:
                click.echo(f"  ... and {len(stats['errors']) - 10} more errors")

        # Exit with appropriate code
        if stats["failed_syncs"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except (ValidationError, ValueError) as e:
        handle_config_error(e)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
def test() -> None:
    """Test connections to all configured Arr instances and Emby."""
    try:
        # Load configuration
        config = get_config()

        # Setup logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)

        logger.info("Testing connections...")

        # Create clients and ensure cleanup
        with ExitStack() as stack:
            arr_clients, emby_client = create_clients(config)
            # Register cleanup
            for c in arr_clients:
                close = getattr(c, "close", None)
                if callable(close):
                    stack.callback(cast("Callable[[], object]", close))
            if hasattr(emby_client, "close") and callable(emby_client.close):
                stack.callback(cast("Callable[[], object]", emby_client.close))

            # Create multi-instance sync service for connection testing
            sync_service = MultiTagSyncService(arr_clients=arr_clients, emby_client=emby_client)

            # Test all connections
            connection_results = sync_service.test_all_connections()

        # Display results
        all_successful = True

        # Test Emby connection
        if connection_results.get("emby", False):
            click.echo("Testing Emby connection... ✓ Success")
        else:
            click.echo("Testing Emby connection... ✗ Failed")
            all_successful = False

        # Test each Arr instance
        for i, arr_client in enumerate(arr_clients, 1):
            instance = config.arr_instances[i - 1]  # Get instance config for name
            service_name = f"{arr_client.arr_type}_{i}"
            instance_name = instance.name or f"{arr_client.arr_type.title()} {i}"

            if connection_results.get(service_name, False):
                click.echo(f"Testing {instance_name} ({arr_client.arr_type})... ✓ Success")
            else:
                click.echo(f"Testing {instance_name} ({arr_client.arr_type})... ✗ Failed")
                all_successful = False

        if all_successful:
            click.echo(f"\nAll connections successful! ({len(arr_clients)} Arr instance(s) + Emby)")
        else:
            click.echo("\nSome connections failed!")
            sys.exit(1)

    except (ValidationError, ValueError) as e:
        handle_config_error(e)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
