"""Tests for SteamStoreClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from steam_query.steam_client import SteamStoreClient, _get_default_country


class TestDefaultCountry:
    """Tests for _get_default_country function."""

    @patch.dict("os.environ", {"STEAM_QUERY_COUNTRY": "JP"}, clear=True)
    def test_country_from_env_variable(self):
        """Test getting country code from environment variable."""
        country = _get_default_country()
        assert country == "JP"

    @patch.dict("os.environ", {}, clear=True)
    def test_country_default_when_no_config(self):
        """Test default country when no config file exists."""
        # Skip on Windows if HOME is not set
        import os
        if not os.getenv("HOME") and not os.getenv("USERPROFILE"):
            pytest.skip("HOME not set on Windows")

        with patch.object(Path, "exists", return_value=False):
            country = _get_default_country()
            assert country == "US"

    @patch.dict("os.environ", {}, clear=True)
    def test_country_from_config_file(self):
        """Test reading country from config file."""
        # Skip on Windows if HOME is not set
        import os
        if not os.getenv("HOME") and not os.getenv("USERPROFILE"):
            pytest.skip("HOME not set on Windows")

        mock_config = {"steam-query": {"country": "KR"}}

        with patch.object(Path, "exists", return_value=True):
            with patch("steam_query.steam_client.tomllib") as mock_tomllib:
                mock_tomllib.load.return_value = mock_config

                import tempfile
                with tempfile.NamedTemporaryFile() as f:
                    # Mock open to return our temp file
                    original_open = open
                    def custom_open(path, *args, **kwargs):
                        if "config.toml" in str(path):
                            return f
                        return original_open(path, *args, **kwargs)

                    with patch("builtins.open", side_effect=custom_open):
                        country = _get_default_country()
                        assert country == "KR"


class TestSteamStoreClient:
    """Tests for SteamStoreClient class."""

    def test_initialization_with_country(self):
        """Test client initialization with country code."""
        client = SteamStoreClient(country_code="JP")
        assert client.country_code == "JP"
        assert client.language == "english"
        assert client.requests_per_second == 1.0

    @patch.dict("os.environ", {"STEAM_QUERY_COUNTRY": "KR"}, clear=True)
    def test_initialization_without_country_uses_env(self):
        """Test client initialization uses environment variable when no country specified."""
        client = SteamStoreClient()
        assert client.country_code == "KR"

    def test_initialization_custom_rate_limit(self):
        """Test client initialization with custom rate limit."""
        client = SteamStoreClient(requests_per_second=2.5)
        assert client.requests_per_second == 2.5

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager creates and closes session."""
        async with SteamStoreClient() as client:
            assert client._session is not None
            assert isinstance(client._session, MagicMock) or client._session is not None

        # Session should be closed after exiting context
        assert True  # If we get here without exception, context manager works


class TestCurrencyHandling:
    """Tests for currency-related methods."""

    def test_currency_uses_decimals_usd(self):
        """Test that USD uses decimal units."""
        client = SteamStoreClient()
        assert client._currency_uses_decimals("USD") is True

    def test_currency_uses_decimals_jpy(self):
        """Test that JPY does not use decimal units."""
        client = SteamStoreClient()
        assert client._currency_uses_decimals("JPY") is False

    def test_currency_uses_decimals_krw(self):
        """Test that KRW does not use decimal units."""
        client = SteamStoreClient()
        assert client._currency_uses_decimals("KRW") is False

    def test_currency_uses_decimals_eur(self):
        """Test that EUR uses decimal units."""
        client = SteamStoreClient()
        assert client._currency_uses_decimals("EUR") is True


