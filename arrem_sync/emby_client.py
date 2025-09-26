"""Emby client for interacting with Emby server API."""

import contextlib
import logging
from types import TracebackType
from typing import Any

from .http_utils import create_session
from .types import EmbyItem

logger = logging.getLogger(__name__)


class EmbyClient:
    """Client for interacting with Emby server using requests."""

    def __init__(self, server_url: str, api_key: str):
        """Initialize the Emby client.

        Args:
            server_url: Emby server URL
            api_key: API key for authentication
        """
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key

        # Caches for efficient lookups
        self._movies_cache: list[EmbyItem] | None = None
        self._series_cache: list[EmbyItem] | None = None
        self._provider_id_cache: dict[str, EmbyItem] = {}

        # Set up requests session with retry strategy and connection pooling
        self.session = create_session()

        # Default headers
        self.session.headers.update(
            {
                "X-Emby-Token": self.api_key,
                "Content-Type": "application/json",
            }
        )

    def test_connection(self) -> bool:
        """Test the connection to Emby server.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test connection by getting system info
            url = f"{self.server_url}/emby/System/Info"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            system_info = response.json()
            server_name = system_info.get("ServerName", "Unknown")
            logger.info(f"Connected to Emby server: {server_name}")
            return True
        except Exception as e:
            logger.error(f"Connection to Emby server failed: {e}")
            return False

    def get_all_movies(self) -> list[EmbyItem]:
        """Get all movies from Emby with caching.

        Returns:
            List of movies with their metadata
        """
        if self._movies_cache is not None:
            logger.debug(f"Using cached movies ({len(self._movies_cache)} items)")
            return self._movies_cache

        try:
            logger.info("Fetching all movies from Emby")

            # Build the API URL
            url = f"{self.server_url}/emby/Items"
            params = {
                "IncludeItemTypes": "Movie",
                "Recursive": "true",
                "Fields": "Tags,Path,ProviderIds",
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            items = data.get("Items", [])

            # Cache the results
            self._movies_cache = items
            self._build_provider_id_cache(items)

            logger.info(f"Retrieved {len(items)} movies from Emby")
            return items  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to fetch movies from Emby: {e}")
            raise

    def get_all_series(self) -> list[EmbyItem]:
        """Get all TV series from Emby with caching.

        Returns:
            List of series with their metadata
        """
        if self._series_cache is not None:
            logger.debug(f"Using cached series ({len(self._series_cache)} items)")
            return self._series_cache

        try:
            logger.info("Fetching all TV series from Emby")

            # Build the API URL
            url = f"{self.server_url}/emby/Items"
            params = {
                "IncludeItemTypes": "Series",
                "Recursive": "true",
                "Fields": "Tags,Path,ProviderIds",
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            items = data.get("Items", [])

            # Cache the results
            self._series_cache = items
            self._build_provider_id_cache(items)

            logger.info(f"Retrieved {len(items)} TV series from Emby")
            return items  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to fetch TV series from Emby: {e}")
            raise

    def get_all_tags(self) -> list[dict[str, Any]]:
        """Get all tags from Emby server.

        Note: This method is primarily for informational purposes since tags are
        automatically created when assigned to items.

        Returns:
            List of all tag objects from the server
        """
        try:
            logger.debug("Fetching all tags from Emby")

            url = f"{self.server_url}/emby/Tags"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            tags = data.get("Items", [])

            logger.debug(f"Retrieved {len(tags)} tags from Emby")
            return tags  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to fetch tags from Emby: {e}")
            raise

    def _build_provider_id_cache(self, items: list[EmbyItem]) -> None:
        """Build a cache of provider IDs to items for fast lookups.

        Args:
            items: List of Emby items to cache
        """
        for item in items:
            provider_ids = item.get("ProviderIds", {})
            if isinstance(provider_ids, dict):
                for provider, provider_id in provider_ids.items():
                    # Create a composite key for provider:id
                    cache_key = f"{provider}:{provider_id}"
                    self._provider_id_cache[cache_key] = item

        logger.debug(f"Built provider ID cache with {len(self._provider_id_cache)} entries")

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._movies_cache = None
        self._series_cache = None
        self._provider_id_cache.clear()
        logger.debug("Cleared Emby client caches")

    def update_item_tags(self, item_id: str, tags: list[str], dry_run: bool = False) -> bool:
        """Update tags for an Emby item.

        Tags are automatically created in Emby if they don't exist when assigned
        to an item.

        Args:
            item_id: Emby item ID
            tags: List of tags to set
            dry_run: If True, don't actually update the item

        Returns:
            True if successful, False otherwise
        """
        try:
            if dry_run:
                return True

            logger.debug(f"Updating item {item_id} with tags: {tags}")

            # Use direct item update approach for better compatibility
            item_data = {"Tags": [{"Name": tag} for tag in tags]}

            # Send the updated tags to the server using the item update endpoint
            url = f"{self.server_url}/emby/Items/{item_id}/Tags/Add"
            response = self.session.post(url, json=item_data, timeout=10)
            response.raise_for_status()

            logger.debug(f"Successfully updated tags for item {item_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update tags for item {item_id}: {e}")
            return False

    def find_item_by_provider_id(self, provider: str, provider_id: str, item_type: str = "Movie") -> EmbyItem | None:
        """Find an Emby item by external provider ID (e.g., IMDb, TheMovieDB).

        This method uses caching for efficient lookups. It will automatically
        populate the cache on first use by fetching all items of the specified type.

        Args:
            provider: Provider name (e.g., 'Imdb', 'Tmdb')
            provider_id: Provider-specific ID
            item_type: Type of item to search for (Movie, Series)

        Returns:
            Item data if found, None otherwise
        """
        try:
            logger.debug(f"Searching for {item_type} with {provider} ID: {provider_id}")

            # Ensure we have the appropriate cache populated
            if item_type == "Movie":
                self.get_all_movies()  # This will populate cache if not already done
            elif item_type == "Series":
                self.get_all_series()  # This will populate cache if not already done

            # Create cache key and lookup
            cache_key = f"{provider}:{provider_id}"
            item = self._provider_id_cache.get(cache_key)

            if item:
                # Verify item type matches (cache contains both movies and series)
                item_type_match = item.get("Type", "").lower()
                expected_type = item_type.lower()

                if item_type_match == expected_type:
                    item_name = item.get("Name", "Unknown")
                    item_id = item.get("Id", "Unknown")
                    logger.debug(f"Found matching item: {item_name} (ID: {item_id})")
                    return item

            logger.debug(f"No {item_type} found with {provider} ID: {provider_id}")
            return None
        except Exception as e:
            logger.error(f"Error searching for item with {provider} ID {provider_id}: {e}")
            return None

    # Resource management
    def close(self) -> None:
        """Close underlying HTTP session."""
        with contextlib.suppress(Exception):
            self.session.close()

    def __enter__(self) -> "EmbyClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
