"""Unit tests for HTTP retry helper."""

from unittest.mock import patch

import pytest
import requests
import responses

from src.utils.http_utils import safe_requests


@responses.activate
def test_safe_requests_success_first_try():
    """Returns the response immediately when the first HTTP call succeeds."""
    responses.add(responses.GET, "https://example.com/data", json={"ok": True}, status=200)

    resp = safe_requests("GET", "https://example.com/data")

    assert resp.json()["ok"] is True
    assert len(responses.calls) == 1


@responses.activate
@patch("src.utils.http_utils.time.sleep")
def test_safe_requests_retries_then_succeeds(mock_sleep):
    """Retries with backoff after transient failures, then returns success."""
    responses.add(responses.GET, "https://example.com/retry", status=500)
    responses.add(responses.GET, "https://example.com/retry", status=500)
    responses.add(responses.GET, "https://example.com/retry", json={"ok": True}, status=200)

    resp = safe_requests("GET", "https://example.com/retry", max_retries=3, backoff=0.01)

    assert resp.json()["ok"] is True
    assert len(responses.calls) == 3
    assert mock_sleep.call_count == 2


@responses.activate
@patch("src.utils.http_utils.time.sleep")
def test_safe_requests_raises_after_max_retries(mock_sleep):
    """Raises the last HTTPError when all retry attempts fail."""
    for _ in range(3):
        responses.add(responses.GET, "https://example.com/fail", status=503)

    with pytest.raises(requests.HTTPError):
        safe_requests("GET", "https://example.com/fail", max_retries=3, backoff=0.01)

    assert len(responses.calls) == 3
    assert mock_sleep.call_count == 2
