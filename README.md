# Steam Query

Query detailed information for any game on the Steam store - no login required, no API key needed!

## Features

- 🔍 **Search Games** - Search the Steam store by game name
- 📋 **Detailed Info** - Get release date, developer, genres, ratings, and more
- 💰 **Price Info** - Display current price and discount information
- 💻 **Platform Support** - Show Windows/Mac/Linux support
- 📊 **Batch Queries** - Query multiple games at once
- 🎯 **Exact Match** - Direct query by App ID
- ⏱️ **Rate Limiting** - Built-in rate limiter, respects API rules
- 📄 **JSON Output** - Export results as JSON

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/carton/steam-query.git
cd steam-query

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install with uv
pip install uv
uv pip install -e .

# Or with pip
pip install -e .
```

### Basic Usage

#### 1. Search Games

```bash
# Search games
steam-query search "Elden Ring"

# Limit results
steam-query search "Hollow Knight" -l 5

# Save search results
steam-query search "Stardew Valley" -o results.json
```

#### 2. Lookup Game Details

```bash
# Lookup by App ID
steam-query lookup 1245620

# Lookup by game name (auto-search)
steam-query lookup -q "Elden Ring"

# Query with specific country pricing
steam-query lookup 1245620 --country US
steam-query lookup 1245620 --country KR
steam-query lookup 1245620 --country JP

# JSON format output
steam-query lookup -q "Hollow Knight" --json

# Save details
steam-query lookup 1245620 -o elden-ring.json
```

#### 3. Batch Queries

```bash
# Query multiple games
steam-query batch "Elden Ring" "Hollow Knight" "Stardew Valley" -o results.json

# From text file (one game name per line)
steam-query batch -i games.txt -o results.json

# With specific country pricing
steam-query batch "Elden Ring" "Hollow Knight" -o results.json --country CN
```

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
   • Steam Deck

💰 Price: 59.99 USD

📝 Description:
   A new action RPG developed by FromSoftware Inc. and BANDAI NAMCO...

🔗 Store Link: https://store.steampowered.com/app/1245620/
```

## Configuration

### Country/Region Settings

Steam prices vary by region. You can specify which country's pricing to use:

**1. Command-line parameter (highest priority):**
```bash
steam-query lookup 1245620 --country US
steam-query search "Elden Ring" --country KR
```

**2. Environment variable:**
```bash
export STEAM_QUERY_COUNTRY=JP
steam-query lookup 1245620
```

**3. Config file:**
```bash
# Create config directory
mkdir -p ~/.steam-query

# Create config file
cat > ~/.steam-query/config.toml << EOF
[steam-query]
country = "US"
EOF
```

**Priority:** CLI parameter > Environment variable > Config file > Default (US)

**Supported country codes:** US, CN, KR, JP, GB, DE, FR, RU, BR, AU, CA, etc.
See [Steam Country Codes](https://partner.steamgames.com/doc/store/localization) for complete list.

### Environment Variables

```bash
# Set default country for pricing
export STEAM_QUERY_COUNTRY=US

# Set log level
export STEAM_QUERY_LOG_LEVEL=DEBUG
```

Default: 1 request/second (follows Steam recommendations)

You can modify in code:
```python
from steam_query import SteamStoreClient

client = SteamStoreClient(requests_per_second=2.0)  # 2 req/sec
```

## Project Structure

```
steam-query/
├── steam_query/
│   ├── __init__.py       # Package initialization
│   ├── steam_client.py   # Steam API client
│   └── cli.py           # Command-line interface
├── pyproject.toml        # Project configuration
└── README.md            # This file
```

## Use Cases

### Use Case 1: Find Game Release Date

```bash
steam-query lookup -q "Hollow Knight" --json | jq '.game.release_date'
```

### Use Case 2: Batch Query Game List

```bash
# Create game list
cat > games.txt << EOF
Elden Ring
Hollow Knight
Stardew Valley
Celeste
EOF

# Batch query
steam-query batch -i games.txt -o results.json
```

## Limitations

1. **Rate Limiting** - Steam Store API has no official rate limit, but 1 request/second is recommended
2. **Search Accuracy** - Uses Steam store search, may not always be exact
3. **Availability** - Depends on Steam store API availability

## API Reference

### SteamStoreClient

```python
from steam_query import SteamStoreClient

# Initialize with country/region settings
async with SteamStoreClient(country_code="US") as client:
    # Search games
    results = await client.search_games_by_name("Elden Ring", limit=10)

    # Get details
    game = await client.get_app_details(1245620)

    # Batch query
    games = await client.get_games_details_batch([1245620, 571860])

# Parameters:
# - requests_per_second: Rate limit (default: 1.0)
# - country_code: Country code for pricing (e.g., "US", "CN", "KR", "JP")
# - language: Language for results (default: "english")
```

### Configuration Priority

When calling `SteamStoreClient(country_code="...")`:

1. **Explicit parameter** - `SteamStoreClient(country_code="JP")`
2. **Environment variable** - `STEAM_QUERY_COUNTRY=US`
3. **Config file** - `~/.steam-query/config.toml`
4. **Default** - `US`

## Contributing

Issues and pull requests are welcome!

## License

MIT License
