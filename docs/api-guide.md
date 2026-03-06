# Steam Query API Guide

Complete reference for using the Steam Query library in your Python projects.

## Table of Contents

- [Overview](#overview)
- [API Styles](#api-styles)
  - [Functional API](#functional-api)
  - [Object API](#object-api)
- [Type System](#type-system)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
  - [Caching](#caching)
  - [Rate Limiting](#rate-limiting)
  - [Async API](#async-api)
- [Examples](#examples)
- [Best Practices](#best-practices)

## Overview

Steam Query provides two styles of APIs:

1. **Functional API** - Simple functions for basic use cases
2. **Object API** - Client-based for advanced features (caching, rate limiting)

Choose based on your needs:

| Feature | Functional API | Object API |
|---------|----------------|------------|
| **Simplicity** | ✅ Simple | 📝 More setup |
| **Caching** | ❌ No | ✅ Built-in LRU cache |
| **Rate Limiting** | ✅ Per call | ✅ Global setting |
| **Batch Operations** | ✅ Yes | ✅ Yes |
| **Stateful** | ❌ No | ✅ Yes |
| **Use Case** | Scripts, simple queries | Applications, repeated queries |

## API Styles

### Functional API

Simple functions that handle async operations automatically. Best for scripts and simple use cases.

#### Import

```python
from steam_query import search_games, get_game_info, get_games_info
```

#### search_games()

Search games by name.

```python
results = search_games(
    query="Elden Ring",
    limit=10,
    country_code="US",
    language="english",
    requests_per_second=1.0
)
```

**Parameters:**
- `query` (str): Search keyword
- `limit` (int): Max results (default: 10)
- `country_code` (str | None): Country code for pricing (e.g., "US", "CN", "KR")
- `language` (str): Language for results (default: "english")
- `requests_per_second` (float): Rate limit (default: 1.0)

**Returns:** `list[SearchResult]`

#### get_game_info()

Get details for a single game.

```python
game = get_game_info(
    app_id=1245620,
    country_code="US",
    language="english",
    requests_per_second=1.0
)
```

**Parameters:**
- `app_id` (int): Steam App ID
- `country_code` (str | None): Country code
- `language` (str): Language (default: "english")
- `requests_per_second` (float): Rate limit (default: 1.0)

**Returns:** `Game | None`

#### get_games_info()

Get details for multiple games.

```python
games = get_games_info(
    app_ids=[1245620, 1091500, 1593500],
    country_code="US",
    language="english",
    requests_per_second=1.0
)
```

**Parameters:**
- `app_ids` (list[int]): List of App IDs
- `country_code` (str | None): Country code
- `language` (str): Language (default: "english")
- `requests_per_second` (float): Rate limit (default: 1.0)

**Returns:** `dict[int, Game]` (only successful queries)

### Object API

Client-based API with caching and rate limiting. Best for applications and repeated queries.

#### Import

```python
from steam_query import SteamQuery
```

#### Initialization

```python
client = SteamQuery(
    country_code="US",
    language="english",
    cache_size=128,
    cache_ttl=300,
    requests_per_second=1.0
)
```

**Parameters:**
- `country_code` (str | None): Country code (default: from env/config)
- `language` (str): Language (default: "english")
- `cache_size` (int): Max cached items (default: 128)
- `cache_ttl` (int): Cache TTL in seconds (default: 300)
- `requests_per_second` (float): Rate limit (default: 1.0)

#### search()

Search games by name.

```python
results: list[SearchResult] = client.search(
    query="Elden Ring",
    limit=10
)
```

**Returns:** `list[SearchResult]`

#### get()

Get game details by App ID.

```python
game: Game = client.get(app_id=1245620)
```

**Returns:** `Game`

**Raises:** `GameNotFoundError` if game not found

#### get_batch()

Get multiple games at once.

```python
games: dict[int, Game] = client.get_batch(
    app_ids=[1245620, 1091500, 1593500]
)
```

**Returns:** `dict[int, Game]` (only successful queries)

#### find()

Search and return first match.

```python
game: Game | None = client.find(query="Hades")
```

**Returns:** `Game | None`

## Type System

Complete type hints for better IDE support and type checking.

### Game

Main game information type.

```python
from steam_query import Game

game: Game = get_game_info(1245620)

# Access properties
print(game.app_id)           # int
print(game.name)             # str
print(game.short_desc)       # str
print(game.release_date)     # str | None
print(game.developers)       # list[str]
print(game.publishers)       # list[str]
print(game.genres)           # list[str]
print(game.tags)             # list[str]
print(game.metacritic_score) # int | None
print(game.is_free)          # bool
print(game.platforms)        # list[str]
print(game.price)            # Price | None
print(game.header_image)     # str
print(game.website)          # str | None
```

### SearchResult

Search result type (simplified Game info).

```python
from steam_query import SearchResult

result: SearchResult = search_games("test")[0]

# Access properties
print(result.app_id)
print(result.name)
print(result.short_desc)
print(result.price)
```

### Price

Price information type.

```python
from steam_query import Price

price: Price = game.price

# Access properties
print(price.initial)          # float (in currency units)
print(price.final)            # float (in currency units)
print(price.discount_percent) # int
print(price.currency)         # str (e.g., "USD", "CNY")
print(price.is_free)          # bool
print(price.is_discounted)    # bool
```

**Note:** For currencies like JPY and KRW, prices are integers (no decimals). For USD, EUR, etc., prices have 2 decimals.

## Error Handling

### Exception Hierarchy

```
SteamQueryError
├── NetworkError          # Network connectivity issues
├── APIError              # API response errors
│   └── RateLimitError    # Rate limiting issues
├── InvalidResponseError  # Invalid API response
├── ConfigurationError    # Configuration issues
└── GameNotFoundError     # Game not found (with app_id)
```

### Handling Errors

```python
from steam_query import SteamQuery
from steam_query.exceptions import (
    GameNotFoundError,
    NetworkError,
    APIError,
    InvalidResponseError
)

client = SteamQuery()

try:
    game = client.get(999999999)
except GameNotFoundError as e:
    print(f"Game not found: {e.app_id}")
except NetworkError as e:
    print(f"Network error: {e}")
except APIError as e:
    print(f"API error: {e}")
except InvalidResponseError as e:
    print(f"Invalid response: {e}")
```

### Error Handling in Functional API

```python
from steam_query import get_game_info
from steam_query.exceptions import GameNotFoundError

game = get_game_info(999999999)
if game is None:
    print("Game not found")
```

## Advanced Usage

### Caching

The `SteamQuery` client includes built-in LRU cache with TTL.

#### How It Works

```python
from steam_query import SteamQuery

client = SteamQuery(
    cache_size=256,    # Cache up to 256 items
    cache_ttl=600      # Cache for 10 minutes
)

# First call - hits API
game1 = client.get(1245620)

# Second call - hits cache (much faster!)
game2 = client.get(1245620)
```

#### Cache Key Format

Cache keys include:
- Query type (search/get)
- Parameters (query, limit, app_id)
- Country code
- Language

Example:
```
search:Elden Ring:10:US:english
get:1245620:US:english
```

#### Disable Caching

```python
# Set cache_size to 0 to disable
client = SteamQuery(cache_size=0)
```

### Rate Limiting

Control API request rate to respect Steam's recommendations.

#### Set Rate Limit

```python
from steam_query import SteamQuery

# Allow 2 requests per second
client = SteamQuery(requests_per_second=2.0)

# Make multiple requests
for app_id in [1245620, 1091500, 1593500]:
    game = client.get(app_id)
    # Requests are automatically rate-limited
```

#### Functional API Rate Limiting

```python
from steam_query import search_games

# Set rate limit for this call
results = search_games("test", requests_per_second=2.0)
```

#### Implementation

Rate limiting uses:
- `asyncio.Lock` for thread safety
- `asyncio.sleep()` for non-blocking delays
- Dynamic rate based on `requests_per_second`

### Async API

For advanced async/await use cases.

#### Using SteamStoreClient Directly

```python
import asyncio
from steam_query.steam_client import SteamStoreClient

async def main():
    async with SteamStoreClient(
        country_code="US",
        requests_per_second=2.0
    ) as client:
        # Search games
        results = await client.search_games_by_name("Elden Ring", limit=10)

        # Get details
        game = await client.get_app_details(1245620)

        # Batch query
        games = await client.get_games_details_batch([1245620, 1091500])

asyncio.run(main())
```

**When to use async API:**
- Building async applications
- Need concurrent requests
- Working with async frameworks (FastAPI, etc.)

## Examples

### Example 1: Game Price Monitor

Monitor game prices across regions.

```python
from steam_query import get_game_info

def check_prices(app_id: int):
    countries = ["US", "JP", "CN", "KR"]

    for country in countries:
        game = get_game_info(app_id, country_code=country)
        if game and game.price:
            print(f"{country}: {game.price.final} {game.price.currency}")

check_prices(1245620)
```

### Example 2: Search and Filter

Search games with custom filtering.

```python
from steam_query import search_games

def find_cheap_games(max_price: float):
    results = search_games("action", limit=50)

    cheap_games = []
    for game in results:
        if game.price and game.price.final <= max_price:
            cheap_games.append({
                "name": game.name,
                "price": game.price.final,
                "currency": game.price.currency
            })

    return cheap_games

games = find_cheap_games(30.0)
for game in games:
    print(f"{game['name']}: ${game['price']}")
```

### Example 3: Batch Processing with Client

Process multiple games efficiently with caching.

```python
from steam_query import SteamQuery

def process_game_library(app_ids: list[int]):
    client = SteamQuery(
        cache_size=512,
        cache_ttl=600,
        requests_per_second=2.0
    )

    # Batch query
    games = client.get_batch(app_ids)

    # Process results
    for app_id, game in games.items():
        print(f"{app_id}: {game.name}")
        if game.metacritic_score:
            print(f"  Metacritic: {game.metacritic_score}/100")

process_game_library([1245620, 1091500, 1593500])
```

### Example 4: Build Game Database

Create a local database of games.

```python
import json
from steam_query import SteamQuery

def build_database(game_names: list[str], output_file: str):
    client = SteamQuery()

    database = []
    for name in game_names:
        results = client.search(name, limit=1)
        if results:
            game = client.get(results[0].app_id)
            database.append({
                "app_id": game.app_id,
                "name": game.name,
                "release_date": game.release_date,
                "genres": game.genres,
                "price": {
                    "final": game.price.final,
                    "currency": game.price.currency
                } if game.price else None
            })

    with open(output_file, 'w') as f:
        json.dump(database, f, indent=2)

build_database(
    ["Elden Ring", "Hollow Knight", "Stardew Valley"],
    "games.json"
)
```

### Example 5: Async Web Scraper

Build async web scraper with Steam Query.

```python
import asyncio
from steam_query.steam_client import SteamStoreClient

async def scrape_multiple_games(app_ids: list[int]):
    async with SteamStoreClient(requests_per_second=2.0) as client:
        tasks = [client.get_app_details(app_id) for app_id in app_ids]
        games = await asyncio.gather(*tasks, return_exceptions=True)

        for i, game in enumerate(games):
            if isinstance(game, Exception):
                print(f"Error fetching {app_ids[i]}: {game}")
            elif game:
                print(f"{game['name']}: {game.get('metacritic_score', 'N/A')}")

asyncio.run(scrape_multiple_games([1245620, 1091500, 1593500]))
```

## Best Practices

### 1. Choose the Right API Style

```python
# ✅ Good: Functional API for simple scripts
from steam_query import get_game_info
game = get_game_info(1245620)

# ✅ Good: Object API for applications
from steam_query import SteamQuery
client = SteamQuery()
game = client.get(1245620)
```

### 2. Handle Errors Properly

```python
# ✅ Good: Explicit error handling
from steam_query import SteamQuery
from steam_query.exceptions import GameNotFoundError

client = SteamQuery()
try:
    game = client.get(app_id)
except GameNotFoundError:
    print(f"Game {app_id} not found")
```

### 3. Use Type Hints

```python
# ✅ Good: With type hints
from steam_query import SteamQuery, Game, SearchResult

def get_game_info_strict(app_id: int) -> Game | None:
    client: SteamQuery = SteamQuery()
    try:
        return client.get(app_id)
    except GameNotFoundError:
        return None
```

### 4. Configure Rate Limiting

```python
# ✅ Good: Respectful rate limiting
client = SteamQuery(requests_per_second=1.0)  # Default
client = SteamQuery(requests_per_second=2.0)  # Moderate
# Avoid: requests_per_second=10.0 (too aggressive)
```

### 5. Leverage Caching

```python
# ✅ Good: Use caching for repeated queries
client = SteamQuery(
    cache_size=256,
    cache_ttl=600
)

# First query - slow
game1 = client.get(1245620)

# Second query - fast (from cache)
game2 = client.get(1245620)
```

### 6. Check for None

```python
# ✅ Good: Check for None
from steam_query import get_game_info

game = get_game_info(app_id)
if game is None:
    print("Game not found")
else:
    print(f"Found: {game.name}")

# ✅ Good: Use exception handling
from steam_query import SteamQuery
from steam_query.exceptions import GameNotFoundError

client = SteamQuery()
try:
    game = client.get(app_id)
    print(f"Found: {game.name}")
except GameNotFoundError:
    print("Game not found")
```

## Related Documentation

- [CLI Guide](cli-guide.md) - Command-line interface documentation
- [Architecture](architecture.md) - Design and implementation details
- [GitHub Repository](https://github.com/carton/steam-query) - Source code
