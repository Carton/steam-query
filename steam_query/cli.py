"""Steam Query CLI - Command-line tool

Query detailed information for any game on the Steam store
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import colorlog

from .steam_client import SteamStoreClient

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


def format_game_info(game: dict) -> str:
    """Format game information for display

    Args:
        game: Game information dictionary

    Returns:
        Formatted string
    """
    lines = [
        "",
        "🎮 " + "=" * 60,
        f"  {game.get('name', 'Unknown')}",
        "🎮 " + "=" * 60,
    ]

    # Basic information
    lines.append(f"\n📋 Basic Info:")
    lines.append(f"   App ID:      {game.get('app_id', 'N/A')}")
    lines.append(f"   Release Date: {game.get('release_date', 'N/A')}")
    lines.append(f"   Free:        {'Yes' if game.get('is_free') else 'No'}")

    if game.get("developers"):
        lines.append(f"   Developer:  {', '.join(game['developers'])}")
    if game.get("publishers"):
        lines.append(f"   Publisher:  {', '.join(game['publishers'])}")

    if game.get("genres"):
        lines.append(f"   Genres:     {', '.join(game['genres'])}")

    if game.get("metacritic_score"):
        score = game["metacritic_score"]
        emoji = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        lines.append(f"   Metascore:  {emoji} {score}/100")

    # Platforms
    if game.get("platforms"):
        lines.append(f"\n💻 Supported Platforms:")
        for platform in game["platforms"]:
            lines.append(f"   • {platform}")

    # Price
    if game.get("price"):
        price = game["price"]
        if price.get("discount_percent", 0) > 0:
            lines.append(
                f"\n💰 Price: ${price['final']:.2f} (was ${price['initial']:.2f}, -{price['discount_percent']}%)"
            )
        else:
            lines.append(f"\n💰 Price: ${price['final']:.2f}")
    elif game.get("is_free"):
        lines.append(f"\n💰 Price: Free")

    # Short description
    if game.get("short_desc"):
        desc = game["short_desc"]
        if len(desc) > 100:
            desc = desc[:97] + "..."
        lines.append(f"\n📝 Description:")
        lines.append(f"   {desc}")

    # Link
    app_id = game.get("app_id")
    if app_id:
        lines.append(f"\n🔗 Store Link: https://store.steampowered.com/app/{app_id}/")

    lines.append("")
    return "\n".join(lines)


def format_game_json(game: dict) -> str:
    """Format as JSON string"""
    # Remove some redundant fields
    game_copy = game.copy()
    if "long_desc" in game_copy:
        del game_copy["long_desc"]
    if "screenshots" in game_copy:
        del game_copy["screenshots"]

    return json.dumps(game_copy, indent=2, ensure_ascii=False)


async def search_command(args):
    """Search games command"""
    async with SteamStoreClient() as client:
        results = await client.search_games_by_name(args.query, limit=args.limit)

        if not results:
            print(f"❌ No matching games found: {args.query}")
            return 1

        print(f"\n✅ Found {len(results)} result(s):\n")

        for i, game in enumerate(results, 1):
            print(f"{i}. {game['name']} (App ID: {game['app_id']})")
            if game.get("short_desc"):
                desc = game["short_desc"][:80] + "..." if len(game["short_desc"]) > 80 else game["short_desc"]
                print(f"   {desc}")
            if game.get("price"):
                price = game["price"]
                if price.get("discount_percent", 0) > 0:
                    print(f"   💰 ${price['final']:.2f} (was ${price['initial']:.2f}, -{price['discount_percent']}%)")
                elif not price.get("final") == 0:
                    print(f"   💰 ${price['final']:.2f}")
            else:
                print(f"   💰 Free or not priced")
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
    async with SteamStoreClient() as client:
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
        print(f"⏳ Getting detailed information...")
        game = await client.get_app_details(app_id)

        if not game:
            print(f"❌ Unable to get game details (App ID: {app_id})")
            return 1

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
                "game": game,
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Details saved to: {args.output}")

        return 0


async def batch_command(args):
    """Batch query command"""
    # Read input
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
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

    async with SteamStoreClient() as client:
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
                    print(f" ✓")
                else:
                    results.append({"query": query, "error": "Cannot get details"})
                    print(f" ⚠️")
            else:
                results.append({"query": query, "error": "Not found"})
                print(f" ❌")

        # Show statistics
        print(f"\n📊 Statistics:")
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

  # Batch query
  steam-query batch "Elden Ring" "Hollow Knight" "Stardew Valley"

  # Batch query from file
  steam-query batch -i games.txt -o results.json

More info: https://github.com/carton/steam-query
        """,
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose logs"
    )

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

    # Batch query command
    batch_parser = subparsers.add_parser("batch", help="Query multiple games in batch")
    batch_input = batch_parser.add_mutually_exclusive_group(required=True)
    batch_input.add_argument(
        "queries", nargs="*", help="List of game names"
    )
    batch_input.add_argument(
        "-i", "--input", help="Input file (JSON or text, one game name per line)"
    )
    batch_parser.add_argument("-o", "--output", required=True, help="Output JSON file")

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
