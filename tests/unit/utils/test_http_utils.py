"""Unit tests for HTTP retry helper."""

from unittest.mock import MagicMock, patch

import pytest
import requests
import responses

from src.utils.http_utils import _retry_after_seconds, safe_requests


class TestRetryAfterSeconds:
    def test_uses_retry_after_header_when_present(self):
        """Prefers numeric Retry-After over exponential backoff."""
        resp = MagicMock()
        resp.headers = {"Retry-After": "30"}

        assert _retry_after_seconds(resp, backoff=1.0, attempt=1) == 30.0

    def test_exponential_backoff_when_no_retry_after(self):
        """Doubles backoff base by attempt when Retry-After is absent."""
        resp = MagicMock()
        resp.headers = {}

        assert _retry_after_seconds(resp, backoff=1.0, attempt=1) == 1.0
        assert _retry_after_seconds(resp, backoff=1.0, attempt=2) == 2.0
        assert _retry_after_seconds(resp, backoff=1.0, attempt=3) == 4.0


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


@responses.activate
@patch("src.utils.http_utils.time.sleep")
def test_safe_requests_retries_429_then_succeeds(mock_sleep):
    """Retries on 429 with exponential backoff until success."""
    url = "https://api.spotify.com/v1/artists/abc"
    responses.add(responses.GET, url, status=429, headers={"Retry-After": "0"})
    responses.add(responses.GET, url, status=429, headers={"Retry-After": "0"})
    responses.add(
        responses.GET,
        url,
        json={"id": "abc", "name": "Artist", "followers": {"total": 1}, "popularity": 50},
        status=200,
    )

    resp = safe_requests(
        "GET",
        url,
        rate_limit_max_retries=5,
        backoff=1.0,
        headers={"Authorization": "Bearer x"},
    )

    assert resp.status_code == 200
    assert len(responses.calls) == 3
    assert mock_sleep.call_count == 2


@responses.activate
@patch("src.utils.http_utils.time.sleep")
def test_safe_requests_stops_after_rate_limit_retries(mock_sleep):
    """Raises after ``rate_limit_max_retries`` consecutive 429 responses."""
    url = "https://api.spotify.com/v1/artists/fail"
    for _ in range(6):
        responses.add(responses.GET, url, status=429)

    with pytest.raises(requests.HTTPError) as exc_info:
        safe_requests("GET", url, rate_limit_max_retries=5, backoff=0.01)

    assert exc_info.value.response.status_code == 429
    assert len(responses.calls) == 6
    assert mock_sleep.call_count == 5


@responses.activate
@patch("src.utils.http_utils.time.sleep")
def test_safe_requests_429_exponential_backoff_without_retry_after(mock_sleep):
    """429 retries use exponential backoff when Retry-After header is missing."""
    url = "https://api.spotify.com/v1/artists/backoff"
    responses.add(responses.GET, url, status=429)
    responses.add(responses.GET, url, status=429)
    responses.add(responses.GET, url, json={"ok": True}, status=200)

    resp = safe_requests("GET", url, rate_limit_max_retries=5, backoff=2.0)

    assert resp.status_code == 200
    assert mock_sleep.call_args_list[0].args == (2.0,)
    assert mock_sleep.call_args_list[1].args == (4.0,)


@responses.activate
@patch("src.utils.http_utils.time.sleep")
def test_safe_requests_429_does_not_consume_generic_retry_budget(mock_sleep):
    """Persistent 429 fails after rate-limit retries only (not max_retries loops)."""
    url = "https://example.com/rate-capped"
    for _ in range(10):
        responses.add(responses.GET, url, status=429)

    with pytest.raises(requests.HTTPError):
        safe_requests("GET", url, max_retries=3, rate_limit_max_retries=5, backoff=0.01)

    assert len(responses.calls) == 6
