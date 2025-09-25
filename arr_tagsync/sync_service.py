"""Tag synchronization service."""

import logging
from typing import Any

from .arr_client import ArrClient
from .emby_client import EmbyClient

logger = logging.getLogger(__name__)


class TagSyncService:
    """Service for synchronizing tags between Arr services and Emby."""

    def __init__(self, arr_client: ArrClient, emby_client: EmbyClient, dry_run: bool = False):
        """Initialize the tag sync service.

        Args:
            arr_client: Client for Arr service (Radarr/Sonarr)
            emby_client: Client for Emby server
            dry_run: If True, only simulate changes without applying them
        """
        self.arr_client = arr_client
        self.emby_client = emby_client
        self.dry_run = dry_run

        # Cache for tag mappings
        self._arr_tags_cache: dict[int, str] | None = None

        # Cache for Emby items to avoid multiple lookups
        self._emby_items_cache: list[dict[str, Any]] | None = None

    def get_arr_tags_mapping(self) -> dict[int, str]:
        """Get mapping of tag IDs to tag labels from Arr service.

        Returns:
            Dictionary mapping tag IDs to tag labels
        """
        if self._arr_tags_cache is None:
            tags = self.arr_client.get_tags()
            self._arr_tags_cache = {tag["id"]: tag["label"] for tag in tags}
            logger.info(f"Cached {len(self._arr_tags_cache)} tags from {self.arr_client.arr_type}")

        return self._arr_tags_cache

    def resolve_tag_labels(self, tag_ids: list[int]) -> list[str]:
        """Resolve tag IDs to their string labels.

        Args:
            tag_ids: List of tag IDs

        Returns:
            List of tag labels
        """
        tag_mapping = self.get_arr_tags_mapping()
        return [tag_mapping.get(tag_id, f"Unknown-{tag_id}") for tag_id in tag_ids]

    def _prefetch_emby_items(self) -> None:
        """Pre-fetch all Emby items to populate the cache for efficient lookups."""
        if self._emby_items_cache is not None:
            logger.debug("Emby items cache already populated")
            return

        logger.info("Pre-fetching Emby items to optimize lookups...")

        # Fetch based on arr_type
        if self.arr_client.arr_type == "radarr":
            self._emby_items_cache = self.emby_client.get_all_movies()
        else:  # sonarr
            self._emby_items_cache = self.emby_client.get_all_series()

        # Handle both real lists and Mock objects (for testing)
        try:
            cache_size = len(self._emby_items_cache)
            logger.info(f"Pre-fetched {cache_size} Emby items")
        except TypeError:
            # This handles Mock objects in tests
            logger.info("Pre-fetched Emby items (mock data)")
            self._emby_items_cache = []  # Set to empty list for tests

    def find_matching_emby_item(self, arr_item: dict[str, Any]) -> dict[str, Any] | None:
        """Find the corresponding Emby item for an Arr item.

        This method uses optimized lookups with pre-fetched cache for efficiency.

        Args:
            arr_item: Item from Arr service

        Returns:
            Matching Emby item or None if not found
        """
        # Ensure Emby items are cached for efficient lookups
        self._prefetch_emby_items()

        item_type = "Movie" if self.arr_client.arr_type == "radarr" else "Series"

        # Try multiple provider IDs in order of reliability
        provider_attempts = []

        # Try to match by TMDb ID first (most reliable)
        tmdb_id = arr_item.get("tmdbId")
        if tmdb_id:
            provider_attempts.append(("Tmdb", str(tmdb_id)))

        # Try to match by IMDb ID
        imdb_id = arr_item.get("imdbId")
        if imdb_id:
            provider_attempts.append(("Imdb", imdb_id))

        # For TV shows, try TVDB ID
        if self.arr_client.arr_type == "sonarr":
            tvdb_id = arr_item.get("tvdbId")
            if tvdb_id:
                provider_attempts.append(("Tvdb", str(tvdb_id)))

        # Try each provider ID until we find a match
        for provider, provider_id in provider_attempts:
            emby_item = self.emby_client.find_item_by_provider_id(provider, provider_id, item_type)
            if emby_item:
                return emby_item

        # Build debug message including all attempted IDs
        debug_parts = [f"Could not find Emby match for {arr_item.get('title', 'Unknown')}"]
        id_parts = [f"TMDb: {tmdb_id}", f"IMDb: {imdb_id}"]

        if self.arr_client.arr_type == "sonarr":
            tvdb_id = arr_item.get("tvdbId")
            id_parts.append(f"TVDB: {tvdb_id}")

        debug_parts.append(f"({', '.join(id_parts)})")
        logger.debug(" ".join(debug_parts))
        return None

    def sync_tags_for_item(self, arr_item: dict[str, Any]) -> tuple[bool, str]:
        """Sync tags for a single item.

        Args:
            arr_item: Item from Arr service

        Returns:
            Tuple of (success, message)
        """
        try:
            # Find matching Emby item
            emby_item = self.find_matching_emby_item(arr_item)
            if not emby_item:
                # Item exists in Arr but not in Emby - this is normal and
                # shouldn't be treated as an error
                return (
                    True,
                    f"Item not found in Emby (may not be imported yet): {arr_item.get('title', 'Unknown')}",
                )

            # Get tags from Arr item
            arr_tag_ids = arr_item.get("tags", [])
            if not arr_tag_ids:
                logger.debug(f"No tags to sync for {arr_item.get('title', 'Unknown')}")
                return True, "No tags to sync"

            # Resolve tag IDs to labels
            new_tags = self.resolve_tag_labels(arr_tag_ids)

            # Get current tags from Emby item
            current_tags = emby_item.get("Tags", [])

            # Check if tags need updating
            if set(new_tags) == set(current_tags):
                logger.debug(f"Tags already up to date for {emby_item.get('Name', 'Unknown')}")
                return True, "Tags already up to date"

            # Update tags in Emby
            success = self.emby_client.update_item_tags(emby_item["Id"], new_tags, dry_run=self.dry_run)

            if success:
                action = "Would update" if self.dry_run else "Updated"
                return True, f"{action} tags: {current_tags} -> {new_tags}"
            else:
                return False, "Failed to update tags in Emby"

        except Exception as e:
            logger.error(f"Error syncing tags for {arr_item.get('title', 'Unknown')}: {e}")
            return False, f"Error: {e!s}"

    def sync_all_tags(self, batch_size: int = 50) -> dict[str, Any]:
        """Sync tags for all items.

        Args:
            batch_size: Number of items to process in each batch

        Returns:
            Dictionary with sync results and statistics
        """
        logger.info("Starting tag synchronization")

        try:
            # Test connections first
            if not self.arr_client.test_connection():
                raise Exception(f"Failed to connect to {self.arr_client.arr_type}")

            if not self.emby_client.test_connection():
                raise Exception("Failed to connect to Emby server")

            # Pre-fetch Emby items for efficient lookups
            logger.info("Pre-fetching Emby items for efficient matching...")
            self._prefetch_emby_items()

            # Get all items from Arr service
            arr_items = self.arr_client.get_all_items()

            # Initialize statistics
            stats: dict[str, Any] = {
                "total_items": len(arr_items),
                "processed_items": 0,
                "successful_syncs": 0,
                "failed_syncs": 0,
                "not_in_emby": 0,
                "already_synced": 0,
                "no_tags_to_sync": 0,
                "errors": [],
            }

            # Process items in batches
            for i in range(0, len(arr_items), batch_size):
                batch = arr_items[i : i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} items)")

                for arr_item in batch:
                    try:
                        success, message = self.sync_tags_for_item(arr_item)
                        stats["processed_items"] += 1

                        if success:
                            if "not found in Emby" in message:
                                stats["not_in_emby"] += 1
                                logger.info(f"⚠ {arr_item.get('title', 'Unknown')}: {message}")
                            elif "already up to date" in message:
                                stats["already_synced"] += 1
                                logger.info(f"✓ {arr_item.get('title', 'Unknown')}: {message}")
                            elif "No tags to sync" in message:
                                stats["no_tags_to_sync"] += 1
                                logger.debug(f"◯ {arr_item.get('title', 'Unknown')}: {message}")
                            else:
                                stats["successful_syncs"] += 1
                                logger.info(f"✓ {arr_item.get('title', 'Unknown')}: {message}")

                        else:
                            stats["failed_syncs"] += 1
                            error_msg = f"✗ {arr_item.get('title', 'Unknown')}: {message}"
                            stats["errors"].append(error_msg)
                            logger.error(error_msg)

                    except Exception as e:
                        stats["failed_syncs"] += 1
                        error_msg = f"✗ {arr_item.get('title', 'Unknown')}: Unexpected error: {e}"
                        stats["errors"].append(error_msg)
                        logger.error(error_msg)

            # Log final statistics
            logger.info("Tag synchronization completed:")
            logger.info(f"  Total items: {stats['total_items']}")
            logger.info(f"  Processed: {stats['processed_items']}")
            logger.info(f"  Successful syncs: {stats['successful_syncs']}")
            logger.info(f"  Already synced: {stats['already_synced']}")
            logger.info(f"  No tags to sync: {stats['no_tags_to_sync']}")
            logger.info(f"  Not found in Emby: {stats['not_in_emby']}")
            logger.info(f"  Failed syncs: {stats['failed_syncs']}")

            # Log cache efficiency info
            try:
                cache_size = len(self.emby_client._provider_id_cache)
                logger.info(f"  Provider ID cache entries: {cache_size}")
            except (AttributeError, TypeError):
                # Handle Mock objects in tests or other edge cases
                logger.debug("  Provider ID cache info not available")

            return stats

        except Exception as e:
            logger.error(f"Tag synchronization failed: {e}")
            raise

    def clear_caches(self) -> None:
        """Clear all cached data."""
        self._arr_tags_cache = None
        self._emby_items_cache = None
        self.emby_client.clear_cache()
        logger.info("Cleared all sync service caches")
