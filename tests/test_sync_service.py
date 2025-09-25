"""Tests for sync service."""

from unittest.mock import Mock, patch

import pytest

from arr_tagsync.arr_client import ArrClient
from arr_tagsync.emby_client import EmbyClient
from arr_tagsync.sync_service import TagSyncService


class TestTagSyncService:
    """Test TagSyncService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_arr_client = Mock(spec=ArrClient)
        self.mock_arr_client.arr_type = "radarr"

        self.mock_emby_client = Mock(spec=EmbyClient)

        self.sync_service = TagSyncService(
            arr_client=self.mock_arr_client,
            emby_client=self.mock_emby_client,
            dry_run=False,
        )

    def test_init(self):
        """Test TagSyncService initialization."""
        service = TagSyncService(
            arr_client=self.mock_arr_client,
            emby_client=self.mock_emby_client,
            dry_run=True,
        )

        assert service.arr_client == self.mock_arr_client
        assert service.emby_client == self.mock_emby_client
        assert service.dry_run is True
        assert service._arr_tags_cache is None

    def test_get_arr_tags_mapping(self):
        """Test getting Arr tags mapping."""
        mock_tags = [
            {"id": 1, "label": "Action"},
            {"id": 2, "label": "Comedy"},
            {"id": 3, "label": "Drama"},
        ]
        self.mock_arr_client.get_tags.return_value = mock_tags

        result = self.sync_service.get_arr_tags_mapping()

        expected = {1: "Action", 2: "Comedy", 3: "Drama"}
        assert result == expected

        # Test caching - should not call get_tags again
        result2 = self.sync_service.get_arr_tags_mapping()
        assert result2 == expected
        self.mock_arr_client.get_tags.assert_called_once()

    def test_resolve_tag_labels(self):
        """Test resolving tag IDs to labels."""
        mock_tags = [
            {"id": 1, "label": "Action"},
            {"id": 2, "label": "Comedy"},
            {"id": 3, "label": "Drama"},
        ]
        self.mock_arr_client.get_tags.return_value = mock_tags

        result = self.sync_service.resolve_tag_labels([1, 3])

        assert result == ["Action", "Drama"]

    def test_resolve_tag_labels_unknown_tag(self):
        """Test resolving tag IDs when some tags are unknown."""
        mock_tags = [{"id": 1, "label": "Action"}, {"id": 2, "label": "Comedy"}]
        self.mock_arr_client.get_tags.return_value = mock_tags

        result = self.sync_service.resolve_tag_labels([1, 99])  # 99 doesn't exist

        assert result == ["Action", "Unknown-99"]

    def test_find_matching_emby_item_by_tmdb(self):
        """Test finding Emby item by TMDb ID."""
        arr_item = {"title": "Test Movie", "tmdbId": 12345, "imdbId": "tt67890"}

        expected_emby_item = {"Id": "emby123", "Name": "Test Movie"}
        self.mock_emby_client.find_item_by_provider_id.return_value = expected_emby_item

        result = self.sync_service.find_matching_emby_item(arr_item)

        assert result == expected_emby_item
        self.mock_emby_client.find_item_by_provider_id.assert_called_once_with("Tmdb", "12345", "Movie")

    def test_find_matching_emby_item_by_imdb_fallback(self):
        """Test finding Emby item by IMDb ID when TMDb fails."""
        arr_item = {"title": "Test Movie", "tmdbId": 12345, "imdbId": "tt67890"}

        expected_emby_item = {"Id": "emby123", "Name": "Test Movie"}

        # First call (TMDb) returns None, second call (IMDb) returns item
        self.mock_emby_client.find_item_by_provider_id.side_effect = [
            None,
            expected_emby_item,
        ]

        result = self.sync_service.find_matching_emby_item(arr_item)

        assert result == expected_emby_item
        assert self.mock_emby_client.find_item_by_provider_id.call_count == 2

    def test_find_matching_emby_item_sonarr_with_tvdb(self):
        """Test finding Emby item for Sonarr with TVDB ID."""
        self.mock_arr_client.arr_type = "sonarr"

        arr_item = {
            "title": "Test Series",
            "tmdbId": None,
            "imdbId": None,
            "tvdbId": 98765,
        }

        expected_emby_item = {"Id": "emby123", "Name": "Test Series"}

        # Since TMDb and IMDb are None, only TVDB call will be made
        self.mock_emby_client.find_item_by_provider_id.return_value = expected_emby_item

        result = self.sync_service.find_matching_emby_item(arr_item)

        assert result == expected_emby_item
        assert self.mock_emby_client.find_item_by_provider_id.call_count == 1
        # Verify the TVDB call was made with correct parameters
        self.mock_emby_client.find_item_by_provider_id.assert_called_with("Tvdb", "98765", "Series")

    def test_find_matching_emby_item_sonarr_all_ids_tvdb_succeeds(self):
        """Test finding Emby item when TMDb and IMDb fail but TVDB succeeds."""
        self.mock_arr_client.arr_type = "sonarr"

        arr_item = {
            "title": "Test Series",
            "tmdbId": 12345,
            "imdbId": "tt67890",
            "tvdbId": 98765,
        }

        expected_emby_item = {"Id": "emby123", "Name": "Test Series"}

        # TMDb and IMDb return None, TVDB returns item
        self.mock_emby_client.find_item_by_provider_id.side_effect = [
            None,
            None,
            expected_emby_item,
        ]

        result = self.sync_service.find_matching_emby_item(arr_item)

        assert result == expected_emby_item
        assert self.mock_emby_client.find_item_by_provider_id.call_count == 3

        # Verify all three calls were made with correct parameters
        calls = self.mock_emby_client.find_item_by_provider_id.call_args_list
        assert calls[0] == (("Tmdb", "12345", "Series"),)  # TMDb call
        assert calls[1] == (("Imdb", "tt67890", "Series"),)  # IMDb call
        assert calls[2] == (("Tvdb", "98765", "Series"),)  # TVDB call

    def test_find_matching_emby_item_not_found(self):
        """Test when no matching Emby item is found."""
        arr_item = {"title": "Test Movie", "tmdbId": 12345, "imdbId": "tt67890"}

        self.mock_emby_client.find_item_by_provider_id.return_value = None

        result = self.sync_service.find_matching_emby_item(arr_item)

        assert result is None

    def test_sync_tags_for_item_success(self):
        """Test successful tag sync for a single item."""
        # Setup mocks
        mock_tags = [{"id": 1, "label": "Action"}, {"id": 2, "label": "Drama"}]
        self.mock_arr_client.get_tags.return_value = mock_tags

        arr_item = {"title": "Test Movie", "tmdbId": 12345, "tags": [1, 2]}

        emby_item = {
            "Id": "emby123",
            "Name": "Test Movie",
            "Tags": ["Comedy"],  # Different from Arr tags
        }

        self.mock_emby_client.find_item_by_provider_id.return_value = emby_item
        self.mock_emby_client.update_item_tags.return_value = True

        # Execute
        success, message = self.sync_service.sync_tags_for_item(arr_item)

        # Verify
        assert success is True
        assert "Updated tags" in message
        self.mock_emby_client.update_item_tags.assert_called_once_with("emby123", ["Action", "Drama"], dry_run=False)

    def test_sync_tags_for_item_no_emby_match(self):
        """Test sync when no matching Emby item found."""
        arr_item = {"title": "Test Movie", "tmdbId": 12345, "tags": [1, 2]}

        self.mock_emby_client.find_item_by_provider_id.return_value = None

        success, message = self.sync_service.sync_tags_for_item(arr_item)

        assert success is True
        assert "not found in Emby" in message
        assert "may not be imported yet" in message

    def test_sync_tags_for_item_no_tags(self):
        """Test sync when Arr item has no tags."""
        arr_item = {"title": "Test Movie", "tmdbId": 12345, "tags": []}

        emby_item = {"Id": "emby123", "Name": "Test Movie", "Tags": []}
        self.mock_emby_client.find_item_by_provider_id.return_value = emby_item

        success, message = self.sync_service.sync_tags_for_item(arr_item)

        assert success is True
        assert "No tags to sync" in message

    def test_sync_tags_for_item_already_synced(self):
        """Test sync when tags are already up to date."""
        mock_tags = [{"id": 1, "label": "Action"}, {"id": 2, "label": "Drama"}]
        self.mock_arr_client.get_tags.return_value = mock_tags

        arr_item = {"title": "Test Movie", "tmdbId": 12345, "tags": [1, 2]}

        emby_item = {
            "Id": "emby123",
            "Name": "Test Movie",
            "Tags": ["Action", "Drama"],  # Same as Arr tags
        }

        self.mock_emby_client.find_item_by_provider_id.return_value = emby_item

        success, message = self.sync_service.sync_tags_for_item(arr_item)

        assert success is True
        assert "already up to date" in message
        self.mock_emby_client.update_item_tags.assert_not_called()

    def test_sync_all_tags_success(self):
        """Test successful sync of all tags."""
        # Setup mocks
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True

        mock_items = [
            {"id": 1, "title": "Movie 1", "tmdbId": 123, "tags": [1]},
            {"id": 2, "title": "Movie 2", "tmdbId": 456, "tags": [2]},
        ]
        self.mock_arr_client.get_all_items.return_value = mock_items

        # Mock successful sync for both items
        with patch.object(self.sync_service, "sync_tags_for_item") as mock_sync:
            mock_sync.side_effect = [
                (True, "Updated tags: [] -> ['Action']"),
                (True, "Updated tags: [] -> ['Comedy']"),
            ]

            result = self.sync_service.sync_all_tags(batch_size=10)

        # Verify results
        assert result["total_items"] == 2
        assert result["processed_items"] == 2
        assert result["successful_syncs"] == 2
        assert result["failed_syncs"] == 0
        assert len(result["errors"]) == 0

    def test_sync_all_tags_connection_failure(self):
        """Test sync when connection test fails."""
        self.mock_arr_client.test_connection.return_value = False

        with pytest.raises(Exception, match="Failed to connect"):
            self.sync_service.sync_all_tags()

    def test_sync_all_tags_with_failures(self):
        """Test sync with some failures."""
        # Setup mocks
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True

        mock_items = [
            {"id": 1, "title": "Movie 1", "tmdbId": 123, "tags": [1]},
            {"id": 2, "title": "Movie 2", "tmdbId": 456, "tags": [2]},
        ]
        self.mock_arr_client.get_all_items.return_value = mock_items

        # Mock one success and one failure
        with patch.object(self.sync_service, "sync_tags_for_item") as mock_sync:
            mock_sync.side_effect = [
                (True, "Updated tags: [] -> ['Action']"),
                (False, "Failed to update tags"),
            ]

            result = self.sync_service.sync_all_tags(batch_size=10)

        # Verify results
        assert result["total_items"] == 2
        assert result["processed_items"] == 2
        assert result["successful_syncs"] == 1
        assert result["failed_syncs"] == 1
        assert len(result["errors"]) == 1

    def test_prefetch_emby_items_with_exception(self):
        """Test _prefetch_emby_items method exception handling."""

        # Create an object that raises TypeError when len() is called
        class BadLengthObject:
            def __len__(self):
                raise TypeError("Mock error")

        self.mock_emby_client.get_all_movies.return_value = BadLengthObject()

        # Should handle the exception gracefully
        self.sync_service._prefetch_emby_items()

        # Cache should be set to empty list after TypeError
        assert self.sync_service._emby_items_cache == []

        # Test normal cache population
        self.sync_service._emby_items_cache = None
        self.mock_emby_client.get_all_movies.return_value = [
            {"Id": "1", "ProviderIds": {"Tmdb": "123"}},
            {"Id": "2", "ProviderIds": {"Imdb": "tt456"}},
        ]

        # Should populate cache normally
        self.sync_service._prefetch_emby_items()
        assert self.sync_service._emby_items_cache is not None
        assert len(self.sync_service._emby_items_cache) == 2

    def test_find_matching_emby_item_with_debug_logging(self):
        """Test find_matching_emby_item debug path when no match found."""
        arr_item = {"title": "Test Movie", "tmdbId": 12345, "imdbId": "tt67890"}

        # Return None to trigger debug path
        self.mock_emby_client.find_item_by_provider_id.return_value = None

        with patch("arr_tagsync.sync_service.logger") as mock_logger:
            result = self.sync_service.find_matching_emby_item(arr_item)

            assert result is None
            # Should have called debug logging
            mock_logger.debug.assert_called()

    def test_sync_tags_for_item_with_exception(self):
        """Test sync_tags_for_item exception handling."""
        arr_item = {"title": "Test Movie", "tmdbId": 12345, "tags": [1]}

        # Make find_item_by_provider_id raise exception
        self.mock_emby_client.find_item_by_provider_id.side_effect = Exception("Network error")

        success, message = self.sync_service.sync_tags_for_item(arr_item)

        assert success is False
        assert "Network error" in message

    def test_sync_all_tags_arr_connection_failure(self):
        """Test sync_all_tags with Arr connection failure."""
        self.mock_arr_client.test_connection.return_value = False

        with pytest.raises(Exception, match="Failed to connect to radarr"):
            self.sync_service.sync_all_tags()

    def test_sync_all_tags_emby_connection_failure(self):
        """Test sync_all_tags with Emby connection failure."""
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = False

        with pytest.raises(Exception, match="Failed to connect to Emby server"):
            self.sync_service.sync_all_tags()

    def test_sync_all_tags_item_not_in_emby_message(self):
        """Test sync_all_tags with 'not found in Emby' message."""
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True
        self.mock_arr_client.get_all_items.return_value = [{"id": 1, "title": "Not Found Movie", "tags": [1]}]

        with patch.object(self.sync_service, "sync_tags_for_item") as mock_sync:
            mock_sync.return_value = (True, "Item not found in Emby")

            result = self.sync_service.sync_all_tags()

            assert result["not_in_emby"] == 1
            assert result["processed_items"] == 1

    def test_sync_all_tags_already_up_to_date_message(self):
        """Test sync_all_tags with 'already up to date' message."""
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True
        self.mock_arr_client.get_all_items.return_value = [{"id": 1, "title": "Synced Movie", "tags": [1]}]

        with patch.object(self.sync_service, "sync_tags_for_item") as mock_sync:
            mock_sync.return_value = (True, "Tags already up to date")

            result = self.sync_service.sync_all_tags()

            assert result["already_synced"] == 1
            assert result["processed_items"] == 1

    def test_sync_all_tags_no_tags_to_sync_message(self):
        """Test sync_all_tags with 'No tags to sync' message."""
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True
        self.mock_arr_client.get_all_items.return_value = [{"id": 1, "title": "No Tags Movie", "tags": []}]

        with patch.object(self.sync_service, "sync_tags_for_item") as mock_sync:
            mock_sync.return_value = (True, "No tags to sync")

            result = self.sync_service.sync_all_tags()

            assert result["no_tags_to_sync"] == 1
            assert result["processed_items"] == 1

    def test_sync_all_tags_sync_item_exception(self):
        """Test sync_all_tags when sync_tags_for_item raises exception."""
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True
        self.mock_arr_client.get_all_items.return_value = [{"id": 1, "title": "Error Movie", "tags": [1]}]

        with patch.object(self.sync_service, "sync_tags_for_item") as mock_sync:
            mock_sync.side_effect = Exception("Unexpected error")

            result = self.sync_service.sync_all_tags()

            assert result["failed_syncs"] == 1
            # processed_items is not incremented if exception occurs in sync_tags_for_item
            assert result["processed_items"] == 0
            assert "Unexpected error" in result["errors"][0]

    def test_sync_all_tags_cache_info_with_cache(self):
        """Test sync_all_tags cache info logging with available cache."""
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True
        self.mock_arr_client.get_all_items.return_value = []

        # Mock cache with some entries
        self.mock_emby_client._provider_id_cache = {"test": "data", "test2": "data2"}

        result = self.sync_service.sync_all_tags()

        assert result["total_items"] == 0

    def test_sync_all_tags_cache_info_no_cache(self):
        """Test sync_all_tags cache info logging without cache."""
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True
        self.mock_arr_client.get_all_items.return_value = []

        # Remove cache attribute to trigger AttributeError
        if hasattr(self.mock_emby_client, "_provider_id_cache"):
            delattr(self.mock_emby_client, "_provider_id_cache")

        result = self.sync_service.sync_all_tags()

        assert result["total_items"] == 0

    def test_sync_all_tags_overall_exception(self):
        """Test sync_all_tags when overall exception occurs."""
        self.mock_arr_client.test_connection.return_value = True
        self.mock_emby_client.test_connection.return_value = True

        # Make get_all_items raise exception
        self.mock_arr_client.get_all_items.side_effect = Exception("Critical error")

        with pytest.raises(Exception, match="Critical error"):
            self.sync_service.sync_all_tags()

    def test_clear_caches(self):
        """Test clearing all caches."""
        # Set up some cached data
        self.sync_service._arr_tags_cache = {"test": "data"}
        self.sync_service._emby_items_cache = {"test": "data"}

        # Clear caches
        self.sync_service.clear_caches()

        # Verify caches are cleared
        assert self.sync_service._arr_tags_cache is None
        assert self.sync_service._emby_items_cache is None
        self.mock_emby_client.clear_cache.assert_called_once()

    def test_prefetch_emby_items_already_cached(self):
        """Test _prefetch_emby_items when cache is already populated."""
        # Set cache to already have data
        self.sync_service._emby_items_cache = [{"Id": "cached"}]

        # Should return early without calling get_all_movies
        self.sync_service._prefetch_emby_items()

        # get_all_movies should not have been called
        self.mock_emby_client.get_all_movies.assert_not_called()

    def test_find_matching_emby_item_debug_sonarr(self):
        """Test find_matching_emby_item debug logging for sonarr items."""
        # Set arr_type to sonarr for TVDB debugging
        self.mock_arr_client.arr_type = "sonarr"

        arr_item = {"title": "Test Series", "tmdbId": 12345, "imdbId": "tt67890", "tvdbId": 98765}

        # Return None to trigger debug path
        self.mock_emby_client.find_item_by_provider_id.return_value = None

        with patch("arr_tagsync.sync_service.logger") as mock_logger:
            result = self.sync_service.find_matching_emby_item(arr_item)

            assert result is None
            # Should have called debug logging with TVDB info
            mock_logger.debug.assert_called()
            debug_call = mock_logger.debug.call_args[0][0]
            assert "TMDb: 12345" in debug_call
            assert "IMDb: tt67890" in debug_call
            assert "TVDB: 98765" in debug_call

    def test_sync_tags_for_item_emby_update_failure(self):
        """Test sync_tags_for_item when Emby update fails."""
        mock_tags = [{"id": 1, "label": "Action"}]
        self.mock_arr_client.get_tags.return_value = mock_tags

        arr_item = {"title": "Test Movie", "tmdbId": 12345, "tags": [1]}

        emby_item = {"Id": "emby123", "Name": "Test Movie", "Tags": []}

        self.mock_emby_client.find_item_by_provider_id.return_value = emby_item
        # Make update_item_tags return False to simulate failure
        self.mock_emby_client.update_item_tags.return_value = False

        success, message = self.sync_service.sync_tags_for_item(arr_item)

        assert success is False
        assert "Failed to update tags in Emby" in message
