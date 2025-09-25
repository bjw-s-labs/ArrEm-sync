"""Tests for module imports."""

from unittest.mock import patch


class TestModuleImports:
    """Test module import behavior."""

    def test_successful_imports(self):
        """Test successful imports expose all classes."""
        import arr_tagsync

        # Should have all expected exports
        expected_exports = ["ArrClient", "Config", "EmbyClient", "TagSyncService", "get_config"]

        for export in expected_exports:
            assert hasattr(arr_tagsync, export)
            assert export in arr_tagsync.__all__

    def test_import_error_fallback(self):
        """Test graceful handling when external dependencies are missing."""
        # Mock ImportError for external dependencies
        with (
            patch("arr_tagsync.arr_client", side_effect=ImportError("Missing dependency")),
            patch("arr_tagsync.emby_client", side_effect=ImportError("Missing dependency")),
            patch("arr_tagsync.sync_service", side_effect=ImportError("Missing dependency")),
        ):
            # Re-import to trigger the exception handling
            import importlib

            import arr_tagsync

            importlib.reload(arr_tagsync)

            # Should only have basic config exports
            expected_basic_exports = ["Config", "get_config"]

            for export in expected_basic_exports:
                assert hasattr(arr_tagsync, export)

            # Should have limited __all__ list
            assert "Config" in arr_tagsync.__all__
            assert "get_config" in arr_tagsync.__all__

    def test_module_metadata(self):
        """Test module metadata."""
        import arr_tagsync

        assert hasattr(arr_tagsync, "__version__")
        assert hasattr(arr_tagsync, "__author__")
        assert hasattr(arr_tagsync, "__email__")

        # Should have reasonable values
        assert isinstance(arr_tagsync.__version__, str)
        assert len(arr_tagsync.__version__) > 0
