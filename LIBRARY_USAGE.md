# Using steam-query as a Python Library

The `steam-query` library provides both **simple functions** for quick usage and an **async client** for advanced usage.

## 🚀 Quick Start

### Installation

```bash
pip install steam-game-query
```

### Basic Usage

```python
from steam_query import search_games, get_game_info

# Search for games
results = search_games("Elden Ring", limit=3)
for game in results:
    print(f"{game.name} - ${game.price.final if game.price else 'Free'}")

# Get detailed game information
game = get_game_info(1245620)
if game:
    print(f"{game.name}")
    print(f"Genres: {', '.join(game.genres)}")
    print(f"Metacritic: {game.metacritic_score}/100")
```

## 📚 API Reference

### High-Level Functions (Recommended)

These functions automatically handle async operations and client lifecycle:

#### `search_games(query, limit=10, country_code=None, language='english')`

Search for Steam games by name.

**Parameters:**
- `query` (str): Search keyword
- `limit` (int): Maximum number of results (default: 10)
- `country_code` (str | None): Country code for pricing (e.g., "US", "JP", "KR")
- `language` (str): Language for results (default: "english")

**Returns:** `list[SearchResult]`

**Example:**
```python
from steam_query import search_games

results = search_games("Hollow Knight", limit=5, country_code="JP")
for game in results:
    print(f"{game.name}: {game.short_desc}")
```

#### `get_game_info(app_id, country_code=None, language='english')`

Get detailed information for a specific game.

**Parameters:**
- `app_id` (int): Steam App ID
- `country_code` (str | None): Country code for pricing
- `language` (str): Language for results

**Returns:** `Game | None`

**Example:**
```python
from steam_query import get_game_info

game = get_game_info(1245620)  # Elden Ring
if game:
    print(f"Developers: {game.developers}")
    print(f"Release Date: {game.release_date}")
    print(f"Platforms: {', '.join(game.platforms)}")
```

#### `get_games_info(app_ids, country_code=None, language='english')`

Get detailed information for multiple games.

**Parameters:**
- `app_ids` (list[int]): List of Steam App IDs
- `country_code` (str | None): Country code for pricing
- `language` (str): Language for results

**Returns:** `dict[int, Game]`

**Example:**
```python
from steam_query import get_games_info

games = get_games_info([1245620, 1091500, 413150])
for app_id, game in games.items():
    print(f"{app_id}: {game.name}")
```

### Data Models

The library uses typed dataclasses for type-safe access:

#### `SearchResult`

Simplified game information from search results.

**Fields:**
- `app_id` (int): Steam App ID
- `name` (str): Game title
- `short_desc` (str): Short description
- `price` (Price | None): Price information
- `platforms` (list[str]): Supported platforms
- `metacritic_score` (int | None): Metacritic score
- `review_score` (int | None): Steam review score

#### `Game`

Complete game information.

**Fields:**
- `app_id` (int): Steam App ID
- `name` (str): Game title
- `short_desc` (str): Short description
- `long_desc` (str): Detailed description
- `release_date` (str | None): ISO format release date
- `developers` (list[str]): Developer names
- `publishers` (list[str]): Publisher names
- `genres` (list[str]): Genre names
- `tags` (list[str]): User tags
- `metacritic_score` (int | None): Metacritic score (0-100)
- `price` (Price | None): Price information
- `platforms` (list[str]): Supported platforms (Windows, Mac, Linux)
- `is_free` (bool): Whether the game is free
- `header_image` (str): Header image URL
- `screenshots` (list[str]): Screenshot URLs
- `website` (str | None): Official website
- `requirements` (dict): System requirements

#### `Price`

Price information.

**Fields:**
- `initial` (float | None): Original price
- `final` (float | None): Current price
- `discount_percent` (int): Discount percentage (0-100)
- `currency` (str): Currency code (e.g., "USD", "EUR")

**Properties:**
- `is_free` (bool): Check if game is free
- `is_discounted` (bool): Check if game is on discount

#### `SystemRequirements`

System requirements for running the game.

**Fields:**
- `os` (str): Operating system
- `processor` (str): CPU requirement
- `memory` (str): RAM requirement
- `graphics` (str): GPU requirement
- `directx` (str): DirectX version
- `storage` (str): Disk space requirement

### Advanced Async Usage

For more control over the async client lifecycle:

```python
import asyncio
from steam_query import SteamStoreClient

async def search_with_custom_config():
    async with SteamStoreClient(country_code="JP", language="english") as client:
        results = await client.search_games_by_name("Hollow Knight", limit=5)
        for game_dict in results:
            print(f"{game_dict['name']}: {game_dict.get('price')}")

asyncio.run(search_with_custom_config())
```

## 🌍 Region/Currency Configuration

Specify pricing region via parameters or environment variables:

```python
# Method 1: Direct parameter
game = get_game_info(1245620, country_code="JP")

# Method 2: Environment variable
import os
os.environ["STEAM_QUERY_COUNTRY"] = "JP"
game = get_game_info(1245620)

# Method 3: Config file
# Create ~/.steam-query/config.toml:
# [steam-query]
# country = "JP"
```

## 🔄 Backward Compatibility

For existing code using raw dicts:

```python
from steam_query import search_games_dict, get_game_info_dict

# Dict-based API (backward compatible)
results = search_games_dict("Elden Ring")
game = get_game_info_dict(1245620)
```

## 💡 Usage Tips

1. **Prefer typed models** over dicts for better IDE support
2. **Use batch queries** when querying multiple games
3. **Check for None** when using `get_game_info()`
4. **Use price properties** (`is_free`, `is_discounted`) for cleaner code
5. **Specify country code** for accurate pricing

## 📖 Examples

See `examples/library_usage.py` for comprehensive examples.

## 🔗 CLI Usage

For command-line usage, see the main [README.md](README.md).
