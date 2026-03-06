# Steam Query CLI Guide

The Steam Query CLI is a powerful command-line tool for querying Steam store game information without requiring login or API keys.

## Table of Contents

- [Installation](#installation)
- [Core Commands](#core-commands)
  - [search - Search Games](#search---search-games)
  - [lookup - Get Details](#lookup---get-details)
  - [batch - Batch Queries](#batch---batch-queries)
- [Configuration](#configuration)
  - [Country/Region Settings](#countryregion-settings)
  - [Rate Limiting](#rate-limiting)
  - [Logging](#logging)
- [Output Formats](#output-formats)
  - [Default Output](#default-output)
  - [JSON Output](#json-output)
  - [Save to File](#save-to-file)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)

## Installation

```bash
# Install from PyPI
pip install steam-game-query

# Verify installation
steam-query --help
```

## Core Commands

### search - Search Games

Search the Steam store by game name.

#### Basic Usage

```bash
# Search games
steam-query search "Elden Ring"

# Limit results
steam-query search "Hollow Knight" --limit 5

# Specify country/region for pricing
steam-query search "Stardew Valley" --country JP
```

#### Parameters

- `query` (required): Search keyword
- `-l, --limit`: Number of results (default: 10)
- `-c, --country`: Country code for pricing (e.g., US, CN, KR, JP)
- `-o, --output`: Save results to JSON file
- `-r, --rate-limit`: Request rate (requests/second, default: 1.0)
- `-v, --verbose`: Show verbose logs

#### Examples

```bash
# Search and save results
steam-query search "action games" -l 20 -o results.json

# Use faster rate
steam-query search "RPG" --rate-limit 2.0

# Show verbose logs
steam-query search "strategy" -v
```

### lookup - Get Details

Get detailed information for a specific game.

#### Basic Usage

```bash
# Query by App ID
steam-query lookup 1245620

# Search by name then lookup
steam-query lookup -q "Elden Ring"

# Specify country/region
steam-query lookup 1245620 --country KR
```

#### Parameters

- `app_id`: Steam App ID (mutually exclusive with -q)
- `-q, --query`: Game name (will search first, then lookup)
- `-c, --country`: Country code
- `-j, --json`: Output in JSON format
- `-o, --output`: Save to JSON file
- `-r, --rate-limit`: Request rate
- `-v, --verbose`: Show verbose logs

#### Examples

```bash
# JSON output
steam-query lookup 1245620 --json

# Lookup and save
steam-query lookup -q "Hollow Knight" -o hollow-knight.json

# Query Japan pricing
steam-query lookup 1245620 --country JP --json | jq '.price'
```

### batch - Batch Queries

Query multiple games at once.

#### Basic Usage

```bash
# Specify game list from command line
steam-query batch "Elden Ring" "Hollow Knight" "Stardew Valley" -o results.json

# Read game list from file
steam-query batch -i games.txt -o results.json

# Specify country/region
steam-query batch "Game1" "Game2" --country CN -o results.json
```

#### Parameters

- `queries`: List of game names (mutually exclusive with -i)
- `-i, --input`: Input file path (supports .txt and .json)
- `-o, --output`: Output JSON file (required)
- `-c, --country`: Country code
- `-r, --rate-limit`: Request rate
- `-v, --verbose`: Show verbose logs

#### Input File Formats

**Text file (.txt)**:
```
Elden Ring
Hollow Knight
Stardew Valley
Celeste
```

**JSON file**:
```json
[
  {"metadata": {"title": "Elden Ring"}},
  {"metadata": {"title": "Hollow Knight"}},
  {"metadata": {"title": "Stardew Valley"}}
]
```

#### Output Format

```json
{
  "timestamp": "2026-03-06T15:30:00",
  "total": 3,
  "found": 2,
  "results": [
    {
      "app_id": 1245620,
      "name": "ELDEN RING"
    }
  ]
}
```

## Configuration

### Country/Region Settings

Steam game prices vary by region. Set your preferred country/region with the following priority:

#### 1. CLI Parameter (Highest Priority)

```bash
steam-query lookup 1245620 --country US
```

#### 2. Environment Variable

```bash
# Linux/Mac
export STEAM_QUERY_COUNTRY=JP

# Windows
set STEAM_QUERY_COUNTRY=JP
```

#### 3. Config File

```bash
# Create config directory
mkdir -p ~/.steam-query

# Create config file
cat > ~/.steam-query/config.toml << EOF
[steam-query]
country = "US"
EOF
```

#### Priority

CLI parameter > Environment variable > Config file > Default (US)

#### Supported Country Codes

Common codes: US, CN, KR, JP, GB, DE, FR, RU, BR, AU, CA, IN, BR, MX, AR, CL, CO, PE, TR, SA, AE, TH, ID, MY, PH, SG, VN, UA, PL, NL, SE, NO, DK, FI, IT, ES, PT, GR, CZ, HU, RO, BG, AT, CH, IE, NZ, IL, ZA

Complete list: [Steam Country Codes](https://partner.steamgames.com/doc/store/localization)

### Rate Limiting

Default rate: 1 request/second (follows Steam recommendations)

#### Adjust Rate Limit

```bash
# Set to 2 requests/second
steam-query search "test" --rate-limit 2.0

# Set to 0.5 requests/second (more conservative)
steam-query search "test" --rate-limit 0.5
```

**Note**: Too high rates may cause Steam to throttle your requests. Keep at default or moderately increase (max 2-3 req/s).

### Logging

```bash
# Show verbose logs
steam-query search "test" --verbose

# Set via environment variable
export STEAM_QUERY_LOG_LEVEL=DEBUG
```

## Output Formats

### Default Output

Beautiful terminal output with emoji icons:

```
🎮 ============================================================
  Elden Ring
🎮 ============================================================

📋 Basic Info:
   App ID:      1245620
   Release Date: 2022-02-25
   Developer:  FromSoftware Inc.
   Metascore:  🟢 96/100

💰 Price: 59.99 USD
```

### JSON Output

Structured JSON format for programmatic processing:

```bash
steam-query lookup 1245620 --json
```

Output:
```json
{
  "app_id": 1245620,
  "name": "ELDEN RING",
  "short_desc": "...",
  "release_date": "2022-02-25",
  "developers": ["FromSoftware Inc."],
  "genres": ["Action RPG", "Adventure"],
  "metacritic_score": 96,
  "price": {
    "initial": 5999,
    "final": 5999,
    "discount_percent": 0,
    "currency": "USD"
  },
  "platforms": ["Windows"]
}
```

### Save to File

```bash
# Save JSON format
steam-query search "test" -o results.json

# Extract specific info with jq
steam-query lookup 1245620 --json | jq '.price.final'
```

## Use Cases

### Use Case 1: Compare Regional Pricing

```bash
# Query US price
steam-query lookup 1245620 --country US --json | jq '.price.final'

# Query Japan price
steam-query lookup 1245620 --country JP --json | jq '.price.final'

# Query China price
steam-query lookup 1245620 --country CN --json | jq '.price.final'
```

### Use Case 2: Monitor Price Changes

```bash
# Save current price
steam-query lookup 1245620 --country US --json > price_$(date +%Y%m%d).json

# Compare later
diff price_20260301.json price_20260306.json
```

### Use Case 3: Batch Export Game Library

```bash
# Create game list
cat > my_games.txt << EOF
Elden Ring
Hollow Knight
Stardew Valley
Celeste
Hades
EOF

# Batch query
steam-query batch -i my_games.txt -o my_library.json
```

### Use Case 4: Find Discounted Games

```bash
# Search and filter discounted games
steam-query search "action" -l 50 -o results.json

# Find games with discounts using jq
jq '.results[] | select(.price.discount_percent > 0) | {name: .name, discount: .price.discount_percent}' results.json
```

### Use Case 5: Build Game Database

```bash
# Import from Epic Games export format
cat > epic_games.json << EOF
[
  {"metadata": {"title": "Elden Ring"}},
  {"metadata": {"title": "Hollow Knight"}}
]
EOF

# Query Steam info
steam-query batch -i epic_games.json -o steam_equivalent.json
```

## Troubleshooting

### Issue 1: Game Not Found

**Symptom**:
```
❌ No matching games found: XXX
```

**Solution**:
- Check game name spelling
- Try partial keywords
- Confirm game exists on Steam store

### Issue 2: Network Error

**Symptom**:
```
NetworkError: Failed to connect to Steam API
```

**Solution**:
- Check network connection
- Steam API might be temporarily unavailable
- Try reducing request rate: `--rate-limit 0.5`

### Issue 3: Rate Limiting

**Symptom**:
- Requests being rejected or timing out

**Solution**:
- Lower request rate: `--rate-limit 0.5`
- Avoid running multiple CLI instances concurrently
- Use more conservative rate for batch queries

### Issue 4: Configuration Not Working

**Symptom**:
- Config file settings not taking effect

**Solution**:
```bash
# Check config file path
ls -la ~/.steam-query/config.toml

# Check config file format
cat ~/.steam-query/config.toml

# Verify environment variable
echo $STEAM_QUERY_COUNTRY
```

### Issue 5: JSON Output Issues

**Symptom**:
- JSON parsing fails

**Solution**:
```bash
# Pretty-print with jq
steam-query lookup 1245620 --json | jq '.'

# Validate JSON format
steam-query lookup 1245620 --json | jq 'empty'
```

## Best Practices

1. **Use Scripts for Batch Tasks**
   ```bash
   # Batch query script
   for game in "Elden Ring" "Hollow Knight" "Stardew Valley"; do
     steam-query lookup -q "$game" --json
   done
   ```

2. **Combine with Other Tools**
   ```bash
   # Use with jq
   steam-query search "RPG" -l 50 -o results.json
   jq '.results[] | select(.price.final < 30)' results.json
   ```

3. **Log Queries**
   ```bash
   # Save query logs
   steam-query search "test" -v 2>&1 | tee query.log
   ```

4. **Error Handling in Scripts**
   ```bash
   # Use in scripts
   if ! steam-query lookup 1245620; then
     echo "Query failed"
     exit 1
   fi
   ```

## More Help

```bash
# Show help
steam-query --help

# Show subcommand help
steam-query search --help
steam-query lookup --help
steam-query batch --help

# Check version
pip show steam-game-query
```

## Related Documentation

- [API Guide](api-guide.md) - Library API usage guide
- [Architecture](architecture.md) - Architecture design documentation
- [GitHub Issues](https://github.com/carton/steam-query/issues) - Issue tracker
