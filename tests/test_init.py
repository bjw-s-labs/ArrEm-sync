"""Tests for module imports."""

from unittest.mock import patch


class TestModuleImports:
    """Test module import behavior."""

    def test_successful_imports(self):
        """Test successful imports expose all classes."""
        import arrem_sync

        # Should have all expected exports
        expected_exports = ["ArrClient", "Config", "EmbyClient", "TagSyncService", "get_config"]

        for export in expected_exports:
            assert hasattr(arrem_sync, export)
            assert export in arrem_sync.__all__

    def test_import_error_fallback(self):
        """Test graceful handling when external dependencies are missing."""
        # Mock ImportError for external dependencies
        with (
            patch("arrem_sync.arr_client", side_effect=ImportError("Missing dependency")),
            patch("arrem_sync.emby_client", side_effect=ImportError("Missing dependency")),
            patch("arrem_sync.sync_service", side_effect=ImportError("Missing dependency")),
        ):
            # Re-import to trigger the exception handling
            import importlib

            import arrem_sync

            importlib.reload(arrem_sync)

            # Should only have basic config exports
            expected_basic_exports = ["Config", "get_config"]

            for export in expected_basic_exports:
                assert hasattr(arrem_sync, export)

            # Should have limited __all__ list
            assert "Config" in arrem_sync.__all__
            assert "get_config" in arrem_sync.__all__

    def test_module_metadata(self):
        """Test module metadata."""
        import arrem_sync

        assert hasattr(arrem_sync, "__version__")
        assert hasattr(arrem_sync, "__author__")
        assert hasattr(arrem_sync, "__email__")

        # Should have reasonable values
        assert isinstance(arrem_sync.__version__, str)
        assert len(arrem_sync.__version__) > 0
