"""High-level API for convenient Steam game queries.

This module provides simple synchronous functions that handle the
async client lifecycle automatically, making the library easier to use.
"""

import asyncio

from steam_query.steam_client import SteamStoreClient
from steam_query.types import Game, SearchResult


def search_games(
    query: str,
    limit: int = 10,
    country_code: str | None = None,
    language: str = "english",
) -> list[SearchResult]:
    """Search for Steam games by name (synchronous wrapper).

    This is a convenience function that automatically handles the async
    client lifecycle. For more control, use SteamStoreClient directly.

    Args:
        query: Search keyword
        limit: Maximum number of results (default 10)
        country_code: Country code for pricing (e.g., US, CN, KR, JP)
        language: Language for results (default: english)

    Returns:
        List of search results with typed fields

    Example:
        >>> from steam_query import search_games
        >>> results = search_games("Elden Ring")
        >>> for game in results:
        ...     print(f"{game.name} - {game.price}")
    """
    return asyncio.run(_search_games_async(query, limit, country_code, language))


async def _search_games_async(
    query: str,
    limit: int,
    country_code: str | None,
    language: str,
) -> list[SearchResult]:
    """Internal async implementation of search_games."""
    async with SteamStoreClient(
        country_code=country_code, language=language
    ) as client:
        results = await client.search_games_by_name(query, limit)
        return [SearchResult.from_dict(r) for r in results]


def get_game_info(
    app_id: int,
    country_code: str | None = None,
    language: str = "english",
) -> Game | None:
    """Get detailed information for a Steam game (synchronous wrapper).

    This is a convenience function that automatically handles the async
    client lifecycle. For more control, use SteamStoreClient directly.

    Args:
        app_id: Steam App ID
        country_code: Country code for pricing (e.g., US, CN, KR, JP)
        language: Language for results (default: english)

    Returns:
        Game object with complete information, or None if not found

    Example:
        >>> from steam_query import get_game_info
        >>> game = get_game_info(1245620)  # Elden Ring
        >>> if game:
        ...     print(f"{game.name} - {game.genres}")
        ...     print(f"Metacritic: {game.metacritic_score}/100")
    """
    return asyncio.run(
        _get_game_info_async(app_id, country_code, language)
    )


async def _get_game_info_async(
    app_id: int,
    country_code: str | None,
    language: str,
) -> Game | None:
    """Internal async implementation of get_game_info."""
    async with SteamStoreClient(
        country_code=country_code, language=language
    ) as client:
        data = await client.get_app_details(app_id)
        return Game.from_dict(data) if data else None


def get_games_info(
    app_ids: list[int],
    country_code: str | None = None,
    language: str = "english",
) -> dict[int, Game]:
    """Get detailed information for multiple Steam games (synchronous wrapper).

    This is a convenience function that automatically handles the async
    client lifecycle. For more control, use SteamStoreClient directly.

    Args:
        app_ids: List of Steam App IDs
        country_code: Country code for pricing (e.g., US, CN, KR, JP)
        language: Language for results (default: english)

    Returns:
        Dictionary mapping App IDs to Game objects (only successful lookups)

    Example:
        >>> from steam_query import get_games_info
        >>> games = get_games_info([1245620, 1091500])
        >>> for app_id, game in games.items():
        ...     print(f"{app_id}: {game.name}")
    """
    return asyncio.run(
        _get_games_info_async(app_ids, country_code, language)
    )


async def _get_games_info_async(
    app_ids: list[int],
    country_code: str | None,
    language: str,
) -> dict[int, Game]:
    """Internal async implementation of get_games_info."""
    async with SteamStoreClient(
        country_code=country_code, language=language
    ) as client:
        results = await client.get_games_details_batch(app_ids)
        return {app_id: Game.from_dict(data) for app_id, data in results.items()}
