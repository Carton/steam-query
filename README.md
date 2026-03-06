# Steam Query

Query detailed information for any game on the Steam store - no login required, no API key needed!

## Features

- 🔍 **Search Games** - Search the Steam store by game name
- 📋 **Detailed Info** - Get release date, developer, genres, ratings, and more
- 💰 **Price Info** - Display current price and discount information
- 💻 **Platform Support** - Show Windows/Mac/Linux support
- 📊 **Batch Queries** - Query multiple games at once
- ⏱️ **Rate Limiting** - Built-in rate limiter, respects API rules
- 💾 **Smart Cache** - LRU cache with TTL for better performance
- 🎯 **Type Safe** - Complete type hints for better IDE support

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install steam-game-query

# Or with uv
uv pip install steam-game-query
```

### CLI Usage

```bash
# Search games
steam-query search "Elden Ring"

# Lookup by App ID
steam-query lookup 1245620

# Batch query multiple games
steam-query batch "Elden Ring" "Hollow Knight" -o results.json
```

### Library Usage

#### Functional API (Simple)

```python
from steam_query import search_games, get_game_info

# Search games
results = search_games("Elden Ring", limit=5)
for game in results:
    print(f"{game.name}: {game.price}")

# Get game details
game = get_game_info(1245620)
if game:
    print(f"{game.name} - {game.genres}")
```

#### Object API (Advanced)

```python
from steam_query import SteamQuery

# Create client with custom settings
client = SteamQuery(
    country_code="US",
    cache_size=256,
    requests_per_second=2.0
)

# Use client methods
game = client.get(1245620)
results = client.search("Hollow Knight", limit=10)
games = client.get_batch([1245620, 1091500, 1593500])
```

## 📖 Documentation

For detailed usage guides and API reference, see:

- **[CLI Guide](docs/cli-guide.md)** - Complete command-line interface documentation
- **[API Guide](docs/api-guide.md)** - Full library API reference and examples
- **[Architecture](docs/architecture.md)** - Design and implementation details

## Output Example

```
🎮 ============================================================
  Elden Ring
🎮 ============================================================

📋 Basic Info:
   App ID:      1245620
   Release Date: 2022-02-25
   Free:        No
   Developer:  FromSoftware Inc.
   Publisher:  BANDAI NAMCO Entertainment Inc.
   Genres:     Action RPG, Adventure
   Metascore:  🟢 96/100

💻 Supported Platforms:
   • Windows

💰 Price: 59.99 USD

🔗 Store Link: https://store.steampowered.com/app/1245620/
```

## Configuration

### Country/Region Settings

Control pricing region with multiple options:

```bash
# CLI parameter
steam-query lookup 1245620 --country US

# Environment variable
export STEAM_QUERY_COUNTRY=JP

# Config file
mkdir -p ~/.steam-query
echo '[steam-query]' > ~/.steam-query/config.toml
echo 'country = "US"' >> ~/.steam-query/config.toml
```

**Priority**: CLI parameter > Environment variable > Config file > Default (US)

Supported countries: US, CN, KR, JP, GB, DE, FR, RU, BR, AU, CA, etc.

### Rate Limiting

Default: 1 request/second (recommended by Steam)

```python
from steam_query import SteamQuery

# Custom rate limit
client = SteamQuery(requests_per_second=2.0)
```

## Error Handling

```python
from steam_query import SteamQuery
from steam_query.exceptions import GameNotFoundError, NetworkError, APIError

client = SteamQuery()

try:
    game = client.get(999999999)
except GameNotFoundError as e:
    print(f"Game not found: {e.app_id}")
except NetworkError as e:
    print(f"Network error: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## Quick Examples

### Example 1: Check Game Price

```python
from steam_query import get_game_info

game = get_game_info(1245620)
if game and game.price:
    print(f"{game.name}: {game.price.final} {game.price.currency}")
```

### Example 2: Search and Filter

```python
from steam_query import search_games

results = search_games("action", limit=20)
for game in results:
    if game.price and game.price.final < 30:
        print(f"{game.name}: ${game.price.final}")
```

### Example 3: Batch Processing

```python
from steam_query import SteamQuery

client = SteamQuery()

app_ids = [1245620, 1091500, 1593500]
games = client.get_batch(app_ids)

for app_id, game in games.items():
    print(f"{app_id}: {game.name}")
```

## Type Hints

```python
from steam_query import SteamQuery, Game, SearchResult

client: SteamQuery = SteamQuery()
results: list[SearchResult] = client.search("Elden Ring")
game: Game = client.get(1245620)
```

## Project Links

- **PyPI**: https://pypi.org/project/steam-game-query/
- **GitHub**: https://github.com/carton/steam-query
- **Issues**: https://github.com/carton/steam-query/issues

## License

MIT License - see LICENSE file for details
