# Steam Query Library Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 5 library improvements: custom exceptions, sync OOP API (SteamQuery), caching, type stubs, and integration tests.

**Architecture:**
- Custom exceptions as foundation
- SteamQuery class wrapping async client with sync interface
- Built-in LRU cache with TTL
- Complete type stubs for mypy
- Integration tests with real API (marked, optional)

**Tech Stack:**
- Python 3.11+
- pytest, pytest-asyncio (testing)
- mypy (type checking)
- dataclasses (type-safe models)
- asyncio (async/sync bridge)

**Order:** Sequential (dependencies: exceptions → SteamQuery → cache → type stubs → integration tests)

---

## Task 1: Custom Exception Classes

**Files:**
- Create: `steam_query/exceptions.py`
- Modify: `steam_query/steam_client.py` (integrate exceptions)
- Test: `tests/test_exceptions.py`

### Step 1: Write the failing tests

Create `tests/test_exceptions.py`:

```python
"""Tests for custom exceptions."""

import pytest
from steam_query.exceptions import (
    SteamQueryError,
    NetworkError,
    TimeoutError,
    APIError,
    RateLimitError,
    GameNotFoundError,
    InvalidResponseError,
    ConfigurationError,
)


class TestExceptionHierarchy:
    """Test exception hierarchy"""

    def test_steam_query_error_is_exception(self):
        """Test that SteamQueryError is an Exception"""
        error = SteamQueryError("test")
        assert isinstance(error, Exception)
        assert str(error) == "test"

    def test_network_error_inherits_from_base(self):
        """Test NetworkError inherits from SteamQueryError"""
        error = NetworkError("network failed")
        assert isinstance(error, SteamQueryError)
        assert isinstance(error, Exception)

    def test_timeout_error_inherits_from_base(self):
        """Test TimeoutError inherits from SteamQueryError"""
        error = TimeoutError("request timeout")
        assert isinstance(error, SteamQueryError)

    def test_api_error_inherits_from_base(self):
        """Test APIError inherits from SteamQueryError"""
        error = APIError("API error", status_code=500)
        assert isinstance(error, SteamQueryError)
        assert error.status_code == 500

    def test_rate_limit_error_inherits_from_api_error(self):
        """Test RateLimitError inherits from APIError"""
        error = RateLimitError("Too many requests")
        assert isinstance(error, APIError)
        assert isinstance(error, SteamQueryError)

    def test_invalid_response_error_inherits_from_base(self):
        """Test InvalidResponseError inherits from SteamQueryError"""
        error = InvalidResponseError("Invalid JSON")
        assert isinstance(error, SteamQueryError)

    def test_configuration_error_inherits_from_base(self):
        """Test ConfigurationError inherits from SteamQueryError"""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, SteamQueryError)


class TestGameNotFoundError:
    """Test GameNotFoundError specific behavior"""

    def test_with_app_id(self):
        """Test creating error with App ID"""
        error = GameNotFoundError(app_id=1245620)
        assert "1245620" in str(error)
        assert error.app_id == 1245620
        assert error.query is None

    def test_with_query(self):
        """Test creating error with query"""
        error = GameNotFoundError(query="Elden Ring")
        assert "Elden Ring" in str(error)
        assert error.query == "Elden Ring"
        assert error.app_id is None

    def test_without_app_id_or_query(self):
        """Test creating error without App ID or query"""
        error = GameNotFoundError()
        assert "Game not found" in str(error)


class TestAPIError:
    """Test APIError specific behavior"""

    def test_with_status_code(self):
        """Test APIError with status code"""
        error = APIError("Not found", status_code=404)
        assert error.status_code == 404
        assert "404" in str(error)

    def test_without_status_code(self):
        """Test APIError without status code"""
        error = APIError("API error")
        assert error.status_code is None
```

### Step 2: Run tests to verify they fail

Run:
```bash
pytest tests/test_exceptions.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'steam_query.exceptions'`

### Step 3: Create exception classes

