"""Tests for Emby client."""

from unittest.mock import Mock, patch

import pytest
import requests

from arrem_sync.emby_client import EmbyClient


class TestEmbyClient:
    """Test EmbyClient class."""

    def test_init(self):
        """Test EmbyClient initialization."""
        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        assert client.server_url == "http://localhost:8096"
        assert client.api_key == "test_key"
        assert client.session is not None
        assert client.session.headers["X-Emby-Token"] == "test_key"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from server_url."""
        client = EmbyClient(server_url="http://localhost:8096/", api_key="test_key")

        assert client.server_url == "http://localhost:8096"

    @patch("requests.Session.get")
    def test_test_connection_success(self, mock_get):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.json.return_value = {"ServerName": "Test Emby Server"}
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        assert client.test_connection() is True
        mock_get.assert_called_once_with("http://localhost:8096/emby/System/Info", timeout=10)

    @patch("requests.Session.get")
    def test_test_connection_failure(self, mock_get):
        """Test failed connection test."""
        mock_get.side_effect = requests.RequestException("Connection failed")

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        assert client.test_connection() is False

    @patch("requests.Session.get")
    def test_get_all_movies(self, mock_get):
        """Test getting all movies."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Items": [
                {"Id": "1", "Name": "Movie 1", "Tags": ["Action", "Drama"]},
                {"Id": "2", "Name": "Movie 2", "Tags": ["Comedy"]},
            ]
        }
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        result = client.get_all_movies()

        assert len(result) == 2
        assert result[0]["Id"] == "1"
        assert result[1]["Id"] == "2"
        mock_get.assert_called_once_with(
            "http://localhost:8096/emby/Items",
            params={
                "IncludeItemTypes": "Movie",
                "Recursive": "true",
                "Fields": "Tags,Path,ProviderIds",
            },
            timeout=30,
        )

    @patch("requests.Session.get")
    def test_get_all_series(self, mock_get):
        """Test getting all TV series."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Items": [
                {"Id": "1", "Name": "Series 1", "Tags": ["Drama"]},
                {"Id": "2", "Name": "Series 2", "Tags": ["Comedy", "Sitcom"]},
            ]
        }
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        result = client.get_all_series()

        assert len(result) == 2
        assert result[0]["Id"] == "1"
        assert result[1]["Id"] == "2"
        mock_get.assert_called_once_with(
            "http://localhost:8096/emby/Items",
            params={
                "IncludeItemTypes": "Series",
                "Recursive": "true",
                "Fields": "Tags,Path,ProviderIds",
            },
            timeout=30,
        )

    def test_update_item_tags_dry_run(self):
        """Test updating item tags in dry-run mode."""
        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        result = client.update_item_tags("item123", ["Action", "Drama"], dry_run=True)

        assert result is True

    @patch("requests.Session.get")
    def test_get_all_tags(self, mock_get):
        """Test getting all tags."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Items": [
                {"Id": "tag1", "Name": "Action"},
                {"Id": "tag2", "Name": "Drama"},
                {"Id": "tag3", "Name": "Comedy"},
            ]
        }
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        result = client.get_all_tags()

        assert len(result) == 3
        assert result[0]["Name"] == "Action"
        assert result[1]["Name"] == "Drama"
        assert result[2]["Name"] == "Comedy"
        mock_get.assert_called_once_with("http://localhost:8096/emby/Tags", timeout=10)

    @patch("requests.Session.post")
    def test_update_item_tags(self, mock_post):
        """Test updating item tags."""
        # Mock the POST response for tag updates
        mock_post_response = Mock()
        mock_post.return_value = mock_post_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        result = client.update_item_tags("item123", ["Action", "Drama"], dry_run=False)

        assert result is True

        # Check that the POST was called once with all tags (direct item update format)
        mock_post.assert_called_once_with(
            "http://localhost:8096/emby/Items/item123/Tags/Add",
            json={"Tags": [{"Name": "Action"}, {"Name": "Drama"}]},
            timeout=10,
        )

    @patch("requests.Session.get")
    def test_find_item_by_provider_id(self, mock_get):
        """Test finding item by provider ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Items": [
                {
                    "Id": "emby123",
                    "Name": "Test Movie",
                    "Type": "movie",
                    "ProviderIds": {"Imdb": "tt1234567", "Tmdb": "12345"},
                    "Tags": ["Action"],
                }
            ]
        }
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        result = client.find_item_by_provider_id("Imdb", "tt1234567", "Movie")

        assert result is not None
        assert result["Id"] == "emby123"
        assert result["Name"] == "Test Movie"
        # The new implementation caches all movies, so it calls get_all_movies
        mock_get.assert_called_once_with(
            "http://localhost:8096/emby/Items",
            params={
                "IncludeItemTypes": "Movie",
                "Recursive": "true",
                "Fields": "Tags,Path,ProviderIds",
            },
            timeout=30,
        )

    @patch("requests.Session.get")
    def test_find_item_by_provider_id_not_found(self, mock_get):
        """Test finding item by provider ID when not found."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Items": [
                {
                    "Id": "emby123",
                    "Name": "Test Movie",
                    "ProviderIds": {"Imdb": "tt9999999"},  # Different ID
                    "Tags": ["Action"],
                }
            ]
        }
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        result = client.find_item_by_provider_id("Imdb", "tt1234567", "Movie")

        assert result is None


