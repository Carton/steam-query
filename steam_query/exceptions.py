"""Custom exceptions for steam-query."""


class SteamQueryError(Exception):
    """Base exception for all steam-query errors."""

    pass


class NetworkError(SteamQueryError):
    """Network request failed."""

    pass


class RequestTimeoutError(SteamQueryError):
    """Request timeout."""

    pass


class APIError(SteamQueryError):
    """Steam API returned an error."""

    def __init__(self, message: str, status_code: int | None = None):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code (if available)
        """
        self.status_code = status_code
        if status_code:
            message = f"{message} (status: {status_code})"
        super().__init__(message)


class RateLimitError(APIError):
    """Rate limit exceeded."""

    pass


class GameNotFoundError(SteamQueryError):
    """Game not found."""

    def __init__(self, app_id: int | None = None, query: str | None = None):
        """Initialize game not found error.

        Args:
            app_id: Steam App ID
            query: Search query
        """
        self.app_id = app_id
        self.query = query

        if app_id:
            message = f"Game not found: App ID {app_id}"
        elif query:
            message = f"Game not found: {query}"
        else:
            message = "Game not found"

        super().__init__(message)


class InvalidResponseError(SteamQueryError):
    """Invalid API response data."""

    pass


class ConfigurationError(SteamQueryError):
    """Configuration error."""

    pass