Create `steam_query/exceptions.py`:

```python
"""Custom exceptions for steam-query."""


class SteamQueryError(Exception):
    """Base exception for all steam-query errors."""

    pass


class NetworkError(SteamQueryError):
    """Network request failed."""

    pass


class TimeoutError(SteamQueryError):
    """Request timeout."""

    pass


class APIError(SteamQueryError):
    """Steam API returned an error."""

    def __init__(self, message: str, status_code: int | None = None):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code (if available)
        """
        self.status_code = status_code
        if status_code:
            message = f"{message} (status: {status_code})"
        super().__init__(message)


class RateLimitError(APIError):
    """Rate limit exceeded."""

    pass


class GameNotFoundError(SteamQueryError):
    """Game not found."""

    def __init__(self, app_id: int | None = None, query: str | None = None):
        """Initialize game not found error.

        Args:
            app_id: Steam App ID
            query: Search query
        """
        self.app_id = app_id
        self.query = query

        if app_id:
            message = f"Game not found: App ID {app_id}"
        elif query:
            message = f"Game not found: {query}"
        else:
            message = "Game not found"

        super().__init__(message)


class InvalidResponseError(SteamQueryError):
    """Invalid API response data."""

    pass


class ConfigurationError(SteamQueryError):
    """Configuration error."""

    pass
```

### Step 4: Run tests to verify they pass

Run:
```bash
pytest tests/test_exceptions.py -v
```

Expected: PASS (13 tests)

### Step 5: Commit

```bash
git add steam_query/exceptions.py tests/test_exceptions.py
git commit -m "feat: add custom exception classes

- Add SteamQueryError base class
- Add NetworkError, TimeoutError
- Add APIError with status_code
- Add RateLimitError
- Add GameNotFoundError with app_id/query
- Add InvalidResponseError, ConfigurationError
- Add 13 tests for all exceptions
```

---

## Task 2: Integrate Exceptions into SteamStoreClient

**Files:**
- Modify: `steam_query/steam_client.py`
- Test: Update tests in `tests/test_exceptions.py`

### Step 1: Add imports

Edit `steam_query/steam_client.py` line 11-12:

```python
import aiohttp
from ratelimit import limits, sleep_and_retry

from .exceptions import APIError, GameNotFoundError, InvalidResponseError, NetworkError
```

### Step 2: Update _get method to raise custom exceptions

Edit `steam_query/steam_client.py` lines 104-122:

```python
@sleep_and_retry
@limits(calls=1, period=1)  # 1 req/sec
async def _get(
    self, url: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """HTTP GET request (with rate limiting)"""
    if not self._session:
        raise RuntimeError("Client not initialized, please use async with")

    try:
        async with self._session.get(url, params=params) as response:
            # Handle HTTP errors
            if response.status == 429:
                raise APIError("Rate limit exceeded", status_code=429)
            if response.status >= 500:
                raise APIError(f"Server error: {response.status}", status_code=response.status)
            if response.status == 404:
                raise APIError("Not found", status_code=404)

            response.raise_for_status()
            return await response.json()

    except aiohttp.ClientError as e:
        logger.error(f"HTTP error: {e}")
        raise NetworkError(f"Network error: {e}") from e
    except APIError:
        raise  # Re-raise API errors
    except Exception as e:
        logger.error(f"Unknown error: {e}")
        raise NetworkError(f"Request failed: {e}") from e
```

### Step 3: Update get_app_details to raise GameNotFoundError

Edit `steam_query/steam_client.py` lines 202-220:

