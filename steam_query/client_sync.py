"""Synchronous Steam query client."""

import asyncio
from logging import getLogger

from .exceptions import GameNotFoundError
from .steam_client import SteamStoreClient
from .types import Game, SearchResult

logger = getLogger(__name__)


async def _search_async(
    query: str,
    limit: int,
    country_code: str | None,
    language: str,
) -> list[dict]:
    """Internal async implementation for search."""
    async with SteamStoreClient(country_code=country_code, language=language) as client:
        return await client.search_games_by_name(query, limit)


async def _get_game_async(
    app_id: int,
    country_code: str | None,
    language: str,
) -> dict | None:
    """Internal async implementation for get."""
    async with SteamStoreClient(country_code=country_code, language=language) as client:
        return await client.get_app_details(app_id)


async def _get_batch_async(
    app_ids: list[int],
    country_code: str | None,
    language: str,
) -> dict[int, dict]:
    """Internal async implementation for get_batch (serial query)."""
    results = {}

    async with SteamStoreClient(country_code=country_code, language=language) as client:
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
    """

    def __init__(
        self,
        country_code: str | None = None,
        language: str = "english",
        cache_size: int = 128,
        cache_ttl: int = 300,
    ):
        """Initialize client.

        Args:
            country_code: Country code (US, CN, JP, etc.)
            language: Language (default: english)
            cache_size: Cache size (default: 128)
            cache_ttl: Cache TTL in seconds (default: 300)
        """
        from .steam_client import _get_default_country

        self.country_code = country_code or _get_default_country()
        self.language = language
        self._cache_size = cache_size
        self._cache_ttl = cache_ttl

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
        results = asyncio.run(
            _search_async(query, limit, self.country_code, self.language)
        )
        return [SearchResult.from_dict(r) for r in results]

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
        data = asyncio.run(_get_game_async(app_id, self.country_code, self.language))

        if data is None:
            raise GameNotFoundError(app_id=app_id)

        return Game.from_dict(data)

    def get_batch(self, app_ids: list[int]) -> dict[int, Game]:
        """Batch get game details (serial query).

        Note: Uses serial query for non-official API safety.

        Args:
            app_ids: List of App IDs

        Returns:
            Dict mapping App ID -> Game (successful queries only)
        """
        results = asyncio.run(
            _get_batch_async(app_ids, self.country_code, self.language)
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
