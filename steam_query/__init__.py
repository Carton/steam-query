"""Steam Query - Query detailed information for any Steam game.

This library provides a simple interface to query Steam game information
without requiring any API keys or user login.

Quick Start:
    >>> from steam_query import search_games, get_game_info
    >>>
    >>> # Search for games
    >>> results = search_games("Elden Ring")
    >>> for game in results:
    ...     print(f"{game.name} - ${game.price.final if game.price else 'Free'}")
    >>>
    >>> # Get detailed game information
    >>> game = get_game_info(1245620)
    >>> if game:
    ...     print(f"{game.name}")
    ...     print(f"Genres: {', '.join(game.genres)}")
    ...     print(f"Metacritic: {game.metacritic_score}/100")

Advanced Usage (async):
    >>> import asyncio
    >>> from steam_query import SteamStoreClient
    >>>
    >>> async def main():
    ...     async with SteamStoreClient(country_code="JP") as client:
    ...         results = await client.search_games_by_name("Hollow Knight", limit=5)
    ...         for game_dict in results:
    ...             print(f"{game_dict['name']}: {game_dict.get('price')}")
    >>>
    >>> asyncio.run(main())
"""

from steam_query.api import get_game_info, get_games_info, search_games
from steam_query.client_sync import SteamQuery
from steam_query.steam_client import SteamStoreClient
from steam_query.types import Game, Price, SearchResult, SystemRequirements

__version__ = "1.0.0"

__all__ = [
    # Version
    "__version__",
    # Core client (advanced usage)
    "SteamStoreClient",
    # Sync client (simple API)
    "SteamQuery",
    # High-level API (recommended for most users)
    "search_games",
    "get_game_info",
    "get_games_info",
    # Data models
    "Game",
    "SearchResult",
    "Price",
    "SystemRequirements",
]
