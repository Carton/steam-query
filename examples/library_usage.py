"""Examples of using steam-query as a Python library.

This demonstrates the simplified API for programmatic access to Steam game data.
"""

from steam_query import (
    SteamStoreClient,
    get_game_info,
    get_games_info,
    search_games,
)


def example_simple_search():
    """Example 1: Simple search (recommended for most users)."""
    print("=== Example 1: Simple Search ===")

    # Search for games - automatic async handling
    results = search_games("Elden Ring", limit=3)

    for game in results:
        # Typed fields with IDE autocomplete support
        print(f"\n🎮 {game.name}")
        print(f"   App ID: {game.app_id}")

        # Price information with safe access
        if game.price:
            if game.price.is_free:
                print("   💰 Price: Free to play")
            elif game.price.is_discounted:
                print(
                    f"   💰 Price: ${game.price.final:.2f} "
                    f"(was ${game.price.initial:.2f}, -{game.price.discount_percent}%)"
                )
            else:
                print(f"   💰 Price: ${game.price.final:.2f}")

        print(
            f"   📊 Metacritic: {game.metacritic_score}/100"
            if game.metacritic_score
            else "   📊 Metacritic: N/A"
        )
        print(f"   🏷️  Tags: {', '.join(game.tags[:5])}")  # First 5 tags


def example_get_game_details():
    """Example 2: Get detailed game information."""
    print("\n\n=== Example 2: Get Game Details ===")

    # Get complete game information
    game = get_game_info(1245620)  # Elden Ring

    if game:
        print(f"\n🎮 {game.name}")
        print(f"📝 {game.short_desc}")
        print(f"\n📅 Release Date: {game.release_date}")
        print(f"🏢 Developers: {', '.join(game.developers)}")
        print(f"🎭 Genres: {', '.join(game.genres)}")

        # System requirements
        if game.requirements:
            print("\n💻 Minimum Requirements:")
            min_reqs = game.requirements.get("minimum")
            if min_reqs:
                print(f"   OS: {min_reqs.os}")
                print(f"   Processor: {min_reqs.processor}")
                print(f"   Memory: {min_reqs.memory}")
                print(f"   Storage: {min_reqs.storage}")


def example_batch_query():
    """Example 3: Query multiple games at once."""
    print("\n\n=== Example 3: Batch Query ===")

    # Query multiple games by App ID
    app_ids = [1245620, 1091500, 413150]  # Elden Ring, Cyberpunk 2077, Stardew Valley
    games = get_games_info(app_ids)

    print(f"\nFound {len(games)} games:")
    for app_id, game in games.items():
        print(f"\n{app_id}: {game.name}")
        print(f"   Genres: {', '.join(game.genres[:3])}")
        if game.price and not game.price.is_free:
            print(f"   Price: ${game.price.final:.2f} {game.price.currency}")


def example_async_usage():
    """Example 4: Advanced async usage with custom configuration."""
    print("\n\n=== Example 4: Advanced Async Usage ===")

    import asyncio

    async def advanced_search():
        """Custom async search with specific configuration."""
        # Use async context manager for advanced usage
        async with SteamStoreClient(country_code="JP", language="english") as client:
            # Search for Japanese pricing
            results = await client.search_games_by_name("Hollow Knight", limit=1)

            for game_dict in results:
                # Raw dict access for maximum compatibility
                name = game_dict["name"]
                price_data = game_dict.get("price")

                print(f"\n🎮 {name}")
                if price_data:
                    print(f"   💰 JPY Price: ¥{price_data.get('final', 0)}")

    asyncio.run(advanced_search())


def example_data_conversion():
    """Example 5: Converting between typed models and dicts."""
    print("\n\n=== Example 5: Data Model Conversion ===")

    # Get game as typed model
    game = get_game_info(1245620)

    if game:
        print("\n🎮 Typed Model Access:")
        print(f"   Name: {game.name}")
        print(f"   Is Free: {game.is_free}")

        # Convert back to dict if needed
        game_dict = {
            "app_id": game.app_id,
            "name": game.name,
            "short_desc": game.short_desc,
            "genres": game.genres,
            # ... all fields accessible
        }
        print(f"\n   Dict representation: {list(game_dict.keys())}")


def example_price_comparison():
    """Example 6: Compare prices across regions."""
    print("\n\n=== Example 6: Price Comparison ===")

    regions = ["US", "JP", "KR", "CN"]
    app_id = 1091500  # Cyberpunk 2077

    print(f"\n💰 Price comparison for App ID {app_id}:")

    for region in regions:
        game = get_game_info(app_id, country_code=region)
        if game and game.price:
            print(f"\n{region}: ${game.price.final:.2f} {game.price.currency}")


if __name__ == "__main__":
    # Run all examples
    example_simple_search()
    example_get_game_details()
    example_batch_query()
    example_async_usage()
    example_data_conversion()
    example_price_comparison()

    print("\n\n✅ All examples completed!")
    print("\n💡 Tip: Use search_games() and get_game_info() for simple usage")
    print("💡 Tip: Use SteamStoreClient directly for advanced async usage")
