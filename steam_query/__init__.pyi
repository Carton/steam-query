"""Type stubs for steam_query"""

from dataclasses import dataclass
from typing import Any


# Data models
@dataclass(frozen=True)
class Price:
    """Price information."""

    initial: float | None
    final: float | None
    discount_percent: int
    currency: str

    @property
    def is_free(self) -> bool: ...
    @property
    def is_discounted(self) -> bool: ...


@dataclass(frozen=True)
class SystemRequirements:
    """System requirements."""

    english: str
    parsed: dict[str, str]


@dataclass(frozen=True)
class Game:
    """Complete game information."""

    app_id: int
    name: str
    short_desc: str
    long_desc: str
    release_date: str | None
    developers: list[str]
    publishers: list[str]
    genres: list[str]
    tags: list[str]
    metacritic_score: int | None
    price: Price | None
    platforms: list[str]
    is_free: bool
    header_image: str
    screenshots: list[str]
    website: str | None
    requirements: dict[str, SystemRequirements]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Game": ...


@dataclass(frozen=True)
class SearchResult:
    """Search result."""

    app_id: int
    name: str
    short_desc: str
    price: Price | None
    platforms: list[str]
    metacritic_score: int | None
    review_score: int | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResult": ...


# Async client
class SteamStoreClient:
    """Async Steam Store API client."""

    def __init__(
        self,
        requests_per_second: float = 1.0,
        country_code: str | None = None,
        language: str = "english",
    ) -> None: ...
    async def __aenter__(self) -> "SteamStoreClient": ...
    async def __aexit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None: ...
    async def search_games_by_name(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]: ...
    async def get_app_details(
        self, app_id: int
    ) -> dict[str, Any] | None: ...
    async def get_games_details_batch(
        self, app_ids: list[int]
    ) -> dict[int, dict[str, Any]]: ...


# Sync client
class SteamQuery:
    """Synchronous Steam query client."""

    def __init__(
        self,
        country_code: str | None = None,
        language: str = "english",
        cache_size: int = 128,
        cache_ttl: int = 300,
    ) -> None: ...
    def search(
        self, query: str, limit: int = 10
    ) -> list[SearchResult]: ...
    def get(self, app_id: int) -> Game: ...
    def get_batch(self, app_ids: list[int]) -> dict[int, Game]: ...
    def find(self, query: str) -> Game | None: ...


# High-level API functions
def search_games(
    query: str,
    limit: int = 10,
    country_code: str | None = None,
    language: str = "english",
) -> list[SearchResult]: ...

def get_game_info(
    app_id: int,
    country_code: str | None = None,
    language: str = "english",
) -> Game | None: ...

def get_games_info(
    app_ids: list[int],
    country_code: str | None = None,
    language: str = "english",
) -> dict[int, Game]: ...


# Version
__version__: str
