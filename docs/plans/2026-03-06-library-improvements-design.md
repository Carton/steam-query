# Steam Query Library Improvements - Design Document

**Date:** 2026-03-06
**Author:** Carton He
**Status:** Approved

## Overview

This document outlines the design for improving the steam-query library with better API design, error handling, caching, type support, and integration testing.

## Goals

1. **Better API Design**: Add synchronous OOP interface alongside existing functional API
2. **Better Error Handling**: Custom exceptions with clear error messages
3. **Better Performance**: Built-in caching to avoid redundant API calls
4. **Better Type Support**: Complete type stubs for mypy
5. **Better Testing**: Integration tests with real API

## Non-Goals

- ~~Concurrent query optimization~~: Deferred until official Steam API + API key support is added
- Breaking changes: All additions are backward compatible

## Implementation Tasks

### 1. Custom Exception Classes

**File:** `steam_query/exceptions.py`

```python
class SteamQueryError(Exception):
    """Base exception for all steam-query errors"""

class NetworkError(SteamQueryError):
    """Network request failed"""

class TimeoutError(SteamQueryError):
    """Request timeout"""

class APIError(SteamQueryError):
    """Steam API returned an error"""
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)

class RateLimitError(APIError):
    """Rate limit exceeded"""

class GameNotFoundError(SteamQueryError):
    """Game not found"""
    def __init__(self, app_id: int | None = None, query: str | None = None):
        self.app_id = app_id
        self.query = query
        # ... construct message

class InvalidResponseError(SteamQueryError):
    """Invalid API response data"""

class ConfigurationError(SteamQueryError):
    """Configuration error"""
```

**Integration Points:**
- Update `steam_client.py` to raise custom exceptions
- Update `api.py` to raise custom exceptions

### 2. Synchronous OOP API - SteamQuery Class

**File:** `steam_query/client_sync.py`

```python
class SteamQuery:
    """Synchronous Steam query client

    Simple, clean API that automatically handles async client lifecycle.
    """

    def __init__(
        self,
        country_code: str | None = None,
        language: str = "english",
        cache_size: int = 128,
        cache_ttl: int = 300,
    ):
        """Initialize client

        Args:
            country_code: Country code (US, CN, JP, etc.)
            language: Language (default: english)
            cache_size: Cache size (default: 128)
            cache_ttl: Cache TTL in seconds (default: 300)
        """
        ...

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search games (simple style)

        Args:
            query: Search keyword
            limit: Result count limit

        Returns:
            List of search results

        Raises:
            NetworkError: Network error
            APIError: API error
        """
        ...

    def get(self, app_id: int) -> Game:
        """Get game details

        Args:
            app_id: Steam App ID

        Returns:
            Game details

        Raises:
            GameNotFoundError: Game not found
            NetworkError: Network error
        """
        ...

    def get_batch(self, app_ids: list[int]) -> dict[int, Game]:
        """Batch get game details (serial query)

        Note: Uses serial query for non-official API safety.
        Consider official API + API key for concurrent queries.

        Args:
            app_ids: List of App IDs

        Returns:
            Dict mapping App ID -> Game (successful queries only)
        """
        ...

    def find(self, query: str) -> Game | None:
        """Search and return first match

        Args:
            query: Search keyword

        Returns:
            Game info, or None if not found
        """
        ...
```

**Design Decisions:**
- **Simple API style**: `client.search("Elden Ring")` instead of `client.search_games(query="Elden Ring")`
- **Serial batch query**: For non-official API safety
- **Automatic cache management**: Built-in LRU cache with TTL
- **Automatic exception handling**: Converts low-level errors to custom exceptions

### 3. Caching Mechanism

**Implementation:** Custom LRU cache with TTL in `SteamQuery` class

```python
class _Cache:
    """Simple LRU cache with TTL"""

    def __init__(self, maxsize: int = 128, ttl: int = 300):
        self._cache: dict[str, Any] = {}
        self._cache_time: dict[str, float] = {}
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        """Get from cache"""
        if key not in self._cache:
            return None

        # Check TTL
        if time.time() - self._cache_time[key] > self._ttl:
            del self._cache[key]
            del self._cache_time[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set in cache with LRU eviction"""
        self._cache[key] = value
        self._cache_time[key] = time.time()

        # LRU eviction
        if len(self._cache) > self._maxsize:
            oldest_key = min(self._cache_time, key=self._cache_time.get)
            del self._cache[oldest_key]
            del self._cache_time[oldest_key]

    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        self._cache_time.clear()
```

**Cache Keys:**
- `search`: `("search", query, limit, country, language)`
- `get`: `("get", app_id, country, language)`
- `get_batch`: Not cached (batch queries are typically one-time)

**Configuration:**
- `cache_size=128`: Max 128 cached items
- `cache_ttl=300`: Cache expires after 5 minutes

