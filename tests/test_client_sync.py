"""Tests for SteamQuery sync client."""

from unittest.mock import AsyncMock, patch

import pytest

from steam_query import SteamQuery
from steam_query.exceptions import GameNotFoundError


class TestSteamQueryInit:
    """Test SteamQuery initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default values"""
        client = SteamQuery()

        # Note: _get_default_country may return CN, US, or other based on env/config
        assert client.country_code in ["US", "CN"]  # Accept both defaults
        assert client.language == "english"
        assert client._cache_size == 128
        assert client._cache_ttl == 300

    def test_init_with_custom_values(self):
        """Test initialization with custom values"""
        client = SteamQuery(
            country_code="JP",
            language="japanese",
            cache_size=64,
            cache_ttl=600,
        )

        assert client.country_code == "JP"
        assert client.language == "japanese"
        assert client._cache_size == 64
        assert client._cache_ttl == 600


class TestSteamQuerySearch:
    """Test search method"""

    @patch("steam_query.client_sync._search_async")
    def test_search_returns_results(self, mock_search):
        """Test search returns list of SearchResult"""
        from steam_query.types import SearchResult, Price

        mock_results = [
            {
                "app_id": 1245620,
                "name": "ELDEN RING",
                "short_desc": "Action RPG",
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
        ]
        mock_search.return_value = mock_results

        client = SteamQuery(country_code="US", language="english")
        results = client.search("Elden Ring", limit=5)

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].name == "ELDEN RING"
        assert results[0].app_id == 1245620
        assert results[0].price.final == 59.99

    @patch("steam_query.client_sync._search_async")
    def test_search_empty_results(self, mock_search):
        """Test search with no results"""
        mock_search.return_value = []

        client = SteamQuery()
        results = client.search("NonExistentGame")

        assert results == []


class TestSteamQueryGet:
    """Test get method"""

    @patch("steam_query.client_sync._get_game_async")
    def test_get_returns_game(self, mock_get):
        """Test get returns Game object"""
        from steam_query.types import Game, Price

        mock_game_dict = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "short_desc": "Action RPG",
            "long_desc": "Full description",
            "release_date": "2022-02-25",
            "developers": ["FromSoftware Inc."],
            "publishers": ["BANDAI NAMCO"],
            "genres": ["Action RPG"],
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
            "screenshots": [],
            "website": "https://eldenring.com",
            "requirements": {},
        }
        mock_get.return_value = mock_game_dict

        client = SteamQuery()
        game = client.get(1245620)

        assert game is not None
        assert isinstance(game, Game)
        assert game.name == "ELDEN RING"
        assert game.app_id == 1245620
        assert game.developers == ["FromSoftware Inc."]

    @patch("steam_query.client_sync._get_game_async")
    def test_get_raises_game_not_found(self, mock_get):
        """Test get raises GameNotFoundError"""
        mock_get.return_value = None

        client = SteamQuery()

        with pytest.raises(GameNotFoundError) as exc_info:
            client.get(999999999)

        assert exc_info.value.app_id == 999999999


class TestSteamQueryGetBatch:
    """Test get_batch method"""

    @patch("steam_query.client_sync._get_batch_async")
    def test_get_batch_returns_multiple_games(self, mock_batch):
        """Test get_batch returns dict of Games"""
        from steam_query.types import Game

        mock_batch.return_value = {
            1245620: {
                "app_id": 1245620,
                "name": "ELDEN RING",
                "short_desc": "",
                "long_desc": "",
                "release_date": "2022-02-25",
                "developers": [],
                "publishers": [],
                "genres": [],
                "tags": [],
                "metacritic_score": None,
                "price": None,
                "platforms": [],
                "is_free": False,
                "header_image": "",
                "screenshots": [],
                "website": None,
                "requirements": {},
            },
            1091500: {
                "app_id": 1091500,
                "name": "Cyberpunk 2077",
                "short_desc": "",
                "long_desc": "",
                "release_date": "2020-12-10",
                "developers": [],
                "publishers": [],
                "genres": [],
                "tags": [],
                "metacritic_score": None,
                "price": None,
                "platforms": [],
                "is_free": False,
                "header_image": "",
                "screenshots": [],
                "website": None,
                "requirements": {},
            },
        }

        client = SteamQuery()
        games = client.get_batch([1245620, 1091500, 9999999])

        assert len(games) == 2
        assert 1245620 in games
        assert 1091500 in games
        assert 9999999 not in games
        assert isinstance(games[1245620], Game)
        assert games[1245620].name == "ELDEN RING"


class TestSteamQueryFind:
    """Test find method"""

    @patch("steam_query.client_sync._search_async")
    @patch("steam_query.client_sync._get_game_async")
    def test_find_returns_first_result(self, mock_get, mock_search):
        """Test find returns first matching game"""
        mock_search.return_value = [
            {"app_id": 1245620, "name": "ELDEN RING", "short_desc": "", "price": None,
             "platforms": [], "metacritic": {"score": 96}, "review_score": None}
        ]
        mock_get.return_value = {
            "app_id": 1245620,
            "name": "ELDEN RING",
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
            "is_free": False,
            "header_image": "",
            "screenshots": [],
            "website": None,
            "requirements": {},
        }

        client = SteamQuery()
        game = client.find("Elden Ring")

        assert game is not None
        assert game.name == "ELDEN RING"

    @patch("steam_query.client_sync._search_async")
    def test_find_returns_none_if_no_results(self, mock_search):
        """Test find returns None if no search results"""
        mock_search.return_value = []

        client = SteamQuery()
        game = client.find("NonExistentGame")

        assert game is None
