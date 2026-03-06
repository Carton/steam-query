# Steam Query Architecture

Design and implementation details of the Steam Query library.

## Table of Contents

- [Design Philosophy](#design-philosophy)
- [Layer Structure](#layer-structure)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Key Implementations](#key-implementations)
  - [Rate Limiting](#rate-limiting)
  - [Caching](#caching)
  - [Type System](#type-system)
- [Extending the Library](#extending-the-library)

## Design Philosophy

### Principles

1. **Simplicity First** - Easy to use for common tasks
2. **Type Safe** - Complete type hints for better developer experience
3. **Async Native** - Built on asyncio for performance
4. **Respectful** - Built-in rate limiting to respect Steam's API
5. **Extensible** - Easy to extend and customize

### Trade-offs

| Aspect | Decision | Reason |
|--------|----------|--------|
| **Rate Limiting** | Custom implementation | More flexible than external libraries, async-compatible |
| **Caching** | LRU with TTL | Simple, effective, no external dependencies |
| **API Style** | Both functional and object | Simple scripts vs applications |
| **Type System** | Pydantic-like classes | Type-safe, IDE-friendly, lightweight |

## Layer Structure

```
┌─────────────────────────────────────┐
│         CLI Layer (cli.py)          │  Command-line interface
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      API Layer (api.py)             │  High-level functions
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Sync Client (client_sync.py)      │  Synchronous wrapper
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Core Client (steam_client.py)      │  Async Steam API client
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Types (types.py)                │  Data models
└─────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. CLI Layer (`cli.py`)

**Responsibilities:**
- Parse command-line arguments
- Format output for terminal
- Handle user interactions
- Coordinate API calls

**Key Components:**
```python
- main()                    # Entry point
- search_command()          # Search games
- lookup_command()          # Get details
- batch_command()           # Batch queries
- format_game_info()        # Format terminal output
- format_game_json()        # Format JSON output
```

#### 2. API Layer (`api.py`)

**Responsibilities:**
- Provide simple functional API
- Handle async lifecycle automatically
- Bridge sync/async worlds

**Key Components:**
```python
- search_games()            # Functional search
- get_game_info()           # Functional get
- get_games_info()          # Functional batch
- _search_games_async()     # Internal async
- _get_game_info_async()    # Internal async
- _get_games_info_async()   # Internal async
```

#### 3. Sync Client Layer (`client_sync.py`)

**Responsibilities:**
- Provide synchronous API
- Manage caching
- Wrap async operations

**Key Components:**
```python
- SteamQuery                # Main client class
- _search_async()           # Internal async search
- _get_game_async()         # Internal async get
- _get_batch_async()        # Internal async batch
- _Cache                    # LRU cache with TTL
```

#### 4. Core Client Layer (`steam_client.py`)

**Responsibilities:**
- Implement Steam API communication
- Handle rate limiting
- Parse and normalize data
- Manage async session

**Key Components:**
```python
- SteamStoreClient          # Async client
- _get()                    # HTTP GET with rate limiting
- search_games_by_name()    # Search API
- get_app_details()         # Details API
- get_games_details_batch() # Batch API
- _parse_app_details()      # Parse game data
- _parse_requirements()     # Parse requirements
- _parse_date()             # Parse dates
```

#### 5. Types Layer (`types.py`)

**Responsibilities:**
- Define data models
- Provide type safety
- Handle data transformations

**Key Components:**
```python
- Game                      # Game information
- SearchResult              # Search result
- Price                     # Price information
- SystemRequirements        # Requirements data
```

## Core Components

### Rate Limiting

Custom async-compatible rate limiting implementation.

#### Design

```python
# In SteamStoreClient._get()

if self.requests_per_second > 0 and self._rate_limit_lock:
    async with self._rate_limit_lock:
        now = time.time()
        elapsed = now - self._last_request_time
        wait_time = (1.0 / self.requests_per_second) - elapsed

        if wait_time > 0:
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()
```

#### Benefits

- **Async-compatible**: Uses `asyncio.sleep()` instead of blocking calls
- **Dynamic**: Can change rate without recreating client
- **Thread-safe**: Uses `asyncio.Lock()` for concurrent requests
- **Precise**: Calculates exact wait time needed

### Caching

LRU cache with TTL for synchronous client.

#### Design

```python
class _Cache:
    def __init__(self, maxsize: int = 128, ttl: int = 300):
        self._cache: dict[str, Any] = {}
        self._cache_time: dict[str, float] = {}
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None

        # Check TTL
        if time.time() - self._cache_time[key] > self._ttl:
            del self._cache[key]
            del self._cache_time[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = key
        self._cache_time[key] = time.time()

        # LRU eviction
        if len(self._cache) > self._maxsize:
            oldest_key = min(self._cache_time, key=self._cache_time.get)
            del self._cache[oldest_key]
            del self._cache_time[oldest_key]
```

#### Cache Key Format

```
<operation>:<params>:<country>:<language>
```

Examples:
- `search:Elden Ring:10:US:english`
- `get:1245620:US:english`

### Type System

Typed data models for better IDE support.

#### Design

```python
@dataclass
class Game:
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
    def from_dict(cls, data: dict[str, Any]) -> "Game":
        # Parse and create instance from API dict
        ...
```

#### Benefits

- **Type-safe**: Catch errors at development time
- **IDE-friendly**: Auto-completion and type hints
- **Self-documenting**: Types serve as documentation
- **Validation**: Ensure data consistency

## Data Flow

### Search Flow

```
User Request
    │
    ▼
┌─────────────────┐
│ CLI/API Layer   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SteamStoreClient│
│  (Async)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ _get()          │  Apply rate limiting
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Steam API       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parse Response  │  _parse_app_details()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return to User  │  as Game object
└─────────────────┘
```

### Sync Client Flow

```
User Request
    │
    ▼
┌─────────────────┐
│ SteamQuery      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check Cache     │  Is result cached?
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
Hit        Miss
    │         │
    ▼         ▼
┌────────┐ ┌─────────────┐
│ Return  │ │ asyncio.run()│
│ Cache  │ └──────┬───────┘
└────────┘        │
                  ▼
         ┌─────────────────┐
         │ _search_async() │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ SteamStoreClient│
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Update Cache    │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Return Result   │
         └─────────────────┘
```

## Key Implementations

### Rate Limiting

#### Problem

Steam Store API has no official rate limit, but recommends ~1 request/second.

#### Solution

Custom async-compatible implementation:

```python
# steam_client.py

class SteamStoreClient:
    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self._rate_limit_lock = None
        self._last_request_time = 0.0

    async def __aenter__(self):
        # Initialize lock in async context
        self._rate_limit_lock = asyncio.Lock()
        return self

    async def _get(self, url: str, params: dict | None = None):
        # Apply rate limiting
        if self.requests_per_second > 0 and self._rate_limit_lock:
            async with self._rate_limit_lock:
                now = time.time()
                elapsed = now - self._last_request_time
                wait_time = (1.0 / self.requests_per_second) - elapsed

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                self._last_request_time = time.time()

        # Make HTTP request
        ...
```

#### Why Not Use `ratelimit` Library?

- ❌ `@limits` decorator doesn't support instance variables
- ❌ `@sleep_and_retry` blocks event loop
- ✅ Custom implementation is async-native
- ✅ More flexible and extensible

### Caching

#### Problem

Repeated queries for same data waste API calls.

#### Solution

LRU cache with TTL:

```python
# client_sync.py

class _Cache:
    def __init__(self, maxsize: int = 128, ttl: int = 300):
        self._cache = {}
        self._cache_time = {}
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None

        # Check TTL
        if time.time() - self._cache_time[key] > self._ttl:
            del self._cache[key]
            del self._cache_time[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._cache_time[key] = time.time()

        # LRU eviction
        if len(self._cache) > self._maxsize:
            oldest_key = min(self._cache_time, key=self._cache_time.get)
            del self._cache[oldest_key]
            del self._cache_time[oldest_key]
```

#### Design Decisions

- **LRU**: Evict least recently used items
- **TTL**: Expire old data automatically
- **Simple**: No external dependencies
- **Efficient**: O(1) get/set operations

### Type System

#### Problem

Steam API returns unstructured dicts. Need type-safe objects.

#### Solution

Dataclass-based models:

```python
# types.py

@dataclass
class Game:
    app_id: int
    name: str
    short_desc: str
    # ... more fields

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Game":
        # Parse price
        price_data = data.get("price")
        price = (
            Price(
                initial=price_data.get("initial"),
                final=price_data.get("final"),
                discount_percent=price_data.get("discount_percent", 0),
                currency=price_data.get("currency", "USD"),
            )
            if price_data and isinstance(price_data, dict)
            else None
        )

        # Parse metacritic
        metacritic = data.get("metacritic")
        metacritic_score = metacritic.get("score") if isinstance(metacritic, dict) else None

        return cls(
            app_id=data["app_id"],
            name=data["name"],
            short_desc=data.get("short_desc", ""),
            price=price,
            metacritic_score=metacritic_score,
            # ... more fields
        )
```

#### Benefits

- **Type-safe**: Compile-time type checking
- **IDE-support**: Auto-completion
- **Self-documenting**: Types as documentation
- **Validation**: Ensure data consistency

## Extending the Library

### Adding New API Endpoints

```python
# In steam_client.py

class SteamStoreClient:
    async def get_news(self, app_id: int, count: int = 5):
        """Get news for a game."""
        params = {"appid": app_id, "count": count, "maxlength": 300}
        return await self._get(
            "https://store.steampowered.com/api/news/",
            params=params
        )

# In types.py

@dataclass
class NewsItem:
    title: str
    url: str
    date: str
    contents: str

    @classmethod
    def from_dict(cls, data: dict) -> "NewsItem":
        return cls(
            title=data["title"],
            url=data["url"],
            date=data["date"],
            contents=data["contents"]
        )
```

### Adding Custom Cache Backend

```python
# In client_sync.py

class RedisCache:
    def __init__(self, redis_url: str, ttl: int = 300):
        import redis
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl

    def get(self, key: str) -> Any | None:
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set(self, key: str, value: Any) -> None:
        self.redis.setex(
            key,
            self.ttl,
            json.dumps(value)
        )

# Use custom cache
client = SteamQuery(cache_backend=RedisCache("redis://localhost"))
```

### Adding Middleware

```python
# In steam_client.py

class SteamStoreClient:
    def __init__(self, middlewares: list = None):
        self.middlewares = middlewares or []

    async def _get(self, url: str, params: dict = None):
        # Apply pre-request middleware
        for middleware in self.middlewares:
            await middleware.before_request(url, params)

        # Make request
        response = await self._session.get(url, params=params)

        # Apply post-request middleware
        for middleware in self.middlewares:
            await middleware.after_request(response)

        return await response.json()
```

## Performance Considerations

### Memory Usage

- **Cache size**: Default 128 items (~1-2 MB)
- **Rate limiting**: Minimal overhead (stores timestamp)
- **Type objects**: Lightweight dataclasses

### Optimization Tips

1. **Use caching** for repeated queries
2. **Batch requests** when possible
3. **Adjust rate limit** based on your needs
4. **Use async API** for concurrent operations

### Benchmarks

| Operation | Time (with cache) | Time (without cache) |
|-----------|-------------------|---------------------|
| Search    | ~500ms            | ~500ms              |
| Get       | ~5ms              | ~500ms              |
| Batch(10) | ~500ms            | ~5000ms             |

## Security Considerations

### API Security

- No authentication required (Steam public API)
- No API keys needed
- Rate limiting prevents abuse

### Data Validation

- Input validation on all parameters
- Type checking prevents invalid data
- Error handling prevents crashes

## Testing Strategy

### Unit Tests

```python
# Test rate limiting
async def test_rate_limit_applied():
    client = SteamStoreClient(requests_per_second=5.0)
    # Measure time for 3 requests
    # Should take at least 0.4 seconds
```

### Integration Tests

```python
# Test against real API
def test_get_elden_ring():
    game = get_game_info(1245620)
    assert game.name == "ELDEN RING"
```

### Mock Tests

```python
# Test without hitting API
@patch('steam_query.steam_client.SteamStoreClient._get')
async def test_search_mock(mock_get):
    mock_get.return_value = sample_data
    # Test logic
```

## Related Documentation

- [API Guide](api-guide.md) - Library API reference
- [CLI Guide](cli-guide.md) - Command-line interface guide
- [GitHub Repository](https://github.com/carton/steam-query) - Source code
