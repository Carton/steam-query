"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiohttp import ClientSession


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session."""
    session = MagicMock(spec=ClientSession)
    return session


@pytest.fixture
def sample_game_data():
    """Sample game data from Steam API."""
    return {
        "1245620": {
            "success": True,
            "data": {
                "steam_appid": 1245620,
                "name": "ELDEN RING",
                "short_description": "A new action RPG",
                "detailed_description": "FromSoftware Inc. action RPG",
                "release_date": {
                    "date": "Feb 25, 2022",
                    "coming_soon": False
                },
                "developers": [
                    {"name": "FromSoftware Inc."}
                ],
                "publishers": [
                    {"name": "BANDAI NAMCO Entertainment Inc."}
                ],
                "genres": [
                    {"description": "Action RPG"},
                    {"description": "Adventure"}
                ],
                "tags": [
                    {"tag": "Souls-like"},
                    {"tag": "Challenging"}
                ],
                "metacritic": {"score": 96},
                "price_overview": {
                    "currency": "USD",
                    "initial": 5999,
                    "final": 5999,
                    "discount_percent": 0
                },
                "platforms": {
                    "windows": True,
                    "mac": False,
                    "linux": False
                },
                "is_free": False,
                "header_image": "https://example.com/header.jpg",
                "screenshots": [
                    {"path_thumbnail": "https://example.com/screen1.jpg"}
                ],
                "website": "https://www.eldenring.com/",
                "pc_requirements": {
                    "minimum": {
                        "english": "OS: Windows 10\nProcessor: i5-8400\nMemory: 12 GB"
                    },
                    "recommended": {
                        "english": "OS: Windows 11\nProcessor: i7-8700K\nMemory: 16 GB"
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_search_results():
    """Sample search results from Steam API."""
    return {
        "total": 2,
        "items": [
            {
                "id": 1245620,
                "name": "ELDEN RING",
                "short_description": "A new action RPG",
                "price": {
                    "currency": "USD",
                    "initial": 5999,
                    "final": 5999,
                    "discount_percent": 0
                },
                "platforms": ["windows"],
                "metacritic": {"score": 96},
                "review_score": 9
            },
            {
                "id": 1091500,
                "name": "Cyberpunk 2077",
                "short_description": "Open world action adventure",
                "price": {
                    "currency": "USD",
                    "initial": 5999,
                    "final": 2999,
                    "discount_percent": 50
                },
                "platforms": ["windows"],
                "metacritic": {"score": 86},
                "review_score": 7
            }
        ]
    }