```python
async def get_app_details(self, app_id: int) -> dict[str, Any] | None:
    """Get detailed game information

    Args:
        app_id: Steam App ID

    Returns:
        Dictionary with detailed game information

    Raises:
        GameNotFoundError: Game not found
        NetworkError: Network error
        APIError: API error
    """
    logger.debug(f"Getting game details: {app_id}")

    # Steam Store API (no API key required)
    url = "https://store.steampowered.com/api/appdetails"
    params = {"appids": app_id, "l": self.language, "cc": self.country_code}

    try:
        data = await self._get(url, params)

        if str(app_id) not in data or not data[str(app_id)].get("success"):
            raise GameNotFoundError(app_id=app_id)

        app_data = data[str(app_id)]["data"]
        return self._parse_app_details(app_data)

    except GameNotFoundError:
        raise
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get details (app_id={app_id}): {e}")
        raise InvalidResponseError(f"Invalid response for app_id={app_id}") from e
```

### Step 4: Add tests for exception integration

Add to `tests/test_exceptions.py`:

```python
class TestExceptionIntegration:
    """Test exceptions raised by SteamStoreClient"""

    @pytest.mark.asyncio
    async def test_get_app_details_raises_game_not_found(self):
        """Test get_app_details raises GameNotFoundError"""
        from steam_query.steam_client import SteamStoreClient

        async with SteamStoreClient() as client:
            with pytest.raises(GameNotFoundError) as exc_info:
                await client.get_app_details(999999999)

            assert exc_info.value.app_id == 999999999
            assert "999999999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_empty_results_returns_empty_list(self):
        """Test search with no results returns empty list (not error)"""
        from steam_query.steam_client import SteamStoreClient

        async with SteamStoreClient() as client:
            results = await client.search_games_by_name("NonExistentGameXYZ123", limit=10)

            assert results == []
```

### Step 5: Run tests to verify they pass

Run:
```bash
pytest tests/test_exceptions.py -v
```

Expected: PASS (15 tests)

### Step 6: Run all tests to ensure no regressions

Run:
```bash
pytest tests/ -v
```

Expected: All existing tests still pass

### Step 7: Commit

```bash
git add steam_query/steam_client.py tests/test_exceptions.py
git commit -m "feat: integrate custom exceptions into SteamStoreClient

- Update _get to raise NetworkError, APIError
- Update get_app_details to raise GameNotFoundError
- Add InvalidResponseError for parsing failures
- Add integration tests for exceptions
- Maintain backward compatibility (empty results = [])
```

---

## Task 3: Create SteamQuery Sync Client

**Files:**
- Create: `steam_query/client_sync.py`
- Modify: `steam_query/__init__.py` (export SteamQuery)
- Test: `tests/test_client_sync.py`

### Step 3.1: Write failing tests for basic functionality

Create `tests/test_client_sync.py`:

