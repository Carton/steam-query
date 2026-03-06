"""Integration tests with real Steam API

These tests are marked as 'integration' and can be skipped:
- pytest tests/ -m "not integration"  # Skip integration tests
- pytest tests/ -m integration         # Run only integration tests
"""

import time
import pytest

from steam_query import SteamQuery, get_game_info, search_games
from steam_query.exceptions import GameNotFoundError


# Test data: Popular, stable games
ELDEN_RING = 1245620
HOLLOW_KNIGHT = 367520
HADES = 1593500
CYBERPUNK = 1091500


@pytest.mark.integration
class TestSteamQueryRealAPI:
    """Test SteamQuery with real API"""

    def test_get_elden_ring(self):
        """Test fetching a popular game (Elden Ring)"""
        client = SteamQuery()

        game = client.get(ELDEN_RING)

        assert game is not None
        assert game.name == "ELDEN RING"
        assert game.app_id == ELDEN_RING
        assert len(game.developers) > 0
        assert len(game.genres) > 0
        assert len(game.platforms) > 0

    def test_search_hollow_knight(self):
        """Test searching for Hollow Knight"""
        client = SteamQuery()

        results = client.search("Hollow Knight", limit=5)

        assert len(results) > 0
        # First result should be Hollow Knight
        assert "Hollow Knight" in results[0].name
        assert results[0].app_id == HOLLOW_KNIGHT

    def test_get_batch_multiple_games(self):
        """Test batch query"""
        client = SteamQuery()

        games = client.get_batch([ELDEN_RING, CYBERPUNK, HADES])

        assert len(games) == 3
        assert ELDEN_RING in games
        assert CYBERPUNK in games
        assert HADES in games
        assert games[ELDEN_RING].name == "ELDEN RING"
        assert games[CYBERPUNK].name == "Cyberpunk 2077"
        assert games[HADES].name == "Hades"

    def test_cache_works(self):
        """Test that caching reduces actual API calls"""
        client = SteamQuery(cache_ttl=60)

        # First call - should hit API
        start = time.time()
        game1 = client.get(ELDEN_RING)
        first_duration = time.time() - start

        # Second call - should hit cache
        start = time.time()
        game2 = client.get(ELDEN_RING)
        second_duration = time.time() - start

        assert game1 == game2
        # Cached call should be much faster (< 50% of first call)
        assert second_duration < first_duration / 2

    def test_find_hades(self):
        """Test find method"""
        client = SteamQuery()

        game = client.find("Hades")

        assert game is not None
        assert game.name == "Hades"
        assert game.app_id == HADES


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling with real API"""

    def test_game_not_found(self):
        """Test fetching non-existent game"""
        client = SteamQuery()

        with pytest.raises(GameNotFoundError) as exc_info:
            client.get(999999999)

        assert exc_info.value.app_id == 999999999

    def test_search_empty_results(self):
        """Test search with no results"""
        client = SteamQuery()

        results = client.search("NonExistentGameXYZ123", limit=10)

        assert results == []


@pytest.mark.integration
class TestHighLevelAPI:
    """Test high-level API functions"""

    def test_search_games_function(self):
        """Test search_games function"""
        results = search_games("Stardew Valley", limit=3)

        assert len(results) > 0
        assert "Stardew Valley" in results[0].name

    def test_get_game_info_function(self):
        """Test get_game_info function"""
        game = get_game_info(HADES)

        assert game is not None
        assert game.name == "Hades"
        assert game.app_id == HADES

    def test_get_games_info_function(self):
        """Test get_games_info function"""
        games = get_games_info([ELDEN_RING, HADES])

        assert len(games) == 2
        assert ELDEN_RING in games
        assert HADES in games
