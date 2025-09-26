"""Factory functions for creating client instances."""

import logging
from typing import TYPE_CHECKING

from .arr_client import ArrClient
from .emby_client import EmbyClient

if TYPE_CHECKING:
    from .config import Config

logger = logging.getLogger(__name__)


def create_arr_clients(config: "Config") -> list[ArrClient]:
    """Create ArrClient instances from configuration.

    Args:
        config: Application configuration

    Returns:
        List of configured ArrClient instances

    Raises:
        ValueError: If no Arr instances are configured
    """
    if not config.arr_instances:
        raise ValueError("No Arr instances configured")

    clients = []
    for i, instance in enumerate(config.arr_instances, 1):
        try:
            client = ArrClient(
                arr_type=instance.type,
                base_url=instance.url,
                api_key=instance.api_key,
            )
            clients.append(client)
            logger.info(f"Created {instance.type} client for instance {i}: {instance.name or 'Unnamed'}")
        except Exception as e:
            logger.error(f"Failed to create client for instance {i} ({instance.name or 'Unnamed'}): {e}")
            raise

    return clients


def create_emby_client(config: "Config") -> EmbyClient:
    """Create EmbyClient instance from configuration.

    Args:
        config: Application configuration

    Returns:
        Configured EmbyClient instance
    """
    return EmbyClient(
        server_url=config.emby_url,
        api_key=config.emby_api_key,
    )


def create_clients(config: "Config") -> tuple[list[ArrClient], EmbyClient]:
    """Create all configured clients.

    Args:
        config: Application configuration

    Returns:
        Tuple of (list of arr_clients, emby_client)
    """
    arr_clients = create_arr_clients(config)
    emby_client = create_emby_client(config)

    return arr_clients, emby_client
