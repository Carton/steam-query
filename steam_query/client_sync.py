"""Synchronous Steam query client."""

import asyncio
import time
from logging import getLogger
from typing import Any

from .exceptions import GameNotFoundError
from .steam_client import SteamStoreClient
from .types import Game, SearchResult

logger = getLogger(__name__)


class _Cache:
    """Simple LRU cache with TTL."""

    def __init__(self, maxsize: int = 128, ttl: int = 300):
        """Initialize cache.

        Args:
            maxsize: Maximum number of items
            ttl: Time-to-live in seconds
        """
        self._cache: dict[str, Any] = {}
        self._cache_time: dict[str, float] = {}
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        """Get from cache.

        Args:
            key: Cache key

        Returns:
            Cached value, or None if not found/expired
        """
        if key not in self._cache:
            return None

        # Check TTL
        if time.time() - self._cache_time[key] > self._ttl:
            del self._cache[key]
            del self._cache_time[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set in cache with LRU eviction.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value
        self._cache_time[key] = time.time()

        # LRU eviction
        if len(self._cache) > self._maxsize:
            oldest_key = min(self._cache_time, key=self._cache_time.get)
            del self._cache[oldest_key]
            del self._cache_time[oldest_key]

    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
        self._cache_time.clear()


async def _search_async(
    query: str,
    limit: int,
    country_code: str | None,
    language: str,
    requests_per_second: float = 1.0,
) -> list[dict]:
    """Internal async implementation for search."""
    async with SteamStoreClient(
        country_code=country_code, language=language, requests_per_second=requests_per_second
    ) as client:
        return await client.search_games_by_name(query, limit)


async def _get_game_async(
    app_id: int,
    country_code: str | None,
    language: str,
    requests_per_second: float = 1.0,
) -> dict | None:
    """Internal async implementation for get."""
    async with SteamStoreClient(
        country_code=country_code, language=language, requests_per_second=requests_per_second
    ) as client:
        return await client.get_app_details(app_id)


async def _get_batch_async(
    app_ids: list[int],
    country_code: str | None,
    language: str,
    requests_per_second: float = 1.0,
) -> dict[int, dict]:
    """Internal async implementation for get_batch (serial query)."""
    results = {}

    async with SteamStoreClient(
        country_code=country_code, language=language, requests_per_second=requests_per_second
    ) as client:
        for app_id in app_ids:
            try:
                data = await client.get_app_details(app_id)
                if data:
                    results[app_id] = data
            except Exception as e:
                logger.warning(f"Failed to fetch {app_id}: {e}")

    return results


class SteamQuery:
    """Synchronous Steam query client.

    Provides simple sync API that automatically handles async client lifecycle.
    Includes built-in LRU cache with TTL.
    """

    def __init__(
        self,
        country_code: str | None = None,
        language: str = "english",
        cache_size: int = 128,
        cache_ttl: int = 300,
        requests_per_second: float = 1.0,
    ):
        """Initialize client.

        Args:
            country_code: Country code (US, CN, JP, etc.)
            language: Language (default: english)
            cache_size: Cache size (default: 128)
            cache_ttl: Cache TTL in seconds (default: 300)
            requests_per_second: Rate limit (default 1 req/sec)
        """
        from .steam_client import _get_default_country

        self.country_code = country_code or _get_default_country()
        self.language = language
        self._cache_size = cache_size
        self._cache_ttl = cache_ttl
        self._cache = _Cache(maxsize=cache_size, ttl=cache_ttl)
        self._requests_per_second = requests_per_second

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search games (simple style).

        Args:
            query: Search keyword
            limit: Result count limit

        Returns:
            List of search results

        Raises:
            NetworkError: Network error
            APIError: API error
        """
        # Check cache
        cache_key = f"search:{query}:{limit}:{self.country_code}:{self.language}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from API
        results = asyncio.run(
            _search_async(query, limit, self.country_code, self.language, self._requests_per_second)
        )
        result_objects = [SearchResult.from_dict(r) for r in results]

        # Cache result
        self._cache.set(cache_key, result_objects)

        return result_objects

    def get(self, app_id: int) -> Game:
        """Get game details.

        Args:
            app_id: Steam App ID

        Returns:
            Game details

        Raises:
            GameNotFoundError: Game not found
            NetworkError: Network error
        """
        # Check cache
        cache_key = f"get:{app_id}:{self.country_code}:{self.language}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from API
        data = asyncio.run(_get_game_async(app_id, self.country_code, self.language, self._requests_per_second))

        if data is None:
            raise GameNotFoundError(app_id=app_id)

        game = Game.from_dict(data)

        # Cache result
        self._cache.set(cache_key, game)

        return game

    def get_batch(self, app_ids: list[int]) -> dict[int, Game]:
        """Batch get game details (serial query).

        Note: Uses serial query for non-official API safety.
        Note: Batch queries are not cached.

        Args:
            app_ids: List of App IDs

        Returns:
            Dict mapping App ID -> Game (successful queries only)
        """
        results = asyncio.run(
            _get_batch_async(app_ids, self.country_code, self.language, self._requests_per_second)
        )
        return {app_id: Game.from_dict(data) for app_id, data in results.items()}

    def find(self, query: str) -> Game | None:
        """Search and return first match.

        Args:
            query: Search keyword

        Returns:
            Game info, or None if not found
        """
        results = self.search(query, limit=1)
        if not results:
            return None

        return self.get(results[0].app_id)
