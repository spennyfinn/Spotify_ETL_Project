"""Unit tests for Snowflake connection helpers (no live Snowflake)."""

from unittest.mock import MagicMock, patch

from src.utils.snowflake_utils import fetch_all


def test_fetch_all_with_passed_cursor():
    """Reuses an existing cursor and does not close it (caller owns lifecycle)."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("song-1", "Artist")]

    rows = fetch_all("SELECT 1", cur=mock_cursor, params={"id": "x"})

    assert rows == [("song-1", "Artist")]
    mock_cursor.execute.assert_called_once_with("SELECT 1", {"id": "x"})
    mock_cursor.close.assert_not_called()


def test_fetch_all_opens_short_lived_cursor():
    """Opens snowflake_cursor context, runs query, and exits context when cur is omitted."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [(1, 2, 3)]
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_cursor)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("src.utils.snowflake_utils.snowflake_cursor", return_value=mock_ctx):
        rows = fetch_all("SELECT * FROM t")

    assert rows == [(1, 2, 3)]
    mock_cursor.execute.assert_called_once_with("SELECT * FROM t", {})
    mock_ctx.__enter__.assert_called_once()
    mock_ctx.__exit__.assert_called_once()