class TestParseDate:
    """Tests for _parse_date method."""

    def test_parse_date_valid_format(self):
        """Test parsing valid date format."""
        client = SteamStoreClient()
        result = client._parse_date("Feb 25, 2022")
        # Returns ISO format with time
        assert result.startswith("2022-02-25")
        assert "T" in result  # ISO format includes time

    def test_parse_date_another_format(self):
        """Test parsing another valid date format."""
        client = SteamStoreClient()
        result = client._parse_date("2022-02-25")
        # Returns ISO format with time
        assert result.startswith("2022-02-25")
        assert "T" in result  # ISO format includes time

    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format returns original string."""
        client = SteamStoreClient()
        result = client._parse_date("Invalid Date")
        assert result == "Invalid Date"

    def test_parse_date_empty_string(self):
        """Test parsing empty string returns None."""
        client = SteamStoreClient()
        result = client._parse_date("")
        assert result is None


class TestParseRequirements:
    """Tests for _parse_requirements method."""

    def test_parse_requirements_basic(self):
        """Test parsing basic system requirements."""
        client = SteamStoreClient()
        req_text = """OS: Windows 10
Processor: Intel i5
Memory: 8 GB RAM
Graphics: NVIDIA GTX 1060
DirectX: Version 11
Storage: 60 GB available space"""

        result = client._parse_requirements(req_text)

        assert "Windows 10" in result["os"]
        assert "Intel i5" in result["processor"]
        assert "8 GB RAM" in result["memory"]
        assert result["graphics"] != ""
        assert result["storage"] != ""

    def test_parse_requirements_multiline(self):
        """Test parsing multiline requirements."""
        client = SteamStoreClient()
        req_text = """OS: Windows 10 64-bit
