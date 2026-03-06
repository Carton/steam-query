"""Tests for CLI functionality."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from steam_query.cli import (
    format_game_info,
    format_game_json,
    setup_logging,
)
from steam_query.types import Game, Price, SystemRequirements


class TestFormatGameInfo:
    """Tests for format_game_info function."""

    def test_format_basic_game_info(self):
        """Test formatting basic game information."""
        game = Game(
            app_id=1245620,
            name="ELDEN RING",
            short_desc="An expansive fantasy action-RPG",
            long_desc="...",
            release_date="2022-02-25",
            developers=["FromSoftware Inc."],
            publishers=["BANDAI NAMCO"],
            genres=["Action RPG", "Adventure"],
            tags=[],
            metacritic_score=96,
            price=None,
            platforms=["Windows"],
            is_free=False,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )

        result = format_game_info(game)

        assert "ELDEN RING" in result
        assert "1245620" in result
        assert "2022-02-25" in result
        assert "FromSoftware Inc." in result
        assert "Action RPG" in result
        assert "96/100" in result

    def test_format_price_with_discount(self):
        """Test formatting price with discount."""
        price = Price(
            initial=59.99,
            final=29.99,
            discount_percent=50,
            currency="USD",
        )
        game = Game(
            app_id=1245620,
            name="Test Game",
            short_desc="Test description",
            long_desc="...",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=None,
            price=price,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )

        result = format_game_info(game)

        assert "29.99 USD" in result
        assert "59.99 USD" in result
        assert "-50%" in result

    def test_format_price_without_discount(self):
        """Test formatting price without discount."""
        price = Price(
            initial=59.99,
            final=59.99,
            discount_percent=0,
            currency="USD",
        )
        game = Game(
            app_id=1245620,
            name="Test Game",
            short_desc="Test description",
            long_desc="...",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=None,
            price=price,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )

        result = format_game_info(game)

        assert "59.99 USD" in result
        assert "-50%" not in result

    def test_format_price_no_decimals(self):
        """Test formatting price for currency without decimals (JPY)."""
        price = Price(
            initial=6000,
            final=6000,
            discount_percent=0,
            currency="JPY",
        )
        game = Game(
            app_id=1245620,
            name="Test Game",
            short_desc="Test description",
            long_desc="...",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=None,
            price=price,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )

        result = format_game_info(game)

        assert "6000 JPY" in result
        # Should not have decimal points
        assert "6000.00 JPY" not in result

    def test_format_free_game(self):
        """Test formatting free game."""
        game = Game(
            app_id=1245620,
            name="Free Game",
            short_desc="",
            long_desc="",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=None,
            price=None,
            platforms=[],
            is_free=True,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )

        result = format_game_info(game)

        assert "Free" in result

    def test_format_metacritic_score_colors(self):
        """Test Metacritic score emoji coloring."""
        # High score (green)
        game_high = Game(
            app_id=1,
            name="Test",
            short_desc="",
            long_desc="",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=90,
            price=None,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )
        result_high = format_game_info(game_high)
        assert "🟢" in result_high

        # Medium score (yellow)
        game_med = Game(
            app_id=1,
            name="Test",
            short_desc="",
            long_desc="",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=65,
            price=None,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )
        result_med = format_game_info(game_med)
        assert "🟡" in result_med

        # Low score (red)
        game_low = Game(
            app_id=1,
            name="Test",
            short_desc="",
            long_desc="",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=40,
            price=None,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )
        result_low = format_game_info(game_low)
        assert "🔴" in result_low


class TestFormatGameJson:
    """Tests for format_game_json function."""

    def test_format_json_removes_long_desc(self):
        """Test that long_desc is removed from JSON output."""
        game = Game(
            app_id=1245620,
            name="Test Game",
            long_desc="A" * 1000,
            short_desc="Short description",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=None,
            price=None,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=["screenshot1.jpg", "screenshot2.jpg"],  # Should be removed
            website=None,
            requirements={},
        )

        result = format_game_json(game)
        data = json.loads(result)

        assert "long_desc" not in data
        assert data["short_desc"] == "Short description"

    def test_format_json_removes_screenshots(self):
        """Test that screenshots are removed from JSON output."""
        game = Game(
            app_id=1245620,
            name="Test Game",
            long_desc="",
            short_desc="Test",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=None,
            price=None,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=["screenshot1.jpg", "screenshot2.jpg"],
            website=None,
            requirements={},
        )

        result = format_game_json(game)
        data = json.loads(result)

        assert "screenshots" not in data

    def test_format_json_valid_json(self):
        """Test that output is valid JSON."""
        price = Price(
            initial=None,
            final=29.99,
            discount_percent=0,
            currency="USD",
        )
        game = Game(
            app_id=1245620,
            name="Test Game",
            long_desc="",
            short_desc="Test",
            release_date=None,
            developers=[],
            publishers=[],
            genres=[],
            tags=[],
            metacritic_score=None,
            price=price,
            platforms=[],
            is_free=False,
            header_image="",
            screenshots=[],
            website=None,
            requirements={},
        )

        result = format_game_json(game)

        # Should not raise exception
        data = json.loads(result)
        assert data["app_id"] == 1245620


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_creates_handler(self):
        """Test that setup_logging creates a log handler."""
        import logging

        setup_logging(verbose=False)

        root_logger = logging.root
        assert root_logger.level == logging.INFO

        setup_logging(verbose=True)
        assert root_logger.level == logging.DEBUG


class TestSearchCommand:
    """Tests for search command."""

    @pytest.mark.asyncio
    async def test_search_command_with_results(self):
        """Test search command returns results."""
        from steam_query.cli import search_command

        mock_results = [
            {
                "app_id": 1245620,
                "name": "ELDEN RING",
                "short_desc": "Action RPG",
                "price": {"final": 59.99, "currency": "USD"},
            }
        ]

        with patch("steam_query.cli.SteamStoreClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.search_games_by_name = AsyncMock(return_value=mock_results)
            mock_client_class.return_value = mock_client

            args = MagicMock(query="Elden Ring", limit=10, output=None)
            result = await search_command(args)

            assert result == 0
            mock_client.search_games_by_name.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_command_no_results(self):
        """Test search command with no results."""
        from steam_query.cli import search_command

        with patch("steam_query.cli.SteamStoreClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.search_games_by_name = AsyncMock(return_value=[])
            mock_client_class.return_value = mock_client

            args = MagicMock(query="NonExistent", limit=10, output=None)
            result = await search_command(args)

            assert result == 1


class TestLookupCommand:
    """Tests for lookup command."""

    @pytest.mark.asyncio
    async def test_lookup_by_app_id(self):
        """Test lookup command with App ID."""
        from steam_query.cli import lookup_command

        mock_game = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "price": {"final": 59.99, "currency": "USD"},
        }

        with patch("steam_query.cli.SteamStoreClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get_app_details = AsyncMock(return_value=mock_game)
            mock_client_class.return_value = mock_client

            args = MagicMock(app_id=1245620, query=None, json=False, output=None)
            result = await lookup_command(args)

            assert result == 0
            mock_client.get_app_details.assert_called_once_with(1245620)

    @pytest.mark.asyncio
    async def test_lookup_by_name_search(self):
        """Test lookup command with name search."""
        from steam_query.cli import lookup_command

        mock_search_results = [{"app_id": 1245620, "name": "ELDEN RING"}]
        mock_game = {
            "app_id": 1245620,
            "name": "ELDEN RING",
            "price": {"final": 59.99, "currency": "USD"},
        }

        with patch("steam_query.cli.SteamStoreClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.search_games_by_name = AsyncMock(
                return_value=mock_search_results
            )
            mock_client.get_app_details = AsyncMock(return_value=mock_game)
            mock_client_class.return_value = mock_client

            args = MagicMock(app_id=None, query="Elden Ring", json=False, output=None)
            result = await lookup_command(args)

            assert result == 0
            mock_client.search_games_by_name.assert_called_once()
            mock_client.get_app_details.assert_called_once()


class TestBatchCommand:
    """Tests for batch command."""

    @pytest.mark.asyncio
    async def test_batch_command_from_args(self):
        """Test batch command with game names as arguments."""
        from steam_query.cli import batch_command

        mock_games = [
            {"app_id": 1245620, "name": "ELDEN RING"},
            {"app_id": 1091500, "name": "Cyberpunk 2077"},
        ]

        with patch("steam_query.cli.SteamStoreClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            # Mock search and get_details
            mock_client.search_games_by_name = AsyncMock(
                side_effect=[
                    [{"app_id": 1245620, "name": "ELDEN RING"}],
                    [{"app_id": 1091500, "name": "Cyberpunk 2077"}],
                ]
            )
            mock_client.get_app_details = AsyncMock(side_effect=mock_games)
            mock_client_class.return_value = mock_client

            args = MagicMock(
                queries=["ELDEN RING", "Cyberpunk 2077"],
                input=None,
                output="results.json",
            )
            result = await batch_command(args)

            assert result == 0
            assert mock_client.search_games_by_name.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_command_from_file(self):
        """Test batch command reading from file."""
        from steam_query.cli import batch_command

        mock_games = [{"app_id": 1245620, "name": "ELDEN RING"}]

        # Create temp file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("ELDEN RING\n")
            f.write("Hollow Knight\n")
            temp_file = f.name

        try:
            with patch("steam_query.cli.SteamStoreClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()

                mock_client.search_games_by_name = AsyncMock(
                    return_value=[{"app_id": 1245620, "name": "ELDEN RING"}]
                )
                mock_client.get_app_details = AsyncMock(return_value=mock_games[0])
                mock_client_class.return_value = mock_client

                args = MagicMock(queries=None, input=temp_file, output="results.json")
                result = await batch_command(args)

                assert result == 0
        finally:
            Path(temp_file).unlink(missing_ok=True)