```python
"""Tests for SteamQuery sync client."""

from unittest.mock import AsyncMock, patch

import pytest

from steam_query import SteamQuery
from steam_query.exceptions import GameNotFoundError


class TestSteamQueryInit:
    """Test SteamQuery initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default values"""
        client = SteamQuery()

        assert client.country_code == "US"  # Default from _get_default_country
        assert client.language == "english"
        assert client._cache_size == 128
        assert client._cache_ttl == 300

    def test_init_with_custom_values(self):
        """Test initialization with custom values"""
        client = SteamQuery(
            country_code="JP",
            language="japanese",
            cache_size=64,
            cache_ttl=600,
        )

        assert client.country_code == "JP"
        assert client.language == "japanese"
        assert client._cache_size == 64
        assert client._cache_ttl == 600


class TestSteamQuerySearch:
    """Test search method"""

    @patch("steam_query.client_sync._search_async")
    def test_search_returns_results(self, mock_search):
        """Test search returns list of SearchResult"""
        from steam_query.types import SearchResult, Price

        mock_results = [
            {
                "app_id": 1245620,
                "name": "ELDEN RING",
                "short_desc": "Action RPG",
                "price": {
                    "initial": 59.99,
                    "final": 59.99,
                    "discount_percent": 0,
                    "currency": "USD",
                },
                "platforms": ["Windows"],
                "metacritic": {"score": 96},
                "review_score": None,
            }
        ]
        mock_search.return_value = mock_results

        client = SteamQuery(country_code="US", language="english")
        results = client.search("Elden Ring", limit=5)

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].name == "ELDEN RING"
        assert results[0].app_id == 1245620
        assert results[0].price.final == 59.99

    @patch("steam_query.client_sync._search_async")
    def test_search_empty_results(self, mock_search):
        """Test search with no results"""
        mock_search.return_value = []

        client = SteamQuery()
        results = client.search("NonExistentGame")

        assert results == []


class TestSteamQueryGet:
    """Test get method"""

    @patch("steam_query.client_sync._get_game_async")
    def test_get_returns_game(self, mock_get):
        """Test get returns Game object"""
        from steam_query.types import Game, Price

        mock_game_dict = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "short_desc": "Action RPG",
            "long_desc": "Full description",
            "release_date": "2022-02-25",
            "developers": ["FromSoftware Inc."],
            "publishers": ["BANDAI NAMCO"],
            "genres": ["Action RPG"],
            "tags": ["Fantasy"],
            "metacritic_score": 96,
            "price": {
                "initial": 59.99,
                "final": 59.99,
                "discount_percent": 0,
                "currency": "USD",
            },
            "platforms": ["Windows"],
            "is_free": False,
            "header_image": "header.jpg",
            "screenshots": [],
            "website": "https://eldenring.com",
            "requirements": {},
        }
        mock_get.return_value = mock_game_dict

        client = SteamQuery()
        game = client.get(1245620)

        assert game is not None
        assert isinstance(game, Game)
        assert game.name == "ELDEN RING"
        assert game.app_id == 1245620
        assert game.developers == ["FromSoftware Inc."]

    @patch("steam_query.client_sync._get_game_async")
    def test_get_raises_game_not_found(self, mock_get):
        """Test get raises GameNotFoundError"""
        mock_get.return_value = None

        client = SteamQuery()

        with pytest.raises(GameNotFoundError) as exc_info:
            client.get(999999999)

        assert exc_info.value.app_id == 999999999


class TestSteamQueryGetBatch:
    """Test get_batch method"""

    @patch("steam_query.client_sync._get_batch_async")
    def test_get_batch_returns_multiple_games(self, mock_batch):
        """Test get_batch returns dict of Games"""
        from steam_query.types import Game

        mock_batch.return_value = {
            1245620: {
                "app_id": 1245620,
                "name": "ELDEN RING",
                "short_desc": "",
                "long_desc": "",
                "release_date": "2022-02-25",
                "developers": [],
                "publishers": [],
                "genres": [],
                "tags": [],
                "metacritic_score": None,
                "price": None,
                "platforms": [],
                "is_free": False,
                "header_image": "",
                "screenshots": [],
                "website": None,
                "requirements": {},
            },
            1091500: {
                "app_id": 1091500,
                "name": "Cyberpunk 2077",
                "short_desc": "",
                "long_desc": "",
                "release_date": "2020-12-10",
                "developers": [],
                "publishers": [],
                "genres": [],
                "tags": [],
                "metacritic_score": None,
                "price": None,
                "platforms": [],
                "is_free": False,
                "header_image": "",
                "screenshots": [],
                "website": None,
                "requirements": {},
            },
        }

        client = SteamQuery()
        games = client.get_batch([1245620, 1091500, 9999999])

        assert len(games) == 2
        assert 1245620 in games
        assert 1091500 in games
        assert 9999999 not in games
        assert isinstance(games[1245620], Game)
        assert games[1245620].name == "ELDEN RING"


class TestSteamQueryFind:
    """Test find method"""

    @patch("steam_query.client_sync._search_async")
    @patch("steam_query.client_sync._get_game_async")
    def test_find_returns_first_result(self, mock_get, mock_search):
        """Test find returns first matching game"""
        mock_search.return_value = [
            {"app_id": 1245620, "name": "ELDEN RING", "short_desc": "", "price": None,
             "platforms": [], "metacritic": None, "review_score": None}
        ]
        mock_get.return_value = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "short_desc": "",
            "long_desc": "",
            "release_date": None,
            "developers": [],
            "publishers": [],
            "genres": [],
            "tags": [],
            "metacritic_score": None,
            "price": None,
            "platforms": [],
            "is_free": False,
            "header_image": "",
            "screenshots": [],
            "website": None,
            "requirements": {},
        }

        client = SteamQuery()
        game = client.find("Elden Ring")

        assert game is not None
        assert game.name == "ELDEN RING"

    @patch("steam_query.client_sync._search_async")
    def test_find_returns_none_if_no_results(self, mock_search):
        """Test find returns None if no search results"""
        mock_search.return_value = []

        client = SteamQuery()
        game = client.find("NonExistentGame")

        assert game is None
```