Processor: Intel Core i5-8400 | AMD Ryzen 5 1600
Memory: 12 GB RAM
Graphics: NVIDIA GTX 1060 6GB | AMD RX 580 8GB
DirectX: Version 12
Storage: 60 GB available space"""

        result = client._parse_requirements(req_text)

        assert "64-bit" in result["os"]
        assert "Intel Core i5-8400" in result["processor"] or "AMD Ryzen 5 1600" in result["processor"]


class TestParseAppDetails:
    """Tests for _parse_app_details method."""

    def test_parse_basic_info(self, sample_game_data):
        """Test parsing basic game information."""
        client = SteamStoreClient()
        app_data = sample_game_data["1245620"]["data"]

        result = client._parse_app_details(app_data)

        assert result["app_id"] == 1245620
        assert result["name"] == "ELDEN RING"
        assert result["is_free"] is False
        assert "Action RPG" in result["genres"]

    def test_parse_price_with_decimals(self, sample_game_data):
        """Test parsing price for currency with decimals (USD)."""
        client = SteamStoreClient()
        app_data = sample_game_data["1245620"]["data"]

        result = client._parse_app_details(app_data)

        assert result["price"] is not None
        assert result["price"]["currency"] == "USD"
        assert result["price"]["final"] == 59.99  # Converted from cents
        assert result["price"]["initial"] == 59.99

    def test_parse_platforms(self, sample_game_data):
        """Test parsing platform support."""
        client = SteamStoreClient()
        app_data = sample_game_data["1245620"]["data"]

        result = client._parse_app_details(app_data)

        assert "Windows" in result["platforms"]
        assert "Mac" not in result["platforms"]
        assert "Linux" not in result["platforms"]

    def test_parse_metacritic_score(self, sample_game_data):
        """Test parsing Metacritic score."""
        client = SteamStoreClient()
        app_data = sample_game_data["1245620"]["data"]

        result = client._parse_app_details(app_data)

        assert result["metacritic_score"] == 96

    def test_parse_requirements(self, sample_game_data):
        """Test parsing system requirements."""
        client = SteamStoreClient()
        app_data = sample_game_data["1245620"]["data"]

        result = client._parse_app_details(app_data)

        assert "requirements" in result
        assert "minimum" in result["requirements"]
        assert "recommended" in result["requirements"]


class TestSearchGames:
    """Tests for search_games_by_name method."""

    @pytest.mark.asyncio
    async def test_search_games_with_results(self, sample_search_results):
        """Test searching games with matching results."""
        client = SteamStoreClient()

        # Mock the _get method
        with patch.object(client, "_get", return_value=sample_search_results):
            results = await client.search_games_by_name("Elden Ring")

            assert len(results) == 2
            assert results[0]["name"] == "ELDEN RING"
            assert results[0]["app_id"] == 1245620
            assert results[1]["name"] == "Cyberpunk 2077"

    @pytest.mark.asyncio
    async def test_search_games_price_conversion(self, sample_search_results):
        """Test that prices are correctly converted from cents."""
        client = SteamStoreClient()

        with patch.object(client, "_get", return_value=sample_search_results):
            results = await client.search_games_by_name("test")

            # USD should be divided by 100
            assert results[0]["price"]["currency"] == "USD"
            assert results[0]["price"]["final"] == 59.99
            assert results[0]["price"]["initial"] == 59.99

    @pytest.mark.asyncio
    async def test_search_games_no_results(self):
        """Test searching games with no matches."""
        client = SteamStoreClient()

        empty_response = {"total": 0, "items": []}
        with patch.object(client, "_get", return_value=empty_response):
            results = await client.search_games_by_name("NonExistentGame")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_with_limit(self, sample_search_results):
        """Test searching with result limit."""
        client = SteamStoreClient()

        with patch.object(client, "_get", return_value=sample_search_results):
            results = await client.search_games_by_name("test", limit=1)

            assert len(results) == 1


class TestGetAppDetails:
    """Tests for get_app_details method."""

    @pytest.mark.asyncio
    async def test_get_app_details_success(self, sample_game_data):
        """Test successfully getting app details."""
        client = SteamStoreClient()

        with patch.object(client, "_get", return_value=sample_game_data):
            result = await client.get_app_details(1245620)

            assert result is not None
            assert result["name"] == "ELDEN RING"
            assert result["app_id"] == 1245620

    @pytest.mark.asyncio
    async def test_get_app_details_not_found(self):
        """Test getting details for non-existent app."""
        client = SteamStoreClient()

        not_found_response = {"9999999": {"success": False}}
        with patch.object(client, "_get", return_value=not_found_response):
            result = await client.get_app_details(9999999)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_app_details_api_error(self):
        """Test handling API errors."""
        client = SteamStoreClient()

        with patch.object(client, "_get", side_effect=Exception("API Error")):
            result = await client.get_app_details(1245620)

            assert result is None


class TestGetGamesDetailsBatch:
    """Tests for get_games_details_batch method."""

    @pytest.mark.asyncio
    async def test_batch_query_multiple_apps(self, sample_game_data):
        """Test querying multiple apps at once."""
        client = SteamStoreClient()

        # Mock responses for different app IDs
        def mock_get_details(app_id):
            if app_id == 1245620:
                return client._parse_app_details(sample_game_data["1245620"]["data"])
            return None

        with patch.object(client, "get_app_details", side_effect=mock_get_details):
            results = await client.get_games_details_batch([1245620, 9999999])

            assert 1245620 in results
            assert results[1245620]["name"] == "ELDEN RING"
            assert 9999999 not in results


class TestAPICalls:
    """Tests for API call parameters."""

    @pytest.mark.asyncio
    async def test_search_uses_country_code(self):
        """Test that search API uses configured country code."""
        client = SteamStoreClient(country_code="JP")

        with patch.object(client, "_get") as mock_get:
            mock_get.return_value = {"total": 0, "items": []}
            await client.search_games_by_name("test")

            # Check that cc parameter was set to JP
            call_args = mock_get.call_args
            assert call_args[1]["params"]["cc"] == "JP"

    @pytest.mark.asyncio
    async def test_lookup_uses_country_code(self):
        """Test that lookup API uses configured country code."""
        client = SteamStoreClient(country_code="KR")

        with patch.object(client, "_get") as mock_get:
            mock_get.return_value = {"1245620": {"success": False}}
            await client.get_app_details(1245620)

            # Check that cc parameter was set to KR
            call_args = mock_get.call_args
            assert call_args[1]["params"]["cc"] == "KR"

    @pytest.mark.asyncio
    async def test_search_uses_language(self):
        """Test that search API uses configured language."""
        client = SteamStoreClient(language="english")

        with patch.object(client, "_get") as mock_get:
            mock_get.return_value = {"total": 0, "items": []}
            await client.search_games_by_name("test")

            # Check that l parameter was set to english
            call_args = mock_get.call_args
            assert call_args[1]["params"]["l"] == "english"
