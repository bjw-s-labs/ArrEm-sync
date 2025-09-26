"""ArrEm-sync: Sync tags between Radarr/Sonarr and Emby."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ArrEm-sync")
except PackageNotFoundError:
    # Fallback for editable/source checkouts without installed dist
    __version__ = "0.0.2"

__author__ = "bjw-s-labs"
__email__ = ""

from .config import Config, get_config

# These require external dependencies, so import conditionally
try:
    from .arr_client import ArrClient
    from .emby_client import EmbyClient
    from .sync_service import TagSyncService

    __all__ = [
        "ArrClient",
        "Config",
        "EmbyClient",
        "TagSyncService",
        "__version__",
        "get_config",
    ]
except ImportError:
    # If external dependencies are missing, only expose config
    __all__ = ["Config", "__version__", "get_config"]
