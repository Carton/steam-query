"""Steam Query CLI - Command-line tool

Query detailed information for any game on the Steam store
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime

import colorlog

from .steam_client import SteamStoreClient
from .types import Game

# Setup logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup colored logging"""
    log_level = logging.DEBUG if verbose else logging.INFO

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    logging.root.setLevel(log_level)
    logging.root.addHandler(handler)


def format_game_info(game: Game) -> str:
    """Format game information for display

    Args:
        game: Game information object

    Returns:
        Formatted string
    """
    lines = [
        "",
        "🎮 " + "=" * 60,
        f"  {game.name}",
        "🎮 " + "=" * 60,
    ]

    # Basic information
    lines.append("\n📋 Basic Info:")
    lines.append(f"   App ID:      {game.app_id}")
    lines.append(f"   Release Date: {game.release_date or 'N/A'}")
    lines.append(f"   Free:        {'Yes' if game.is_free else 'No'}")

    if game.developers:
        lines.append(f"   Developer:  {', '.join(game.developers)}")
    if game.publishers:
        lines.append(f"   Publisher:  {', '.join(game.publishers)}")

    if game.genres:
        lines.append(f"   Genres:     {', '.join(game.genres)}")

    if game.metacritic_score:
        score = game.metacritic_score
        emoji = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        lines.append(f"   Metascore:  {emoji} {score}/100")

    # Platforms
    if game.platforms:
        lines.append("\n💻 Supported Platforms:")
        for platform in game.platforms:
            lines.append(f"   • {platform}")

    # Price - use Price model properties
    if game.price:
        price = game.price
        if price.is_free:
            lines.append("\n💰 Price: Free")
        elif price.is_discounted:
            # Price has discount
            if price.currency in {"JPY", "KRW"}:
                lines.append(
                    f"\n💰 Price: {int(price.final)} {price.currency} "
                    f"(was {int(price.initial)} {price.currency}, -{price.discount_percent}%)"
                )
            else:
                lines.append(
                    f"\n💰 Price: {price.final:.2f} {price.currency} "
                    f"(was {price.initial:.2f} {price.currency}, -{price.discount_percent}%)"
                )
        else:
            # Regular price
            if price.currency in {"JPY", "KRW"}:
                lines.append(f"\n💰 Price: {int(price.final)} {price.currency}")
            else:
                lines.append(f"\n💰 Price: {price.final:.2f} {price.currency}")
    elif game.is_free:
        lines.append("\n💰 Price: Free")

    # Short description
    if game.short_desc:
        desc = game.short_desc
        if len(desc) > 100:
            desc = desc[:97] + "..."
        lines.append("\n📝 Description:")
        lines.append(f"   {desc}")

    # Link
    lines.append(f"\n🔗 Store Link: https://store.steampowered.com/app/{game.app_id}/")

    lines.append("")
    return "\n".join(lines)


def format_game_json(game: Game) -> str:
    """Format as JSON string"""
    # Convert Game to dict and remove some redundant fields for display
    game_dict = {
        "app_id": game.app_id,
        "name": game.name,
        "short_desc": game.short_desc,
        "release_date": game.release_date,
        "developers": game.developers,
        "publishers": game.publishers,
        "genres": game.genres,
        "tags": game.tags,
        "metacritic_score": game.metacritic_score,
        "price": {
            "initial": game.price.initial,
            "final": game.price.final,
            "discount_percent": game.price.discount_percent,
            "currency": game.price.currency,
        }
        if game.price
        else None,
        "platforms": game.platforms,
        "is_free": game.is_free,
        "header_image": game.header_image,
        "website": game.website,
    }

    return json.dumps(game_dict, indent=2, ensure_ascii=False)


