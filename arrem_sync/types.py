"""Typed structures for Arr and Emby entities used in the app.

These types are intentionally lightweight and match only the fields we read.
They keep runtime overhead zero while improving static guarantees.
"""

from typing import Literal, NotRequired, TypedDict


class ArrTag(TypedDict):
    id: int
    label: str


class ArrItem(TypedDict, total=False):
    id: int
    title: str
    tmdbId: int | None
    imdbId: str | None
    tvdbId: int | None  # Sonarr only
    tags: list[int]


class EmbyTagItem(TypedDict, total=False):
    Name: str
    Id: NotRequired[int]


class EmbyItem(TypedDict, total=False):
    Id: str
    Name: str
    Type: Literal["Movie", "Series"]
    TagItems: list[EmbyTagItem]
    ProviderIds: dict[str, str | int]
    Path: str
