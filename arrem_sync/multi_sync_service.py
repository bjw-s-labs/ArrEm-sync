"""Multi-instance tag synchronization service."""

import logging
from typing import Any

from .arr_client import ArrClient
from .emby_client import EmbyClient
from .sync_service import TagSyncService

logger = logging.getLogger(__name__)


class MultiTagSyncService:
    """Service for synchronizing tags between multiple Arr instances and Emby."""

    def __init__(self, arr_clients: list[ArrClient], emby_client: EmbyClient, dry_run: bool = False):
        """Initialize the multi-instance tag sync service.

        Args:
            arr_clients: List of Arr clients (Radarr/Sonarr)
            emby_client: Client for Emby server
            dry_run: If True, only simulate changes without applying them
        """
        self.arr_clients = arr_clients
        self.emby_client = emby_client
        self.dry_run = dry_run

        # Create individual sync services for each Arr client
        self.sync_services = [
            TagSyncService(arr_client=client, emby_client=emby_client, dry_run=dry_run) for client in arr_clients
        ]

    def test_all_connections(self) -> dict[str, bool]:
        """Test connections to all Arr instances and Emby.

        Returns:
            Dictionary mapping service names to connection status
        """
        results = {}

        # Test Emby connection
        results["emby"] = self.emby_client.test_connection()

        # Test each Arr client connection
        for i, client in enumerate(self.arr_clients, 1):
            service_name = f"{client.arr_type}_{i}"
            results[service_name] = client.test_connection()

        return results

    def sync_all_instances(self, batch_size: int = 50) -> dict[str, Any]:
        """Sync tags from all Arr instances to Emby.

        Behavior is additive: for each item found in Emby, any tags present
        in the corresponding Arr item are added if missing. Existing tags set
        directly in Emby are preserved and are never removed by this sync.
        When the same logical item exists across multiple Arr instances, the
        effective result is a union of all Arr-provided tags added over time.

        Args:
            batch_size: Number of items to process in each batch per instance

        Returns:
            Dictionary with aggregated sync results and statistics
        """
        logger.info(f"Starting multi-instance tag synchronization with {len(self.arr_clients)} instances")

        # Test all connections first
        connection_results = self.test_all_connections()
        failed_connections = [name for name, status in connection_results.items() if not status]

        if failed_connections:
            raise Exception(f"Failed to connect to services: {', '.join(failed_connections)}")

        # Initialize aggregated statistics
        overall_stats: dict[str, Any] = {
            "total_instances": len(self.arr_clients),
            "instance_results": [],
            "total_items": 0,
            "processed_items": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "not_in_emby": 0,
            "already_synced": 0,
            "no_tags_to_sync": 0,
            "errors": [],
        }

        # Process each Arr instance
        for i, (client, sync_service) in enumerate(zip(self.arr_clients, self.sync_services, strict=False), 1):
            instance_name = f"Instance {i} ({client.arr_type})"
            logger.info(f"Processing {instance_name}")

            try:
                # Sync this instance
                instance_stats = sync_service.sync_all_tags(batch_size=batch_size)

                # Add instance information to the results
                instance_result = {
                    "instance_number": i,
                    "instance_name": instance_name,
                    "arr_type": client.arr_type,
                    "base_url": client.base_url,
                    "stats": instance_stats,
                }
                overall_stats["instance_results"].append(instance_result)

                # Aggregate statistics
                overall_stats["total_items"] += instance_stats["total_items"]
                overall_stats["processed_items"] += instance_stats["processed_items"]
                overall_stats["successful_syncs"] += instance_stats["successful_syncs"]
                overall_stats["failed_syncs"] += instance_stats["failed_syncs"]
                overall_stats["not_in_emby"] += instance_stats["not_in_emby"]
                overall_stats["already_synced"] += instance_stats["already_synced"]
                overall_stats["no_tags_to_sync"] += instance_stats["no_tags_to_sync"]
                overall_stats["errors"].extend(instance_stats["errors"])

                logger.debug(f"Completed {instance_name}: {instance_stats['processed_items']} items processed")

            except Exception as e:
                error_msg = f"Failed to sync {instance_name}: {e}"
                logger.error(error_msg)
                overall_stats["errors"].append(error_msg)

                # Add failed instance to results
                instance_result = {
                    "instance_number": i,
                    "instance_name": instance_name,
                    "arr_type": client.arr_type,
                    "base_url": client.base_url,
                    "stats": {"error": str(e)},
                }
                overall_stats["instance_results"].append(instance_result)

        # Log final aggregated statistics at DEBUG; CLI prints the user-facing summary
        logger.debug("Multi-instance tag synchronization completed:")
        logger.debug(f"  Total instances: {overall_stats['total_instances']}")
        logger.debug(f"  Total items across all instances: {overall_stats['total_items']}")
        logger.debug(f"  Processed: {overall_stats['processed_items']}")
        logger.debug(f"  Successful syncs: {overall_stats['successful_syncs']}")
        logger.debug(f"  Already synced: {overall_stats['already_synced']}")
        logger.debug(f"  No tags to sync: {overall_stats['no_tags_to_sync']}")
        logger.debug(f"  Not found in Emby: {overall_stats['not_in_emby']}")
        logger.debug(f"  Failed syncs: {overall_stats['failed_syncs']}")

        return overall_stats

    def clear_all_caches(self) -> None:
        """Clear caches for all sync services."""
        for sync_service in self.sync_services:
            sync_service.clear_caches()
        logger.info("Cleared caches for all sync services")

    def get_instance_info(self) -> list[dict[str, Any]]:
        """Get information about all configured Arr instances.

        Returns:
            List of dictionaries with instance information
        """
        return [
            {
                "instance_number": i,
                "arr_type": client.arr_type,
                "base_url": client.base_url,
                "has_api_key": bool(client.api_key),
            }
            for i, client in enumerate(self.arr_clients, 1)
        ]