### 4. Type Stubs

**File:** `steam_query/__init__.pyi`

Complete type annotations for all public APIs:
- Data models (`Game`, `SearchResult`, `Price`, `SystemRequirements`)
- Async client (`SteamStoreClient`)
- Sync client (`SteamQuery`)
- High-level functions (`search_games`, `get_game_info`, `get_games_info`)

**Benefits:**
- ✅ Better IDE autocomplete
- ✅ Complete mypy support
- ✅ Better parameter hints
- ✅ No runtime performance impact

### 5. Integration Tests

**File:** `tests/test_integration.py`

```python
@pytest.mark.integration
class TestSteamQueryRealAPI:
    """Test SteamQuery with real API"""

    def test_get_elden_ring(self):
        """Test fetching a popular game"""
        client = SteamQuery()
        game = client.get(1245620)  # Elden Ring

        assert game is not None
        assert game.name == "ELDEN RING"
        ...

    def test_search_hollow_knight(self):
        """Test searching for Hollow Knight"""
        client = SteamQuery()
        results = client.search("Hollow Knight", limit=5)

        assert len(results) > 0
        assert "Hollow Knight" in results[0].name
        ...

    def test_cache_works(self):
        """Test that caching reduces API calls"""
        import time

        client = SteamQuery(cache_ttl=60)

        # First call - hits API
        start = time.time()
        game1 = client.get(1245620)
        first_duration = time.time() - start

        # Second call - hits cache
        start = time.time()
        game2 = client.get(1245620)
        second_duration = time.time() - start

        assert game1 == game2
        assert second_duration < first_duration / 2
```

**Test Data:**
Use popular, stable games:
- Elden Ring (1245620)
- Hollow Knight (367520)
- Hades (1593500)
- Cyberpunk 2077 (1091500)

**Configuration:**

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
]
```

**Run Commands:**
```bash
# Only unit tests (fast)
pytest tests/ -m "not integration"

# Only integration tests (requires network)
pytest tests/ -m integration

# All tests
pytest tests/
```

## Implementation Order

Based on dependency analysis:

1. **Custom Exceptions** (`steam_query/exceptions.py`)
   - No dependencies
   - Foundation for other modules

2. **SteamQuery Class** (`steam_query/client_sync.py`)
   - Depends on: Custom exceptions
   - Core feature

3. **Cache Mechanism**
   - Integrated into SteamQuery class
   - Depends on: SteamQuery class

4. **Type Stubs** (`steam_query/__init__.pyi`)
   - Independent
   - Can be done anytime

5. **Integration Tests** (`tests/test_integration.py`)
   - Depends on: All above features
   - Final validation

## File Structure

```
steam_query/
├── __init__.py          # Public API exports
├── __init__.pyi         # Type stubs (NEW)
├── exceptions.py        # Custom exceptions (NEW)
├── client_sync.py       # Sync OOP API (NEW)
├── api.py               # Functional API (existing)
├── steam_client.py      # Async OOP API (existing)
└── types.py             # Data models (existing)

tests/
├── test_api.py          # Unit tests for API (existing)
├── test_cli.py          # Unit tests for CLI (existing)
└── test_integration.py  # Integration tests (NEW)
```

## Backward Compatibility

All changes are **additive only**:
- ✅ Existing API functions remain unchanged
- ✅ Existing CLI behavior unchanged
- ✅ New SteamQuery class is optional
- ✅ New exceptions are raised but can be caught as `Exception`

## Testing Strategy

1. **Unit Tests**: Test each module in isolation
   - Exception classes
   - SteamQuery methods (mocked async client)
   - Cache functionality
   - Type stub validation

2. **Integration Tests**: Test with real API
   - Marked with `@pytest.mark.integration`
   - Use stable test data
   - Test cache effectiveness
   - Test error handling

3. **Regression Tests**: Ensure nothing breaks
   - All existing tests must pass
   - Current target: 58 tests passing
   - After additions: ~80 tests passing

## Success Criteria

- [ ] All custom exceptions defined and integrated
- [ ] SteamQuery class fully implemented with tests
- [ ] Cache mechanism working and tested
- [ ] Type stubs complete and mypy clean
- [ ] Integration tests passing (or skipped appropriately)
- [ ] All existing tests still passing
- [ ] Documentation updated

## Future Enhancements

Out of scope for this iteration:

1. **Concurrent Queries**: Add official Steam API support with API key
2. **Persistent Cache**: Add disk caching option
3. **Retry Logic**: Add exponential backoff for transient failures
4. **Metrics**: Add performance metrics and logging

## References

- Steam Store API: `https://store.steampowered.com/api/`
- Python dataclasses: `https://docs.python.org/3/library/dataclasses.html`
- pytest markers: `https://docs.pytest.org/en/stable/mark/`
- Type stubs: `https://peps.python.org/pep-0484/`