async def search_command(args):
    """Search games command"""
    async with SteamStoreClient(
        country_code=args.country, requests_per_second=args.rate_limit
    ) as client:
        results_dict = await client.search_games_by_name(args.query, limit=args.limit)

        if not results_dict:
            print(f"❌ No matching games found: {args.query}")
            return 1

        # Convert to SearchResult objects for type-safe access
        from .types import SearchResult

        results = [SearchResult.from_dict(r) for r in results_dict]

        print(f"\n✅ Found {len(results)} result(s):\n")

        for i, game in enumerate(results, 1):
            print(f"{i}. {game.name} (App ID: {game.app_id})")
            if game.short_desc:
                desc = (
                    game.short_desc[:80] + "..."
                    if len(game.short_desc) > 80
                    else game.short_desc
                )
                print(f"   {desc}")
            if game.price:
                price = game.price
                if price.is_free:
                    print("   💰 Free")
                elif price.is_discounted:
                    if price.currency in {"JPY", "KRW"}:
                        print(
                            f"   💰 {int(price.final)} {price.currency} "
                            f"(was {int(price.initial)} {price.currency}, -{price.discount_percent}%)"
                        )
                    else:
                        print(
                            f"   💰 {price.final:.2f} {price.currency} "
                            f"(was {price.initial:.2f} {price.currency}, -{price.discount_percent}%)"
                        )
                else:
                    if price.currency in {"JPY", "KRW"}:
                        print(f"   💰 {int(price.final)} {price.currency}")
                    else:
                        print(f"   💰 {price.final:.2f} {price.currency}")
            else:
                print("   💰 Free or not priced")
            print()

        # Save to file
        if args.output:
            output_data = {
                "query": args.query,
                "timestamp": datetime.now().isoformat(),
                "total": len(results),
                "results": results,
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Results saved to: {args.output}")

        return 0


async def lookup_command(args):
    """Lookup game details command"""
    async with SteamStoreClient(
        country_code=args.country, requests_per_second=args.rate_limit
    ) as client:
        # If it's a search query, search first
        if args.query:
            print(f"🔍 Searching: {args.query}")
            search_results = await client.search_games_by_name(args.query, limit=1)

            if not search_results:
                print(f"❌ Game not found: {args.query}")
                return 1

            app_id = search_results[0]["app_id"]
            print(f"✅ Found: {search_results[0]['name']} (App ID: {app_id})")
        else:
            app_id = args.app_id

        # Get detailed information
        print("⏳ Getting detailed information...")
        game_dict = await client.get_app_details(app_id)

        if not game_dict:
            print(f"❌ Unable to get game details (App ID: {app_id})")
            return 1

        # Convert to Game object for type-safe access
        game = Game.from_dict(game_dict)

        # Display results
        if args.json:
            print(format_game_json(game))
        else:
            print(format_game_info(game))

        # Save to file
        if args.output:
            output_data = {
                "app_id": app_id,
                "timestamp": datetime.now().isoformat(),
                "game": game_dict,  # Save the original dict for JSON compatibility
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Details saved to: {args.output}")

        return 0


async def batch_command(args):
    """Batch query command"""
    # Read input
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            if args.input.endswith(".json"):
                data = json.load(f)
                # Assume Epic games format
                queries = [
                    g.get("metadata", {}).get("title", "")
                    for g in data
                    if g.get("metadata", {}).get("title")
                ]
            else:
                # Text file, one game name per line
                queries = [line.strip() for line in f if line.strip()]
    else:
        queries = args.queries

    if not queries:
        print("❌ No games to query")
        return 1

    print(f"📋 Will query {len(queries)} game(s)\n")

    async with SteamStoreClient(
        country_code=args.country, requests_per_second=args.rate_limit
    ) as client:
        results = []
        found = 0

        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] 🔍 {query}... ", end="", flush=True)

            # Search
            search_results = await client.search_games_by_name(query, limit=1)

            if search_results:
                app_id = search_results[0]["app_id"]
                print(f"✅ (App ID: {app_id})", end="", flush=True)

                # Get details
                game = await client.get_app_details(app_id)
                if game:
                    results.append(game)
                    found += 1
                    print(" ✓")
                else:
                    results.append({"query": query, "error": "Cannot get details"})
                    print(" ⚠️")
            else:
                results.append({"query": query, "error": "Not found"})
                print(" ❌")

        # Show statistics
        print("\n📊 Statistics:")
        print(f"   Total: {len(queries)}")
        print(f"   Found: {found}")
        print(f"   Not Found: {len(queries) - found}")

        # Save results
        if args.output:
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "total": len(queries),
                "found": found,
                "results": results,
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Results saved to: {args.output}")

        return 0


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        prog="steam-query",
        description="Query detailed information for any game on the Steam store",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search games
  steam-query search "Elden Ring"

  # Lookup game details (by App ID)
  steam-query lookup 1245620

  # Lookup game details (by name search)
  steam-query lookup -q "Hollow Knight"

  # Query with specific country/region pricing
  steam-query lookup 1245620 --country US
  steam-query search "Elden Ring" --country CN

  # Batch query
  steam-query batch "Elden Ring" "Hollow Knight" "Stardew Valley"

  # Query with custom rate limit
  steam-query batch -i games.txt -o out.json --rate-limit 0.5

Configuration:
  You can set a default country via:
    - Environment variable: STEAM_QUERY_COUNTRY=US
    - Config file: ~/.steam-query/config.toml
      [steam-query]
      country = "US"

  Supported country codes: US, CN, KR, JP, GB, DE, FR, RU, BR, etc.
  See: https://partner.steamgames.com/doc/store/localization

More info: https://github.com/carton/steam-query
        """,
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose logs"
    )

    parser.add_argument(
        "-r",
        "--rate-limit",
        type=float,
        default=1.0,
        help="Requests per second (default: 1.0)",
    )

    # Common country argument for all subcommands
    country_kwargs = {
        "help": "Country code for pricing (e.g., US, CN, KR, JP, GB). Overrides environment/config.",
        "type": lambda x: x.upper(),
    }

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Search command
    search_parser = subparsers.add_parser(
        "search", help="Search games (returns matching game list)"
    )
    search_parser.add_argument("query", help="Search keyword")
    search_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Number of results (default 10)"
    )
    search_parser.add_argument("-o", "--output", help="Save results to JSON file")
    search_parser.add_argument("-c", "--country", **country_kwargs)  # type: ignore[arg-type]

    # Lookup command
    lookup_parser = subparsers.add_parser(
        "lookup", help="Lookup detailed game information"
    )
    lookup_group = lookup_parser.add_mutually_exclusive_group(required=True)
    lookup_group.add_argument("app_id", nargs="?", type=int, help="Steam App ID")
    lookup_group.add_argument("-q", "--query", help="Game name (will search first)")
    lookup_parser.add_argument(
        "-j", "--json", action="store_true", help="Output in JSON format"
    )
    lookup_parser.add_argument("-o", "--output", help="Save results to JSON file")
    lookup_parser.add_argument("-c", "--country", **country_kwargs)  # type: ignore[arg-type]

    # Batch query command
    batch_parser = subparsers.add_parser("batch", help="Query multiple games in batch")
    batch_input = batch_parser.add_mutually_exclusive_group(required=True)
    batch_input.add_argument("queries", nargs="*", help="List of game names")
    batch_input.add_argument(
        "-i", "--input", help="Input file (JSON or text, one game name per line)"
    )
    batch_parser.add_argument("-o", "--output", required=True, help="Output JSON file")
    batch_parser.add_argument("-c", "--country", **country_kwargs)  # type: ignore[arg-type]

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging
    setup_logging(args.verbose)

    # Execute command
    try:
        if args.command == "search":
            return await search_command(args)
        elif args.command == "lookup":
            return await lookup_command(args)
        elif args.command == "batch":
            return await batch_command(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled")
        return 130
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1


def cli_main():
    """CLI entry point"""
    exit(asyncio.run(main()))


if __name__ == "__main__":
    cli_main()
