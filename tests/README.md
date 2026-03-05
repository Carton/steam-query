# Testing

## Running Tests

### Install Test Dependencies

```bash
# Using uv
uv sync --group dev

# Or using pip
pip install -e ".[dev]"
```

### Run All Tests

```bash
# Using uv
uv run pytest

# Using pip
pytest
```

### Run Specific Test File

```bash
# Using uv
uv run pytest tests/test_steam_client.py

# Using pip
pytest tests/test_steam_client.py
```

### Run with Coverage

```bash
# Install coverage
uv add --dev pytest-cov

# Run tests with coverage
uv run pytest --cov=steam_query --cov-report=html
```

### Run with Verbose Output

```bash
uv run pytest -v
```

### Run Specific Test

```bash
# Run a specific test function
uv run pytest tests/test_steam_client.py::TestParseDate::test_parse_date_valid_format
```

### Debug Failed Tests

```bash
# Show print statements
uv run pytest -s

# Stop on first failure
uv run pytest -x

# Drop into debugger on failure
uv run pytest --pdb
```

## Test Structure

```
tests/
├── __init__.py           # Test package marker
├── conftest.py           # Shared fixtures and configuration
├── test_steam_client.py  # Tests for SteamStoreClient
└── test_cli.py           # Tests for CLI commands
```

## Test Coverage

Current test coverage includes:

- **Configuration**: Country code detection from environment and config file
- **Currency handling**: Decimal vs non-decimal currency formatting
- **Date parsing**: Various date formats from Steam API
- **Price processing**: Conversion from cents, discount calculation
- **API calls**: Search and lookup with mocked responses
- **CLI formatting**: Game info display, JSON output
- **Error handling**: API failures, not found cases

## Writing New Tests

When adding new features, follow these patterns:

```python
"""Tests for new_feature.py."""

import pytest
from unittest.mock import AsyncMock, patch

from steam_query.new_feature import NewFeature


class TestNewFeature:
    """Tests for NewFeature class."""

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return {"key": "value"}

    def test_basic_functionality(self, sample_data):
        """Test basic functionality."""
        feature = NewFeature()
        result = feature.process(sample_data)
        assert result == "expected"

    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async methods."""
        feature = NewFeature()
        with patch.object(feature, "api_call", return_value={"data": "test"}):
            result = await feature.fetch_data()
            assert result is not None
```

## Mocking External APIs

All tests use mocking to avoid calling the real Steam API:

```python
with patch.object(client, "_get", return_value=mock_response):
    result = await client.get_app_details(12345)
    assert result is not None
```

This ensures:
- ✅ Fast test execution
- ✅ No network dependency
- ✅ Deterministic results
- ✅ No API rate limits
