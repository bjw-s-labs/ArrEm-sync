"""Arr (Radarr/Sonarr) client for interacting with Arr APIs."""

import contextlib
import logging
from types import TracebackType
from typing import Any

import requests

from .http_utils import create_session
from .types import ArrItem, ArrTag

logger = logging.getLogger(__name__)


class ArrClient:
    """Client for interacting with Radarr/Sonarr APIs."""

    def __init__(self, arr_type: str, base_url: str, api_key: str):
        """Initialize the Arr client.

        Args:
            arr_type: Type of service ('radarr' or 'sonarr')
            base_url: Base URL of the Arr service
            api_key: API key for authentication
        """
        self.arr_type = arr_type.lower()
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

        # Setup session with retry strategy and connection pooling
        self.session = create_session()

        # Set default headers
        self.session.headers.update({"X-Api-Key": self.api_key, "Content-Type": "application/json"})

    def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Make a request to the Arr API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON data

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/api/v3/{endpoint.lstrip('/')}"

        try:
            # Ensure network calls don't hang indefinitely
            kwargs.setdefault("timeout", 15)
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            raise

    def get_all_items(self) -> list[ArrItem]:
        """Get all items (movies or series) from the Arr service.

        Returns:
            List of items with their metadata
        """
        endpoint = "movie" if self.arr_type == "radarr" else "series"
        logger.info(f"Fetching all {endpoint}s from {self.arr_type}")

        try:
            items = self._make_request("GET", endpoint)
            logger.info(f"Retrieved {len(items)} {endpoint}s from {self.arr_type}")
            return items  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Failed to fetch {endpoint}s from {self.arr_type}: {e}")
            raise

    def get_tags(self) -> list[ArrTag]:
        """Get all tags from the Arr service.

        Returns:
            List of tags with their IDs and labels
        """
        logger.info(f"Fetching tags from {self.arr_type}")

        try:
            tags = self._make_request("GET", "tag")
            logger.info(f"Retrieved {len(tags)} tags from {self.arr_type}")
            return tags  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Failed to fetch tags from {self.arr_type}: {e}")
            raise

    def get_item_by_id(self, item_id: int) -> ArrItem | None:
        """Get a specific item by ID.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            Item data or None if not found
        """
        endpoint = f"{'movie' if self.arr_type == 'radarr' else 'series'}/{item_id}"

        try:
            return self._make_request("GET", endpoint)  # type: ignore[no-any-return]
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def test_connection(self) -> bool:
        """Test the connection to the Arr service.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self._make_request("GET", "system/status")
            logger.info(f"Connection to {self.arr_type} successful")
            return True
        except Exception as e:
            logger.error(f"Connection to {self.arr_type} failed: {e}")
            return False

    # Resource management
    def close(self) -> None:
        """Close underlying HTTP session."""
        with contextlib.suppress(Exception):
            self.session.close()

    def __enter__(self) -> "ArrClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
