"""Data models for Steam game information.

Provides type-safe data classes for game information, replacing raw dicts.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Price:
    """Game price information.

    Attributes:
        initial: Original price (None if free)
        final: Current price (None if free)
        discount_percent: Discount percentage (0-100)
        currency: Currency code (e.g., USD, EUR, JPY)
    """

    initial: float | None
    final: float | None
    discount_percent: int
    currency: str

    @property
    def is_free(self) -> bool:
        """Check if the game is free."""
        return self.final is None or self.final == 0

    @property
    def is_discounted(self) -> bool:
        """Check if the game is currently on discount."""
        return self.discount_percent > 0


@dataclass(frozen=True)
class SystemRequirements:
    """System requirements for running the game.

    Attributes:
        os: Operating system requirement
        processor: CPU requirement
        memory: RAM requirement
        graphics: GPU requirement
        directx: DirectX version requirement
        storage: Disk space requirement
    """

    os: str = ""
    processor: str = ""
    memory: str = ""
    graphics: str = ""
    directx: str = ""
    storage: str = ""


@dataclass(frozen=True)
class Game:
    """Complete information about a Steam game.

    This is the primary data model returned by the library.

    Attributes:
        app_id: Steam App ID
        name: Game title
        short_desc: Short description (1-2 sentences)
        long_desc: Detailed description (first 500 chars)
        release_date: ISO format release date or None
        developers: List of developer names
        publishers: List of publisher names
        genres: List of genre names
        tags: List of user tags
        metacritic_score: Metacritic score (0-100) or None
        price: Price information or None if free
        platforms: List of supported platforms (Windows, Mac, Linux)
        is_free: Whether the game is free to play
        header_image: URL to header image
        screenshots: List of screenshot URLs (max 5)
        website: Official website URL or None
        requirements: System requirements (minimum and recommended)
    """

    app_id: int
    name: str
    short_desc: str
    long_desc: str
    release_date: str | None
    developers: list[str]
    publishers: list[str]
    genres: list[str]
    tags: list[str]
    metacritic_score: int | None
    price: Price | None
    platforms: list[str]
    is_free: bool
    header_image: str
    screenshots: list[str]
    website: str | None
    requirements: dict[str, SystemRequirements]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Game":
        """Create Game instance from raw API dict.

        This method provides backward compatibility with code using raw dicts.

        Args:
            data: Raw game data dictionary from API

        Returns:
            Game instance with typed fields
        """
        # Parse price
        price_data = data.get("price")
        price = (
            Price(
                initial=price_data.get("initial"),
                final=price_data.get("final"),
                discount_percent=price_data.get("discount_percent", 0),
                currency=price_data.get("currency", "USD"),
            )
            if price_data and isinstance(price_data, dict)
            else None
        )

        # Parse requirements
        reqs_data = data.get("requirements", {})
        requirements = {}
        for level in ["minimum", "recommended"]:
            if level in reqs_data and isinstance(reqs_data[level], dict):
                level_reqs = reqs_data[level].get("parsed", {})
                requirements[level] = SystemRequirements(
                    os=level_reqs.get("os", ""),
                    processor=level_reqs.get("processor", ""),
                    memory=level_reqs.get("memory", ""),
                    graphics=level_reqs.get("graphics", ""),
                    directx=level_reqs.get("directx", ""),
                    storage=level_reqs.get("storage", ""),
                )

        return cls(
            app_id=data["app_id"],
            name=data["name"],
            short_desc=data.get("short_desc", ""),
            long_desc=data.get("long_desc", ""),
            release_date=data.get("release_date"),
            developers=data.get("developers", []),
            publishers=data.get("publishers", []),
            genres=data.get("genres", []),
            tags=data.get("tags", []),
            metacritic_score=data.get("metacritic_score"),
            price=price,
            platforms=data.get("platforms", []),
            is_free=data.get("is_free", False),
            header_image=data.get("header_image", ""),
            screenshots=data.get("screenshots", []),
            website=data.get("website"),
            requirements=requirements,
        )


@dataclass(frozen=True)
class SearchResult:
    """Simplified game information from search results.

    Used for search results where full details aren't loaded yet.

    Attributes:
        app_id: Steam App ID
        name: Game title
        short_desc: Short description
        price: Price information or None
        platforms: List of supported platforms
        metacritic_score: Metacritic score or None
        review_score: Steam user review score or None
    """

    app_id: int
    name: str
    short_desc: str
    price: Price | None
    platforms: list[str]
    metacritic_score: int | None
    review_score: int | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResult":
        """Create SearchResult instance from raw API dict.

        Args:
            data: Raw search result dictionary from API

        Returns:
            SearchResult instance with typed fields
        """
        # Parse price
        price_data = data.get("price")
        price = (
            Price(
                initial=price_data.get("initial"),
                final=price_data.get("final"),
                discount_percent=price_data.get("discount_percent", 0),
                currency=price_data.get("currency", "USD"),
            )
            if price_data and isinstance(price_data, dict)
            else None
        )

        return cls(
            app_id=data["app_id"],
            name=data["name"],
            short_desc=data.get("short_desc", ""),
            price=price,
            platforms=data.get("platforms", []),
            metacritic_score=data.get("metacritic", {}).get("score"),
            review_score=data.get("review_score"),
        )


# Type aliases for backward compatibility
GameDict = dict[str, Any]
SearchResultDict = dict[str, Any]