### Step 3.2: Run tests to verify they fail

Run:
```bash
pytest tests/test_client_sync.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'steam_query.client_sync'`

### Step 3.3: Implement SteamQuery class (without cache)

Create `steam_query/client_sync.py`:

```python
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
```

### Step 3.4: Run tests to verify they pass

Run:
```bash
pytest tests/test_client_sync.py -v
```

Expected: PASS (12 tests)

### Step 3.5: Export SteamQuery from __init__.py

Edit `steam_query/__init__.py`:

```python
"""Steam Query - Query detailed information for any Steam game."""

# ... existing docstring ...

from steam_query.api import get_game_info, get_games_info, search_games
from steam_query.client_sync import SteamQuery  # NEW
from steam_query.steam_client import SteamStoreClient
from steam_query.types import Game, Price, SearchResult, SystemRequirements

__version__ = "1.0.0"

__all__ = [
    # Version
    "__version__",
    # Core client (advanced usage)
    "SteamStoreClient",
    # Sync client (NEW)
    "SteamQuery",
    # High-level API (recommended)
    "search_games",
    "get_game_info",
    "get_games_info",
    # Data models
    "Game",
    "SearchResult",
    "Price",
    "SystemRequirements",
]
```

### Step 3.6: Run all tests to ensure no regressions

Run:
```bash
pytest tests/ -v
```

Expected: All tests pass

### Step 3.7: Commit

```bash
git add steam_query/client_sync.py steam_query/__init__.py tests/test_client_sync.py
git commit -m "feat: add SteamQuery sync client

- Add SteamQuery class with simple API
- Add search(), get(), get_batch(), find() methods
- Serial batch query for non-official API safety
- Add 12 tests for SteamQuery
- Export SteamQuery from __init__.py
```

---

## Task 4: Add Caching to SteamQuery

**Files:**
- Modify: `steam_query/client_sync.py` (add _Cache class)
- Test: `tests/test_client_sync.py` (add cache tests)

### Step 4.1: Write failing cache tests

Add to `tests/test_client_sync.py`:

