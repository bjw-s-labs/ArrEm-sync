"""Tests for Arr client."""

from unittest.mock import patch

import pytest
import requests
import responses

from arrem_sync.arr_client import ArrClient


class TestArrClient:
    """Test ArrClient class."""

    def test_init(self):
        """Test ArrClient initialization."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        assert client.arr_type == "radarr"
        assert client.base_url == "http://localhost:7878"
        assert client.api_key == "test_key"
        assert "X-Api-Key" in client.session.headers
        assert client.session.headers["X-Api-Key"] == "test_key"

    def test_init_normalizes_arr_type(self):
        """Test that arr_type is normalized to lowercase."""
        client = ArrClient(arr_type="RADARR", base_url="http://localhost:7878", api_key="test_key")

        assert client.arr_type == "radarr"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base_url."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878/", api_key="test_key")

        assert client.base_url == "http://localhost:7878"

    @responses.activate
    def test_make_request_success(self):
        """Test successful API request."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        # Mock response
        responses.add(
            responses.GET,
            "http://localhost:7878/api/v3/movie",
            json=[{"id": 1, "title": "Test Movie"}],
            status=200,
        )

        result = client._make_request("GET", "movie")
        assert result == [{"id": 1, "title": "Test Movie"}]

    @responses.activate
    def test_make_request_failure(self):
        """Test failed API request."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        # Mock error response
        responses.add(responses.GET, "http://localhost:7878/api/v3/movie", status=500)

        with pytest.raises(requests.exceptions.RetryError):
            client._make_request("GET", "movie")

    @responses.activate
    def test_get_all_items_radarr(self):
        """Test getting all items from Radarr."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        mock_movies = [
            {"id": 1, "title": "Movie 1", "tags": [1, 2]},
            {"id": 2, "title": "Movie 2", "tags": [2, 3]},
        ]

        responses.add(
            responses.GET,
            "http://localhost:7878/api/v3/movie",
            json=mock_movies,
            status=200,
        )

        result = client.get_all_items()
        assert result == mock_movies

    @responses.activate
    def test_get_all_items_sonarr(self):
        """Test getting all items from Sonarr."""
        client = ArrClient(arr_type="sonarr", base_url="http://localhost:8989", api_key="test_key")

        mock_series = [
            {"id": 1, "title": "Series 1", "tags": [1, 2]},
            {"id": 2, "title": "Series 2", "tags": [2, 3]},
        ]

        responses.add(
            responses.GET,
            "http://localhost:8989/api/v3/series",
            json=mock_series,
            status=200,
        )

        result = client.get_all_items()
        assert result == mock_series

    @responses.activate
    def test_get_tags(self):
        """Test getting tags."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        mock_tags = [
            {"id": 1, "label": "Action"},
            {"id": 2, "label": "Comedy"},
            {"id": 3, "label": "Drama"},
        ]

        responses.add(
            responses.GET,
            "http://localhost:7878/api/v3/tag",
            json=mock_tags,
            status=200,
        )

        result = client.get_tags()
        assert result == mock_tags

    @responses.activate
    def test_get_item_by_id(self):
        """Test getting item by ID."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        mock_movie = {"id": 1, "title": "Test Movie", "tags": [1, 2]}

        responses.add(
            responses.GET,
            "http://localhost:7878/api/v3/movie/1",
            json=mock_movie,
            status=200,
        )

        result = client.get_item_by_id(1)
        assert result == mock_movie

    @responses.activate
    def test_get_item_by_id_not_found(self):
        """Test getting item by ID when item doesn't exist."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        responses.add(responses.GET, "http://localhost:7878/api/v3/movie/999", status=404)

        result = client.get_item_by_id(999)
        assert result is None

    @responses.activate
    def test_test_connection_success(self):
        """Test successful connection test."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        responses.add(
            responses.GET,
            "http://localhost:7878/api/v3/system/status",
            json={"version": "4.0.0"},
            status=200,
        )

        assert client.test_connection() is True

    @responses.activate
    def test_test_connection_failure(self):
        """Test failed connection test."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        responses.add(responses.GET, "http://localhost:7878/api/v3/system/status", status=500)

        assert client.test_connection() is False


class TestArrClientExceptionHandling:
    """Test exception handling in ArrClient."""

    @responses.activate
    def test_get_all_items_exception_handling(self):
        """Test exception handling in get_all_items."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        # Mock a request exception
        responses.add(
            responses.GET,
            "http://localhost:7878/api/v3/movie",
            body=requests.exceptions.RequestException("Connection failed"),
        )

        with pytest.raises(requests.exceptions.RequestException):
            client.get_all_items()

    @responses.activate
    def test_get_all_items_sonarr_exception_handling(self):
        """Test exception handling in get_all_items for sonarr."""
        client = ArrClient(arr_type="sonarr", base_url="http://localhost:8989", api_key="test_key")

        # Mock a connection error
        responses.add(
            responses.GET,
            "http://localhost:8989/api/v3/series",
            body=requests.exceptions.ConnectionError("Network unreachable"),
        )

        with pytest.raises(requests.exceptions.ConnectionError):
            client.get_all_items()

    @responses.activate
    def test_get_tags_exception_handling(self):
        """Test exception handling in get_tags."""
        client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")

        # Mock a timeout error
        responses.add(
            responses.GET, "http://localhost:7878/api/v3/tag", body=requests.exceptions.Timeout("Request timeout")
        )

        with pytest.raises(requests.exceptions.Timeout):
            client.get_tags()

    def test_get_all_items_with_different_arr_types(self):
        """Test get_all_items with different arr types."""
        # Test that different arr_types result in different endpoints
        radarr_client = ArrClient(arr_type="radarr", base_url="http://localhost:7878", api_key="test_key")
        sonarr_client = ArrClient(arr_type="sonarr", base_url="http://localhost:8989", api_key="test_key")
        lidarr_client = ArrClient(arr_type="lidarr", base_url="http://localhost:8686", api_key="test_key")

        with patch.object(radarr_client, "_make_request") as mock_radarr:
            mock_radarr.return_value = []
            radarr_client.get_all_items()
            mock_radarr.assert_called_once_with("GET", "movie")

        with patch.object(sonarr_client, "_make_request") as mock_sonarr:
            mock_sonarr.return_value = []
            sonarr_client.get_all_items()
            mock_sonarr.assert_called_once_with("GET", "series")

        with patch.object(lidarr_client, "_make_request") as mock_lidarr:
            mock_lidarr.return_value = []
            lidarr_client.get_all_items()
            # Lidarr defaults to series endpoint since it's not radarr
            mock_lidarr.assert_called_once_with("GET", "series")
