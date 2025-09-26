"""Tag synchronization service."""

import logging
from dataclasses import dataclass
from typing import Any, Literal

from .arr_client import ArrClient
from .emby_client import EmbyClient
from .types import ArrItem, EmbyItem

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

    # No local Emby item cache; rely on EmbyClient's internal caches

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

    # Structured result for internal/statistics usage
    StatusCode = Literal["updated", "already_synced", "no_tags", "not_in_emby", "failed", "error"]

    @dataclass(frozen=True)
    class SyncResult:
        success: bool
        message: str
        code: "TagSyncService.StatusCode"

    def _warm_emby_client_cache(self) -> None:
        """Warm EmbyClient caches to optimize lookups; no local caching here."""
        logger.debug("Warming Emby client caches for efficient matching...")
        if self.arr_client.arr_type == "radarr":
            _ = self.emby_client.get_all_movies()
        else:
            _ = self.emby_client.get_all_series()
        # Best-effort log of provider cache size
        try:
            cache_size = len(self.emby_client._provider_id_cache)
            logger.debug(f"Warmed provider ID cache entries: {cache_size}")
        except (AttributeError, TypeError):
            logger.debug("Provider ID cache info not available")

    def find_matching_emby_item(self, arr_item: ArrItem) -> EmbyItem | None:
        """Find the corresponding Emby item for an Arr item.

        This method uses optimized lookups with pre-fetched cache for efficiency.

        Args:
            arr_item: Item from Arr service

        Returns:
            Matching Emby item or None if not found
        """
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

    def sync_tags_for_item_structured(self, arr_item: ArrItem) -> "TagSyncService.SyncResult":
        """Structured sync for a single item, for internal use and stats tracking."""
        try:
            # Find matching Emby item
            emby_item = self.find_matching_emby_item(arr_item)
            if not emby_item:
                # Item exists in Arr but not in Emby - this is normal and
                # shouldn't be treated as an error
                return TagSyncService.SyncResult(
                    True,
                    f"Item not found in Emby (may not be imported yet): {arr_item.get('title', 'Unknown')}",
                    "not_in_emby",
                )

            # Get tags from Arr item
            arr_tag_ids = arr_item.get("tags", [])
            if not arr_tag_ids:
                logger.debug(f"No tags to sync for {arr_item.get('title', 'Unknown')}")
                return TagSyncService.SyncResult(True, "No tags to sync", "no_tags")

            # Resolve tag IDs to labels
            new_tags = self.resolve_tag_labels(arr_tag_ids)

            # Get current tags from Emby item (extract tag names from TagItems array)
            current_tags = [tag_item["Name"] for tag_item in emby_item.get("TagItems", [])]
            logger.debug(f"Current tags for {emby_item.get('Name', 'Unknown')}: {current_tags}")

            # Non-destructive behavior: only add missing Arr tags; never remove user-set Emby tags
            current_set = set(current_tags)
            new_set = set(new_tags)

            # If all Arr tags are already present on Emby, no action needed
            if new_set.issubset(current_set):
                logger.debug(f"Tags already up to date for {emby_item.get('Name', 'Unknown')}")
                return TagSyncService.SyncResult(True, "Tags already up to date", "already_synced")

            # Compute only the tags that are missing on Emby, preserving original order from Arr
            missing_tags = [t for t in new_tags if t not in current_set]
            logger.debug(
                f"Will add missing tags for {emby_item.get('Name', 'Unknown')}: {missing_tags} (dry_run={self.dry_run})"
            )

            # Update tags in Emby by adding the missing ones only
            success = self.emby_client.update_item_tags(emby_item["Id"], missing_tags, dry_run=self.dry_run)

            if success:
                action = "Would add" if self.dry_run else "Added"
                return TagSyncService.SyncResult(True, f"{action} tags: {missing_tags}", "updated")
            else:
                return TagSyncService.SyncResult(False, "Failed to update tags in Emby", "failed")

        except Exception as e:
            logger.error(f"Error syncing tags for {arr_item.get('title', 'Unknown')}: {e}")
            return TagSyncService.SyncResult(False, f"Error: {e!s}", "error")

    def sync_tags_for_item(self, arr_item: ArrItem) -> tuple[bool, str]:
        """Backward-compatible wrapper returning (success, message)."""
        res = self.sync_tags_for_item_structured(arr_item)
        return res.success, res.message

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
            self._warm_emby_client_cache()

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
                logger.debug(f"Processing batch {i // batch_size + 1} ({len(batch)} items)")

                for arr_item in batch:
                    try:
                        res = self.sync_tags_for_item_structured(arr_item)
                        stats["processed_items"] += 1

                        if res.success:
                            match res.code:
                                case "not_in_emby":
                                    stats["not_in_emby"] += 1
                                    logger.info(f"⚠ {arr_item.get('title', 'Unknown')}: {res.message}")
                                case "already_synced":
                                    stats["already_synced"] += 1
                                    logger.info(f"✓ {arr_item.get('title', 'Unknown')}: {res.message}")
                                case "no_tags":
                                    stats["no_tags_to_sync"] += 1
                                    logger.debug(f"◯ {arr_item.get('title', 'Unknown')}: {res.message}")
                                case _:
                                    stats["successful_syncs"] += 1
                                    logger.info(f"✓ {arr_item.get('title', 'Unknown')}: {res.message}")
                        else:
                            stats["failed_syncs"] += 1
                            error_msg = f"✗ {arr_item.get('title', 'Unknown')}: {res.message}"
                            stats["errors"].append(error_msg)
                            logger.error(error_msg)

                    except Exception as e:
                        stats["failed_syncs"] += 1
                        error_msg = f"✗ {arr_item.get('title', 'Unknown')}: Unexpected error: {e}"
                        stats["errors"].append(error_msg)
                        logger.error(error_msg)

            # Log final statistics at DEBUG to avoid duplicating CLI summary output
            logger.debug("Tag synchronization completed:")
            logger.debug(f"  Total items: {stats['total_items']}")
            logger.debug(f"  Processed: {stats['processed_items']}")
            logger.debug(f"  Successful syncs: {stats['successful_syncs']}")
            logger.debug(f"  Already synced: {stats['already_synced']}")
            logger.debug(f"  No tags to sync: {stats['no_tags_to_sync']}")
            logger.debug(f"  Not found in Emby: {stats['not_in_emby']}")
            logger.debug(f"  Failed syncs: {stats['failed_syncs']}")

            # Log cache efficiency info
            try:
                cache_size = len(self.emby_client._provider_id_cache)
                logger.debug(f"  Provider ID cache entries: {cache_size}")
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
        self.emby_client.clear_cache()
        logger.info("Cleared all sync service caches")