```python
class TestSteamQueryCache:
    """Test caching functionality"""

    @patch("steam_query.client_sync._get_game_async")
    def test_cache_returns_same_result(self, mock_get):
        """Test that cached result is identical"""
        mock_get.return_value = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "short_desc": "",
            "long_desc": "",
            "release_date": "2022-02-25",
            "developers": [],
            "publishers": [],
            "genres": [],
            "tags": [],
            "metacritic_score": None,
            "price": None,
            "platforms": [],
            "is_free": False,
            "header_image": "",
            "screenshots": [],
            "website": None,
            "requirements": {},
        }

        client = SteamQuery(cache_ttl=60)

        # First call
        game1 = client.get(1245620)
        # Second call (should hit cache)
        game2 = client.get(1245620)

        assert game1 == game2
        # Should only call async function once
        assert mock_get.call_count == 1

    @patch("steam_query.client_sync._get_game_async")
    def test_cache_expires_after_ttl(self, mock_get):
        """Test that cache expires after TTL"""
        import time

        mock_get.return_value = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "short_desc": "",
            "long_desc": "",
            "release_date": "2022-02-25",
            "developers": [],
            "publishers": [],
            "genres": [],
            "tags": [],
            "metacritic_score": None,
            "price": None,
            "platforms": [],
            "is_free": False,
            "header_image": "",
            "screenshots": [],
            "website": None,
            "requirements": {},
        }

        client = SteamQuery(cache_ttl=1, cache_size=10)

        # First call
        client.get(1245620)
        # Wait for cache to expire
        time.sleep(2)
        # Second call (should not hit cache)
        client.get(1245620)

        assert mock_get.call_count == 2

    @patch("steam_query.client_sync._get_game_async")
    def test_cache_lru_eviction(self, mock_get):
        """Test LRU eviction when cache is full"""
        client = SteamQuery(cache_size=2, cache_ttl=60)

        mock_game = {
            "app_id": 1,
            "name": "Game 1",
            "short_desc": "",
            "long_desc": "",
            "release_date": None,
            "developers": [],
            "publishers": [],
            "genres": [],
            "tags": [],
            "metacritic_score": None,
            "price": None,
            "platforms": [],
            "is_free": False,
            "header_image": "",
            "screenshots": [],
            "website": None,
            "requirements": {},
        }

        def get_mock(app_id):
            return {**mock_game, "app_id": app_id, "name": f"Game {app_id}"}

        mock_get.side_effect = [
            get_mock(1),
            get_mock(2),
            get_mock(3),
            get_mock(1),  # Should fetch again (evicted)
        ]

        # Fill cache (size=2)
        client.get(1)
        client.get(2)
        # This should evict app_id=1
        client.get(3)
        # This should fetch from API (evicted)
        client.get(1)

        assert mock_get.call_count == 4
```

### Step 4.2: Run tests to verify they fail

Run:
```bash
pytest tests/test_client_sync.py::TestSteamQueryCache -v
```

Expected: FAIL (cache not implemented yet)

### Step 4.3: Implement cache in SteamQuery

Edit `steam_query/client_sync.py`:

```python
"""Synchronous Steam query client."""

import asyncio
import time
from logging import getLogger

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


# ... (_search_async, _get_game_async, _get_batch_async remain the same) ...


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
        self._cache = _Cache(maxsize=cache_size, ttl=cache_ttl)

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
            _search_async(query, limit, self.country_code, self.language)
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
        data = asyncio.run(_get_game_async(app_id, self.country_code, self.language))

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
```

### Step 4.4: Run tests to verify they pass

Run:
```bash
pytest tests/test_client_sync.py::TestSteamQueryCache -v
```

Expected: PASS (4 tests)

### Step 4.5: Run all tests to ensure no regressions

Run:
```bash
pytest tests/ -v
```

Expected: All tests pass

### Step 4.6: Commit

```bash
git add steam_query/client_sync.py tests/test_client_sync.py
git commit -m "feat: add LRU cache with TTL to SteamQuery

- Add _Cache class with LRU eviction
- Cache search() and get() results
- Configurable cache size and TTL
- get_batch() not cached (one-time queries)
- Add 4 cache tests
```

---

## Task 5: Create Type Stubs

**Files:**
- Create: `steam_query/__init__.pyi`
- Test: Manual mypy check

### Step 5.1: Create type stub file

Create `steam_query/__init__.pyi`:

```python
"""Type stubs for steam_query"""

from dataclasses import dataclass
from typing import Any, NotRequired


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
```

### Step 5.2: Verify with mypy

Run:
```bash
mypy steam_query --ignore-missing-imports
```

Expected: No errors (or minimal errors)

### Step 5.3: Add mypy to pyproject.toml

Edit `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
warn_return_any = true
warn_unused_configs = true
```

### Step 5.4: Run mypy check

Run:
```bash
mypy steam_query
```

Expected: Success

### Step 5.5: Commit

