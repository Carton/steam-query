"""Tests for high-level API functions (search_games, get_game_info, etc.)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from steam_query import get_game_info, get_games_info, search_games
from steam_query.types import Game, Price, SearchResult


class TestSearchGames:
    """Tests for search_games function."""

    @patch("steam_query.api._search_games_async")
    def test_search_games_returns_results(self, mock_async_search):
        """Test that search_games returns SearchResult objects."""
        # Mock the async implementation to return typed results
        expected_results = [
            SearchResult(
                app_id=1245620,
                name="ELDEN RING",
                short_desc="An expansive fantasy action-RPG",
                price=Price(
                    initial=59.99,
                    final=59.99,
                    discount_percent=0,
                    currency="USD",
                ),
                platforms=["Windows"],
                metacritic_score=96,
                review_score=None,
            )
        ]
        mock_async_search.return_value = expected_results

        results = search_games("Elden Ring", limit=10)

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].name == "ELDEN RING"
        assert results[0].app_id == 1245620
        assert results[0].price is not None
        assert results[0].price.final == 59.99

    @patch("steam_query.api._search_games_async")
    def test_search_games_empty_results(self, mock_async_search):
        """Test that search_games handles empty results."""
        mock_async_search.return_value = []

        results = search_games("NonExistentGame")

        assert results == []


class TestGetGameInfo:
    """Tests for get_game_info function."""

    @patch("steam_query.api._get_game_info_async")
    def test_get_game_info_returns_game_object(self, mock_async_get):
        """Test that get_game_info returns a Game object."""
        # Mock the async implementation to return a Game object
        expected_game = Game(
            app_id=1245620,
            name="ELDEN RING",
            short_desc="An expansive fantasy action-RPG",
            long_desc="Full description here...",
            release_date="2022-02-25",
            developers=["FromSoftware Inc."],
            publishers=["BANDAI NAMCO Entertainment"],
            genres=["Action RPG", "Adventure"],
            tags=["Fantasy", "Difficult"],
            metacritic_score=96,
            price=Price(
                initial=59.99,
                final=59.99,
                discount_percent=0,
                currency="USD",
            ),
            platforms=["Windows"],
            is_free=False,
            header_image="https://example.com/header.jpg",
            screenshots=["screenshot1.jpg"],
            website="https://www.eldenring.com/",
            requirements={},
        )
        mock_async_get.return_value = expected_game

        game = get_game_info(1245620)

        assert game is not None
        assert isinstance(game, Game)
        assert game.name == "ELDEN RING"
        assert game.app_id == 1245620
        assert game.developers == ["FromSoftware Inc."]
        assert game.price is not None
        assert game.price.final == 59.99

    @patch("steam_query.api._get_game_info_async")
    def test_get_game_info_not_found(self, mock_async_get):
        """Test that get_game_info returns None for non-existent games."""
        mock_async_get.return_value = None

        game = get_game_info(9999999)

        assert game is None


class TestGetGamesInfo:
    """Tests for get_games_info function."""

    @patch("steam_query.api._get_games_info_async")
    def test_get_games_info_returns_multiple_games(self, mock_async_get):
        """Test that get_games_info returns multiple Game objects."""
        # Mock the async implementation
        expected_games = {
            1245620: Game(
                app_id=1245620,
                name="ELDEN RING",
                short_desc="",
                long_desc="",
                release_date="2022-02-25",
                developers=["FromSoftware Inc."],
                publishers=["BANDAI NAMCO"],
                genres=["Action RPG"],
                tags=[],
                metacritic_score=96,
                price=None,
                platforms=["Windows"],
                is_free=False,
                header_image="",
                screenshots=[],
                website=None,
                requirements={},
            ),
            1091500: Game(
                app_id=1091500,
                name="Cyberpunk 2077",
                short_desc="",
                long_desc="",
                release_date="2020-12-10",
                developers=["CD Projekt Red"],
                publishers=["CD Projekt"],
                genres=["RPG"],
                tags=[],
                metacritic_score=86,
                price=None,
                platforms=["Windows"],
                is_free=False,
                header_image="",
                screenshots=[],
                website=None,
                requirements={},
            ),
        }
        mock_async_get.return_value = expected_games

        games = get_games_info([1245620, 1091500, 9999999])

        assert len(games) == 2  # Only 2 found
        assert 1245620 in games
        assert 1091500 in games
        assert 9999999 not in games  # Not found
        assert isinstance(games[1245620], Game)
        assert isinstance(games[1091500], Game)
        assert games[1245620].name == "ELDEN RING"
        assert games[1091500].name == "Cyberpunk 2077"

    @patch("steam_query.api._get_games_info_async")
    def test_get_games_info_empty_result(self, mock_async_get):
        """Test that get_games_info handles empty results."""
        mock_async_get.return_value = {}

        games = get_games_info([9999999, 8888888])

        assert games == {}


class TestPriceModel:
    """Tests for Price dataclass properties."""

    def test_price_is_free_property(self):
        """Test Price.is_free property."""
        # Free game (final is None)
        price_free = Price(initial=None, final=None, discount_percent=0, currency="USD")
        assert price_free.is_free is True

        # Paid game
        price_paid = Price(initial=59.99, final=59.99, discount_percent=0, currency="USD")
        assert price_paid.is_free is False

        # Free game (final is 0)
        price_zero = Price(initial=0, final=0, discount_percent=0, currency="USD")
        assert price_zero.is_free is True

    def test_price_is_discounted_property(self):
        """Test Price.is_discounted property."""
        # Discounted
        price_discounted = Price(
            initial=59.99, final=29.99, discount_percent=50, currency="USD"
        )
        assert price_discounted.is_discounted is True

        # Not discounted
        price_full = Price(
            initial=59.99, final=59.99, discount_percent=0, currency="USD"
        )
        assert price_full.is_discounted is False


class TestGameModel:
    """Tests for Game dataclass."""

    def test_game_from_dict_method(self):
        """Test Game.from_dict creates valid Game object."""
        game_dict = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "short_desc": "An expansive fantasy action-RPG",
            "long_desc": "Full description",
            "release_date": "2022-02-25",
            "developers": ["FromSoftware Inc."],
            "publishers": ["BANDAI NAMCO"],
            "genres": ["Action RPG", "Adventure"],
            "tags": ["Fantasy"],
            "metacritic_score": 96,
            "price": {
                "initial": 59.99,
                "final": 59.99,
                "discount_percent": 0,
                "currency": "USD",
            },
            "platforms": ["Windows"],
            "is_free": False,
            "header_image": "header.jpg",
            "screenshots": ["screenshot1.jpg"],
            "website": "https://example.com",
            "requirements": {},
        }

        game = Game.from_dict(game_dict)

        assert game.app_id == 1245620
        assert game.name == "ELDEN RING"
        assert game.developers == ["FromSoftware Inc."]
        assert game.price is not None
        assert game.price.final == 59.99

    def test_game_from_dict_with_missing_optional_fields(self):
        """Test Game.from_dict handles missing optional fields."""
        game_dict = {
            "app_id": 1245620,
            "name": "Test Game",
            "short_desc": "",
            "long_desc": "",
            "release_date": None,
            "developers": [],
            "publishers": [],
            "genres": [],
            "tags": [],
            "metacritic_score": None,
            "price": None,
            "platforms": [],
            "is_free": True,
            "header_image": "",
            "screenshots": [],
            "website": None,
            "requirements": {},
        }

        game = Game.from_dict(game_dict)

        assert game.app_id == 1245620
        assert game.name == "Test Game"
        assert game.price is None
        assert game.is_free is True


class TestSearchResultModel:
    """Tests for SearchResult dataclass."""

    def test_search_result_from_dict_method(self):
        """Test SearchResult.from_dict creates valid SearchResult object."""
        result_dict = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "short_desc": "An expansive fantasy action-RPG",
            "price": {
                "initial": 59.99,
                "final": 59.99,
                "discount_percent": 0,
                "currency": "USD",
            },
            "platforms": ["Windows"],
            "metacritic": {"score": 96},
            "review_score": None,
        }

        result = SearchResult.from_dict(result_dict)

        assert result.app_id == 1245620
        assert result.name == "ELDEN RING"
        assert result.price is not None
        assert result.price.final == 59.99
        assert result.metacritic_score == 96


class TestAPIClientInitialization:
    """Tests for API wrapper passing correct arguments to SteamStoreClient."""

    @patch("steam_query.api.SteamStoreClient")
    @pytest.mark.asyncio
    async def test_search_games_passes_rate_limit(self, mock_client_class):
        """Test that _search_games_async passes requests_per_second."""
        from steam_query.api import _search_games_async

        # Setup mock context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.search_games_by_name.return_value = []
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance

        await _search_games_async("test", 10, "US", "english", requests_per_second=2.5)

        mock_client_class.assert_called_once_with(
            country_code="US", language="english", requests_per_second=2.5
        )

    @patch("steam_query.api.SteamStoreClient")
    @pytest.mark.asyncio
    async def test_get_game_info_passes_rate_limit(self, mock_client_class):
        """Test that _get_game_info_async passes requests_per_second."""
        from steam_query.api import _get_game_info_async

        # Setup mock context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.get_app_details.return_value = None
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance

        await _get_game_info_async(123, "US", "english", requests_per_second=3.0)

        mock_client_class.assert_called_once_with(
            country_code="US", language="english", requests_per_second=3.0
        )

    @patch("steam_query.api.SteamStoreClient")
    @pytest.mark.asyncio
    async def test_get_games_info_passes_rate_limit(self, mock_client_class):
        """Test that _get_games_info_async passes requests_per_second."""
        from steam_query.api import _get_games_info_async

        # Setup mock context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.get_games_details_batch.return_value = {}
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance

        await _get_games_info_async([123], "US", "english", requests_per_second=4.0)

        mock_client_class.assert_called_once_with(
            country_code="US", language="english", requests_per_second=4.0
        )
