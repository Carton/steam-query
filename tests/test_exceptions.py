"""Tests for custom exceptions."""

import pytest
from steam_query.exceptions import (
    SteamQueryError,
    NetworkError,
    TimeoutError,
    APIError,
    RateLimitError,
    GameNotFoundError,
    InvalidResponseError,
    ConfigurationError,
)


class TestExceptionHierarchy:
    """Test exception hierarchy"""

    def test_steam_query_error_is_exception(self):
        """Test that SteamQueryError is an Exception"""
        error = SteamQueryError("test")
        assert isinstance(error, Exception)
        assert str(error) == "test"

    def test_network_error_inherits_from_base(self):
        """Test NetworkError inherits from SteamQueryError"""
        error = NetworkError("network failed")
        assert isinstance(error, SteamQueryError)
        assert isinstance(error, Exception)

    def test_timeout_error_inherits_from_base(self):
        """Test TimeoutError inherits from SteamQueryError"""
        error = TimeoutError("request timeout")
        assert isinstance(error, SteamQueryError)

    def test_api_error_inherits_from_base(self):
        """Test APIError inherits from SteamQueryError"""
        error = APIError("API error", status_code=500)
        assert isinstance(error, SteamQueryError)
        assert error.status_code == 500

    def test_rate_limit_error_inherits_from_api_error(self):
        """Test RateLimitError inherits from APIError"""
        error = RateLimitError("Too many requests")
        assert isinstance(error, APIError)
        assert isinstance(error, SteamQueryError)

    def test_invalid_response_error_inherits_from_base(self):
        """Test InvalidResponseError inherits from SteamQueryError"""
        error = InvalidResponseError("Invalid JSON")
        assert isinstance(error, SteamQueryError)

    def test_configuration_error_inherits_from_base(self):
        """Test ConfigurationError inherits from SteamQueryError"""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, SteamQueryError)


class TestGameNotFoundError:
    """Test GameNotFoundError specific behavior"""

    def test_with_app_id(self):
        """Test creating error with App ID"""
        error = GameNotFoundError(app_id=1245620)
        assert "1245620" in str(error)
        assert error.app_id == 1245620
        assert error.query is None

    def test_with_query(self):
        """Test creating error with query"""
        error = GameNotFoundError(query="Elden Ring")
        assert "Elden Ring" in str(error)
        assert error.query == "Elden Ring"
        assert error.app_id is None

    def test_without_app_id_or_query(self):
        """Test creating error without App ID or query"""
        error = GameNotFoundError()
        assert "Game not found" in str(error)


class TestAPIError:
    """Test APIError specific behavior"""

    def test_with_status_code(self):
        """Test APIError with status code"""
        error = APIError("Not found", status_code=404)
        assert error.status_code == 404
        assert "404" in str(error)

    def test_without_status_code(self):
        """Test APIError without status code"""
        error = APIError("API error")
        assert error.status_code is None