```bash
git add steam_query/__init__.pyi pyproject.toml
git commit -m "feat: add type stubs for complete mypy support

- Add __init__.pyi with all public API types
- Add type annotations for SteamQuery, SteamStoreClient
- Add type annotations for data models
- Add type annotations for high-level functions
- Add mypy configuration
```

---

## Task 6: Integration Tests

**Files:**
- Create: `tests/test_integration.py`
- Modify: `pyproject.toml` (add pytest markers)

### Step 6.1: Add pytest marker configuration

Edit `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
]
```

### Step 6.2: Create integration tests

Create `tests/test_integration.py`:

```python
"""Integration tests with real Steam API

These tests are marked as 'integration' and can be skipped:
- pytest tests/ -m "not integration"  # Skip integration tests
- pytest tests/ -m integration         # Run only integration tests
"""

import time
import pytest

from steam_query import SteamQuery, get_game_info, search_games
from steam_query.exceptions import GameNotFoundError


# Test data: Popular, stable games
ELDEN_RING = 1245620
HOLLOW_KNIGHT = 367520
HADES = 1593500
CYBERPUNK = 1091500


@pytest.mark.integration
class TestSteamQueryRealAPI:
    """Test SteamQuery with real API"""

    def test_get_elden_ring(self):
        """Test fetching a popular game (Elden Ring)"""
        client = SteamQuery()

        game = client.get(ELDEN_RING)

        assert game is not None
        assert game.name == "ELDEN RING"
        assert game.app_id == ELDEN_RING
        assert len(game.developers) > 0
        assert len(game.genres) > 0
        assert len(game.platforms) > 0

    def test_search_hollow_knight(self):
        """Test searching for Hollow Knight"""
        client = SteamQuery()

        results = client.search("Hollow Knight", limit=5)

        assert len(results) > 0
        # First result should be Hollow Knight
        assert "Hollow Knight" in results[0].name
        assert results[0].app_id == HOLLOW_KNIGHT

    def test_get_batch_multiple_games(self):
        """Test batch query"""
        client = SteamQuery()

        games = client.get_batch([ELDEN_RING, CYBERPUNK, HADES])

        assert len(games) == 3
        assert ELDEN_RING in games
        assert CYBERPUNK in games
        assert HADES in games
        assert games[ELDEN_RING].name == "ELDEN RING"
        assert games[CYBERPUNK].name == "Cyberpunk 2077"
        assert games[HADES].name == "Hades"

    def test_cache_works(self):
        """Test that caching reduces actual API calls"""
        client = SteamQuery(cache_ttl=60)

        # First call - should hit API
        start = time.time()
        game1 = client.get(ELDEN_RING)
        first_duration = time.time() - start

        # Second call - should hit cache
        start = time.time()
        game2 = client.get(ELDEN_RING)
        second_duration = time.time() - start

        assert game1 == game2
        # Cached call should be much faster (< 50% of first call)
        assert second_duration < first_duration / 2

    def test_find_hades(self):
        """Test find method"""
        client = SteamQuery()

        game = client.find("Hades")

        assert game is not None
        assert game.name == "Hades"
        assert game.app_id == HADES


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling with real API"""

    def test_game_not_found(self):
        """Test fetching non-existent game"""
        client = SteamQuery()

        with pytest.raises(GameNotFoundError) as exc_info:
            client.get(999999999)

        assert exc_info.value.app_id == 999999999

    def test_search_empty_results(self):
        """Test search with no results"""
        client = SteamQuery()

        results = client.search("NonExistentGameXYZ123", limit=10)

        assert results == []


@pytest.mark.integration
class TestHighLevelAPI:
    """Test high-level API functions"""

    def test_search_games_function(self):
        """Test search_games function"""
        results = search_games("Stardew Valley", limit=3)

        assert len(results) > 0
        assert "Stardew Valley" in results[0].name

    def test_get_game_info_function(self):
        """Test get_game_info function"""
        game = get_game_info(HADES)

        assert game is not None
        assert game.name == "Hades"
        assert game.app_id == HADES

    def test_get_games_info_function(self):
        """Test get_games_info function"""
        games = get_games_info([ELDEN_RING, HADES])

        assert len(games) == 2
        assert ELDEN_RING in games
        assert HADES in games
```

