"""HTTP utilities shared across clients."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type-only import for annotations
    from collections.abc import Iterable

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session(
    *,
    total_retries: int = 3,
    status_forcelist: Iterable[int] = (429, 500, 502, 503, 504),
    backoff_factor: float = 1.0,
    allowed_methods: Iterable[str] = ("HEAD", "GET", "OPTIONS"),
    pool_connections: int = 10,
    pool_maxsize: int = 20,
) -> Session:
    """Create a requests.Session with retry and connection pooling configured.

    Args:
        total_retries: Total number of retries for idempotent requests.
        status_forcelist: HTTP statuses that should trigger a retry.
        backoff_factor: Backoff factor for retries.
        allowed_methods: HTTP methods eligible for retry.
        pool_connections: Number of connection pools to cache.
        pool_maxsize: Maximum number of connections to save in the pool.

    Returns:
        Configured requests.Session instance.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=total_retries,
        status_forcelist=list(status_forcelist),
        allowed_methods=set(allowed_methods),
        backoff_factor=backoff_factor,
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
