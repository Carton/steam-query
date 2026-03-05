"""Steam Store API Client - Query any game

No login required, can query any game on the Steam store directly
"""

import asyncio
import logging
import re
import json
from typing import Any, Optional
from datetime import datetime

import aiohttp
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)


class SteamStoreClient:
    """Steam Store API Client

    Query any game on the Steam store without user login
    """

    def __init__(self, requests_per_second: float = 1.0):
        """Initialize client

        Args:
            requests_per_second: Request rate limit (default 1 req/sec)
        """
        self.requests_per_second = requests_per_second
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()

    @sleep_and_retry
    @limits(calls=1, period=1)  # 1 req/sec
    async def _get(
        self, url: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """HTTP GET request (with rate limiting)"""
        if not self._session:
            raise RuntimeError("Client not initialized, please use async with")

        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unknown error: {e}")
            raise

    async def search_games_by_name(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search games by name

        Uses Steam store search functionality

        Args:
            query: Search keyword
            limit: Number of results to return

        Returns:
            List of games with app_id and name
        """
        logger.info(f"Searching for game: {query}")

        # Steam store search API (unofficial but stable)
        url = "https://store.steampowered.com/api/storesearch/"
        params = {
            "term": query,
            "l": "english",
            "cc": "US",
            "category1": "998",  # Games
        }

        try:
            data = await self._get(url, params)

            if data.get("total", 0) > 0:
                items = data.get("items", [])[:limit]
                results = []

                for item in items:
                    # Process price data - convert from cents to dollars
                    price_data = item.get("price")
                    if price_data and isinstance(price_data, dict):
                        price_data = {
                            "initial": price_data.get("initial", 0) / 100 if price_data.get("initial") else None,
                            "final": price_data.get("final", 0) / 100 if price_data.get("final") else None,
                            "discount_percent": price_data.get("discount_percent", 0),
                            "currency": price_data.get("currency", "USD"),
                        }

                    results.append({
                        "app_id": item.get("id"),
                        "name": item.get("name"),
                        "short_desc": item.get("short_description"),
                        "price": price_data,
                        "platforms": item.get("platforms", []),
                        "metacritic": item.get("metacritic"),
                        "review_score": item.get("review_score"),
                    })

                logger.info(f"Found {len(results)} result(s)")
                return results
            else:
                logger.warning(f"No matching games found for: {query}")
                return []

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def get_app_details(self, app_id: int) -> Optional[dict[str, Any]]:
        """Get detailed game information

        Args:
            app_id: Steam App ID

        Returns:
            Dictionary with detailed game information
        """
        logger.debug(f"Getting game details: {app_id}")

        # Steam Store API (no API key required)
        url = "https://store.steampowered.com/api/appdetails"
        params = {"appids": app_id, "l": "english"}

        try:
            data = await self._get(url, params)

            if str(app_id) in data and data[str(app_id)].get("success"):
                app_data = data[str(app_id)]["data"]
                return self._parse_app_details(app_data)

            logger.warning(f"Game {app_id} not found")
            return None

        except Exception as e:
            logger.error(f"Failed to get details (app_id={app_id}): {e}")
            return None

    def _currency_uses_decimals(self, currency: str) -> bool:
        """Check if currency uses decimal units (cents)

        Some currencies like JPY, KRW don't have smaller units
        """
        # Currencies that don't use decimal units
        no_decimal_currencies = {
            "JPY", "KRW", "CLP", "ISK", "BIF", "DJF", "GNF",
            "KHR", "KPW", "LAK", "MGA", "MZN", "RWF", "UGX",
            "VND", "VUV", "XAF", "XOF", "XPF"
        }
        return currency not in no_decimal_currencies

    def _parse_app_details(self, app_data: dict[str, Any]) -> dict[str, Any]:
        """Parse detailed game information

        Args:
            app_data: Raw API data

        Returns:
            Parsed game information
        """
        # Extract release date
        release_date_info = app_data.get("release_date", {})
        release_date = None
        if not release_date_info.get("coming_soon", False):
            date_str = release_date_info.get("date")
            if date_str:
                release_date = self._parse_date(date_str)

        # Extract developers/publishers
        developers = [
            dev.get("name", "")
            for dev in app_data.get("developers", [])
            if isinstance(dev, dict)
        ]
        publishers = [
            pub.get("name", "")
            for pub in app_data.get("publishers", [])
            if isinstance(pub, dict)
        ]

        # Extract genres
        genres = [
            genre.get("description", "")
            for genre in app_data.get("genres", [])
            if isinstance(genre, dict)
        ]

        # Extract tags
        tags = [
            tag.get("tag", "")
            for tag in app_data.get("tags", [])
            if isinstance(tag, dict)
        ]

        # Metacritic score
        metacritic = app_data.get("metacritic", {})
        metacritic_score = metacritic.get("score") if isinstance(metacritic, dict) else None

        # Price information
        # Note: appdetails API returns price in cents for some currencies, but not for others
        # Currencies like JPY, KRW don't use decimal units
        price_overview = app_data.get("price_overview", {})
        price = None
        if isinstance(price_overview, dict) and price_overview.get("initial") is not None:
            currency = price_overview.get("currency", "USD")
            uses_decimals = self._currency_uses_decimals(currency)

            initial = price_overview.get("initial")
            final = price_overview.get("final")

            # Convert to main currency units if using decimals (e.g., cents to dollars)
            if uses_decimals:
                initial = initial / 100 if initial else None
                final = final / 100 if final else None

            price = {
                "initial": initial,
                "final": final,
                "discount_percent": price_overview.get("discount_percent", 0),
                "currency": currency,
            }

        # Supported platforms
        platforms = app_data.get("platforms", False)
        supported_platforms = []
        if isinstance(platforms, dict):
            if platforms.get("windows", False):
                supported_platforms.append("Windows")
            if platforms.get("mac", False):
                supported_platforms.append("Mac")
            if platforms.get("linux", False):
                supported_platforms.append("Linux")

        return {
            "app_id": app_data.get("steam_appid"),
            "name": app_data.get("name"),
            "short_desc": app_data.get("short_description"),
            "long_desc": app_data.get("detailed_description", "")[:500],  # First 500 chars
            "release_date": release_date,
            "developers": developers,
            "publishers": publishers,
            "genres": genres,
            "tags": tags,
            "metacritic_score": metacritic_score,
            "price": price,
            "platforms": supported_platforms,
            "is_free": app_data.get("is_free", False),
            "header_image": app_data.get("header_image"),
            "screenshots": [
                s.get("path_thumbnail", s.get("path", ""))
                for s in app_data.get("screenshots", [])[:5]  # Max 5 screenshots
                if isinstance(s, dict)
            ],
            "website": app_data.get("website"),
            "requirements": self._extract_requirements(app_data),
        }

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string

        Args:
            date_str: Date string

        Returns:
            ISO format date string
        """
        if not date_str:
            return None

        # Try common formats
        formats = ["%d %b, %Y", "%b %d, %Y", "%Y-%m-%d", "%d %b %Y", "%b %d %Y"]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue

        # If all fail, return original string
        return date_str

    def _extract_requirements(self, app_data: dict[str, Any]) -> dict[str, dict[str, str]]:
        """Extract system requirements

        Args:
            app_data: Game data

        Returns:
            System requirements dictionary
        """
        pc_requirements = app_data.get("pc_requirements", {})
        requirements = {}

        if isinstance(pc_requirements, dict):
            for platform in ["minimum", "recommended"]:
                req_data = pc_requirements.get(platform, {})
                if isinstance(req_data, dict):
                    requirements[platform] = {
                        "english": req_data.get("english", ""),
                        "parsed": self._parse_requirements(req_data.get("english", "")),
                    }

        return requirements

    def _parse_requirements(self, req_text: str) -> dict[str, str]:
        """Parse system requirements text

        Args:
            req_text: System requirements text

        Returns:
            Structured requirements dictionary
        """
        requirements = {
            "os": "",
            "processor": "",
            "memory": "",
            "graphics": "",
            "directx": "",
            "storage": "",
        }

        lines = req_text.split("\n")
        current_key = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if it's a new requirement type
            matched = False
            for key in requirements.keys():
                if line.lower().startswith(f"{key}:"):
                    current_key = key
                    requirements[key] = line.split(":", 1)[1].strip()
                    matched = True
                    break

            # If no new key matched and we have a current key, continue the previous requirement
            if not matched and current_key:
                requirements[current_key] += " " + line

        return requirements

    async def get_games_details_batch(
        self, app_ids: list[int]
    ) -> dict[int, dict[str, Any]]:
        """Batch get game details

        Args:
            app_ids: List of Steam App IDs

        Returns:
            Mapping of App IDs to game details
        """
        results = {}

        for app_id in app_ids:
            details = await self.get_app_details(app_id)
            if details:
                results[app_id] = details

        return results