class TestEmbyClientCaching:
    """Test EmbyClient caching functionality."""

    @patch("requests.Session.get")
    def test_get_all_movies_with_cache(self, mock_get):
        """Test that movie cache is used when available."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"Items": [{"Id": "movie1", "Name": "Cached Movie", "Type": "Movie"}]}
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        # First call should fetch from API
        movies1 = client.get_all_movies()
        assert len(movies1) == 1
        assert movies1[0]["Name"] == "Cached Movie"
        assert mock_get.call_count == 1

        # Second call should use cache (no additional API call)
        movies2 = client.get_all_movies()
        assert len(movies2) == 1
        assert movies1 == movies2
        assert mock_get.call_count == 1  # Still 1, cache was used

    @patch("requests.Session.get")
    def test_get_all_series_with_cache(self, mock_get):
        """Test that series cache is used when available."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"Items": [{"Id": "series1", "Name": "Cached Series", "Type": "Series"}]}
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        # First call should fetch from API
        series1 = client.get_all_series()
        assert len(series1) == 1
        assert series1[0]["Name"] == "Cached Series"
        assert mock_get.call_count == 1

        # Second call should use cache (no additional API call)
        series2 = client.get_all_series()
        assert len(series2) == 1
        assert series1 == series2
        assert mock_get.call_count == 1  # Still 1, cache was used

    @patch("requests.Session.get")
    def test_get_all_movies_exception_handling(self, mock_get):
        """Test exception handling in get_all_movies."""
        # Mock exception
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        with pytest.raises(requests.exceptions.RequestException):
            client.get_all_movies()

    @patch("requests.Session.get")
    def test_get_all_series_exception_handling(self, mock_get):
        """Test exception handling in get_all_series."""
        # Mock exception
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        with pytest.raises(requests.exceptions.RequestException):
            client.get_all_series()

    @patch("requests.Session.get")
    def test_get_all_tags_exception_handling(self, mock_get):
        """Test exception handling in get_all_tags."""
        # Mock exception
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        with pytest.raises(requests.exceptions.RequestException):
            client.get_all_tags()

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        # Set some cache data
        client._movies_cache = [{"Id": "movie1"}]
        client._series_cache = [{"Id": "series1"}]
        client._provider_id_cache = {"Imdb:tt123": {"Id": "movie1"}}

        # Verify cache is populated
        assert client._movies_cache is not None
        assert client._series_cache is not None
        assert len(client._provider_id_cache) > 0

        # Clear cache
        client.clear_cache()

        # Verify cache is cleared
        assert client._movies_cache is None
        assert client._series_cache is None
        assert len(client._provider_id_cache) == 0

    @patch("requests.Session.post")
    def test_update_item_tags_exception_handling(self, mock_post):
        """Test exception handling in update_item_tags."""
        # Mock exception
        mock_post.side_effect = requests.exceptions.RequestException("Update failed")

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        result = client.update_item_tags("item123", ["Action"], dry_run=False)

        # Should return False on exception
        assert result is False

    def test_find_item_by_provider_id_exception_handling(self):
        """Test exception handling in find_item_by_provider_id."""
        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        # Mock a method that will be called during the process to raise an exception
        with patch.object(client, "get_all_movies", side_effect=Exception("Cache error")):
            result = client.find_item_by_provider_id("Imdb", "tt123", "Movie")
            assert result is None

    @patch("requests.Session.get")
    def test_find_item_by_provider_id_type_mismatch(self, mock_get):
        """Test find_item_by_provider_id with type mismatch."""
        # Mock response with a series when looking for a movie
        mock_response = Mock()
        mock_response.json.return_value = {
            "Items": [
                {
                    "Id": "item123",
                    "Name": "Test Series",
                    "Type": "Series",  # Series instead of Movie
                    "ProviderIds": {"Imdb": "tt1234567"},
                }
            ]
        }
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        # Look for Movie but item is Series - should return None
        result = client.find_item_by_provider_id("Imdb", "tt1234567", "Movie")
        assert result is None

    @patch("requests.Session.get")
    def test_find_item_by_provider_id_series_success(self, mock_get):
        """Test successful find_item_by_provider_id for series."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "Items": [
                {
                    "Id": "series123",
                    "Name": "Test Series",
                    "Type": "Series",
                    "ProviderIds": {"Tvdb": "123456"},
                }
            ]
        }
        mock_get.return_value = mock_response

        client = EmbyClient(server_url="http://localhost:8096", api_key="test_key")

        # Should find series successfully
        result = client.find_item_by_provider_id("Tvdb", "123456", "Series")
        assert result is not None
        assert result["Id"] == "series123"
        assert result["Name"] == "Test Series"
