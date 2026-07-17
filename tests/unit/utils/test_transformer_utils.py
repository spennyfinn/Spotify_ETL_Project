"""Unit tests for legacy transform helper utilities."""

import pytest

from src.utils.transformer_utils import (
    determine_missing_fields,
    safe_float,
    safe_int,
    safe_string,
)


class TestSafeInt:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("42", 42),
            ("42.9", 42),
            ("", None),
            (None, None),
            ("not-a-number", None),
        ],
    )
    def test_safe_int(self, value, expected):
        """Parses numeric strings to int; empty/invalid values return default None."""
        assert safe_int(value) == expected


class TestSafeFloat:
    def test_safe_float_parses_numeric_string(self):
        """Parses a numeric string to float."""
        assert safe_float("3.14") == pytest.approx(3.14)

    def test_safe_float_empty_returns_default(self):
        """Empty string returns the default 0.0."""
        assert safe_float("") == 0.0


class TestSafeString:
    def test_strips_and_lowercases(self):
        """Strips whitespace and optionally lowercases string values."""
        assert safe_string("  Hello  ", lowercase=True) == "hello"

    def test_blank_returns_none(self):
        """Whitespace-only strings return None."""
        assert safe_string("   ") is None


class TestDetermineMissingFields:
    def test_logs_missing_none_values(self, caplog):
        """Logs debug message listing keys whose values are None."""
        import logging

        caplog.set_level(logging.DEBUG)
        determine_missing_fields({"a": 1, "b": None})
        assert "Missing fields" in caplog.text