### Step 6.3: Run only unit tests (fast)

Run:
```bash
pytest tests/ -m "not integration" -v
```

Expected: All unit tests pass (fast)

### Step 6.4: Run integration tests (requires network)

Run:
```bash
pytest tests/ -m integration -v
```

Expected: Integration tests pass (slower, requires network)

### Step 6.5: Commit

```bash
git add tests/test_integration.py pyproject.toml
git commit -m "test: add integration tests with real API

- Add integration tests for SteamQuery
- Add integration tests for error handling
- Add integration tests for high-level API
- Add pytest marker configuration
- Use stable test data (Elden Ring, Hollow Knight, Hades)
- Test cache effectiveness with real API
- Can be skipped with -m 'not integration'
"
```

---

## Task 7: Update Documentation

**Files:**
- Update: `README.md`
- Create: `LIBRARY_API.md`

### Step 7.1: Update README.md

Add section about SteamQuery class:

```markdown
## Library Usage

### Quick Start

```python
from steam_query import SteamQuery

# Create client
client = SteamQuery(country_code="US")

# Search games
games = client.search("Elden Ring", limit=5)
for game in games:
    print(f"{game.name}: ${game.price.final if game.price else 'Free'}")

# Get game details
game = client.get(1245620)  # Elden Ring
print(f"{game.name}")
print(f"Genres: {', '.join(game.genres)}")
print(f"Metacritic: {game.metacritic_score}/100")

# Batch query
games = client.get_batch([1245620, 1091500, 1593500])
for app_id, game in games.items():
    print(f"{app_id}: {game.name}")
```

### Caching

```python
# Custom cache settings
client = SteamQuery(
    cache_size=256,    # Cache up to 256 items
    cache_ttl=600,     # Cache for 10 minutes
)
```

### Error Handling

```python
from steam_query.exceptions import GameNotFoundError

try:
    game = client.get(999999999)
except GameNotFoundError as e:
    print(f"Game not found: {e.app_id}")
```
```

### Step 7.2: Commit

```bash
git add README.md
git commit -m "docs: update README with SteamQuery usage examples

- Add SteamQuery quick start
- Add caching documentation
- Add error handling examples
"
```

---

## Final Verification

### Step: Run full test suite

Run:
```bash
# Unit tests only (fast)
pytest tests/ -m "not integration" -v

# Full test suite (slow)
pytest tests/ -v

# Type checking
mypy steam_query
```

Expected:
- All unit tests pass (~70 tests)
- Integration tests pass (or skipped)
- mypy clean

### Step: Create summary commit

```bash
git add .
git commit -m "chore: final cleanup and verification

- All 5 improvements implemented
- Custom exceptions ✓
- SteamQuery sync client ✓
- LRU cache with TTL ✓
- Type stubs ✓
- Integration tests ✓
- All tests passing
- Ready for release
"
```

---

## Summary

**Total Changes:**
- 5 new features implemented
- ~30 new tests added
- ~50 new tests passing
- Complete type stub coverage
- Full backward compatibility

**Files Created:**
- `steam_query/exceptions.py`
- `steam_query/client_sync.py`
- `steam_query/__init__.pyi`
- `tests/test_exceptions.py`
- `tests/test_client_sync.py`
- `tests/test_integration.py`
- `docs/plans/2026-03-06-library-improvements-implementation.md`

**Files Modified:**
- `steam_query/__init__.py`
- `steam_query/steam_client.py`
- `pyproject.toml`
- `README.md`

**Test Coverage:**
- Unit tests: ~70 tests
- Integration tests: ~10 tests
- Total: ~80 tests

**Next Steps:**
1. Bump version to 1.1.0 or 2.0.0
2. Update CHANGELOG.md
3. Create GitHub release
4. Publish to PyPI
