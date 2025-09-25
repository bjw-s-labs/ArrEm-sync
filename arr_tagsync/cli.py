"""Main CLI application for arr-tagsync."""

import logging
import sys

import click
from pydantic import ValidationError

from .arr_client import ArrClient
from .config import Config, get_config
from .emby_client import EmbyClient
from .errors import handle_config_error
from .sync_service import TagSyncService


def setup_logging(log_level: str) -> None:
    """Setup logging configuration.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def create_clients(config: Config) -> tuple[ArrClient, EmbyClient]:
    """Create and return configured clients.

    Args:
        config: Application configuration

    Returns:
        Tuple of (arr_client, emby_client)
    """
    # Create Arr client
    arr_client = ArrClient(arr_type=config.arr_type, base_url=config.arr_url, api_key=config.arr_api_key)

    # Create Emby client
    emby_client = EmbyClient(
        server_url=config.emby_url,
        api_key=config.emby_api_key,
        user_id=config.emby_user_id,
    )

    return arr_client, emby_client


@click.group()
@click.version_option(version="1.0.0")
def cli() -> None:
    """arr-tagsync: Sync tags between Radarr/Sonarr and Emby."""
    pass


@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help=("Run in dry-run mode without making changes (can also be set via TAGSYNC_DRY_RUN)"),
)
@click.option("--log-level", default=None, help="Override log level (DEBUG, INFO, WARNING, ERROR)")
def sync(dry_run: bool, log_level: str | None) -> None:
    """Sync tags from Radarr/Sonarr to Emby."""
    try:
        # Load configuration
        config = get_config()

        # Override config with CLI options
        if dry_run:
            config.dry_run = True
        if log_level:
            config.log_level = log_level.upper()

        # Setup logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)

        # Log configuration (without sensitive data)
        logger.info(f"Starting {config.app_name}")
        logger.info(f"Arr type: {config.arr_type}")
        logger.info(f"Arr URL: {config.arr_url}")
        logger.info(f"Emby URL: {config.emby_url}")
        logger.info(f"Emby user ID: {config.emby_user_id or 'None'}")
        logger.info(f"Dry run mode: {config.dry_run}")
        logger.info(f"Batch size: {config.batch_size}")

        # Create clients
        arr_client, emby_client = create_clients(config)

        # Create sync service
        sync_service = TagSyncService(arr_client=arr_client, emby_client=emby_client, dry_run=config.dry_run)

        # Perform synchronization
        stats = sync_service.sync_all_tags(batch_size=config.batch_size)

        # Print summary
        click.echo("\n" + "=" * 50)
        click.echo("SYNCHRONIZATION SUMMARY")
        click.echo("=" * 50)
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
    """Test connections to Radarr/Sonarr and Emby."""
    try:
        # Load configuration
        config = get_config()

        # Setup logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)

        logger.info("Testing connections...")

        # Create clients
        arr_client, emby_client = create_clients(config)

        # Test Arr connection
        click.echo(f"Testing {config.arr_type} connection...", nl=False)
        if arr_client.test_connection():
            click.echo(" ✓ Success")
        else:
            click.echo(" ✗ Failed")
            sys.exit(1)

        # Test Emby connection
        click.echo("Testing Emby connection...", nl=False)
        if emby_client.test_connection():
            click.echo(" ✓ Success")
        else:
            click.echo(" ✗ Failed")
            sys.exit(1)

        click.echo("\nAll connections successful!")

    except (ValidationError, ValueError) as e:
        handle_config_error(e)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
