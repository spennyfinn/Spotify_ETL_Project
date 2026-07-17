"""Shared pytest fixtures for the music streaming pipeline."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_write_pandas():
    """Patch Snowflake write_pandas to simulate a successful append."""
    with patch("src.load.snowflake_loader.write_pandas") as mock_wp:
        mock_wp.return_value = (None, None, 1, None)
        yield mock_wp


@pytest.fixture
def mock_get_snowflake_connection():
    """Patch get_snowflake_connection so unit tests never open a real session."""
    with patch(
        "src.load.snowflake_loader.get_snowflake_connection",
        return_value=MagicMock(),
    ) as mock_get_conn:
        yield mock_get_conn


@pytest.fixture
def mock_snowflake_write(mock_write_pandas):
    """Alias used by loader tests."""
    return mock_write_pandas


@pytest.fixture
def mock_snowflake_connection(mock_get_snowflake_connection):
    """Alias used by loader tests."""
    return mock_get_snowflake_connection


@pytest.fixture
def snowflake_context_manager():
    """Reusable snowflake_connection() context mock for extractor main() tests."""
    mock_conn = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx
