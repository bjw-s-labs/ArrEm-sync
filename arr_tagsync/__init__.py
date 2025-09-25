"""arr-tagsync: Sync tags between Radarr/Sonarr and Emby."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .config import Config, get_config

# These require external dependencies, so import conditionally
try:
    from .arr_client import ArrClient
    from .emby_client import EmbyClient
    from .sync_service import TagSyncService

    __all__ = ["ArrClient", "Config", "EmbyClient", "TagSyncService", "get_config"]
except ImportError:
    # If external dependencies are missing, only expose config
    __all__ = ["Config", "get_config"]
