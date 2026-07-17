"""Unit tests for Spotify extract helpers and batch search."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.extract.spotify_artist_extractor import extract_spotify_artist_metrics
from src.extract.spotify_track_extractor import extract_batch_spotify_data
from src.utils.spotify_api_utils import extract_spotify_data


def _spotify_track_item(
    *,
    track_id="track-1",
    track_name="Blinding Lights",
    artist_id="artist-1",
    artist_name="The Weeknd",
):
    return {
        "id": track_id,
        "name": track_name,
        "duration_ms": 200_040,
        "explicit": False,
        "popularity": 95,
        "track_number": 1,
        "is_playable": True,
        "type": "track",
        "artists": [{"id": artist_id, "name": artist_name}],
        "album": {
            "id": "album-1",
            "name": "After Hours",
            "album_type": "album",
            "release_date": "2020-03-20",
            "release_date_precision": "day",
            "total_tracks": 14,
        },
    }


SPOTIFY_SEARCH_BODY = {"tracks": {"items": [_spotify_track_item()]}}


class TestExtractSpotifyData:
    def test_maps_api_json_to_loader_fields(self):
        """Maps Spotify search API JSON to dict keys required by raw_spotify_tracks."""
        rows = extract_spotify_data(SPOTIFY_SEARCH_BODY)

        assert len(rows) == 1
        row = rows[0]
        assert row["song_id"] == "track-1"
        assert row["name"] == "Blinding Lights"
        assert row["artist_id"] == "artist-1"
        assert row["duration_ms"] == 200_040
        assert row["source"] == "Spotify"

    def test_skips_items_missing_album_or_artist(self):
        """Skips tracks missing album or artists block entirely."""
        body = {
            "tracks": {
                "items": [
                    {"id": "x", "name": "No Album", "artists": [{"id": "a", "name": "A"}]},
                    {"id": "y", "name": "No Artist", "album": {"id": "b", "name": "B"}},
                ]
            }
        }

        assert extract_spotify_data(body) == []

    def test_skips_track_when_artists_list_empty(self):
        """Skips tracks whose artists array is empty (no primary artist)."""
        body = {
            "tracks": {
                "items": [
                    {
                        "id": "x",
                        "name": "Lonely Track",
                        "artists": [],
                        "album": {"id": "a", "name": "Album"},
                    }
                ]
            }
        }

        assert extract_spotify_data(body) == []


class TestExtractBatchSpotifyData:
    @patch("src.extract.spotify_track_extractor.time.sleep")
    @patch("src.extract.spotify_track_extractor.random.uniform", return_value=0)
    @patch("src.extract.spotify_track_extractor.get_spotify_token", return_value="token")
    @patch("src.extract.spotify_track_extractor.safe_requests")
    def test_collects_tracks_from_search_pages(
        self, mock_safe_requests, _mock_token, _mock_uniform, _mock_sleep
    ):
        """Paginates offsets 0/50/100/150 and aggregates tracks from each page."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = SPOTIFY_SEARCH_BODY
        mock_safe_requests.return_value = mock_resp

        data = extract_batch_spotify_data(["blinding"])

        assert len(data) == 4  # offsets 0, 50, 100, 150
        assert all(row["source"] == "Spotify" for row in data)
        assert mock_safe_requests.call_count == 4

    @patch("src.extract.spotify_track_extractor.time.sleep")
    @patch("src.extract.spotify_track_extractor.random.uniform", return_value=0)
    @patch("src.extract.spotify_track_extractor.get_spotify_token", return_value="token")
    @patch("src.extract.spotify_track_extractor.safe_requests", return_value=None)
    def test_continues_when_request_fails(
        self, _mock_safe_requests, _mock_token, _mock_uniform, _mock_sleep
    ):
        """Returns empty list when all paginated requests fail (no exception)."""
        assert extract_batch_spotify_data(["query"]) == []

    @patch("src.extract.spotify_track_extractor.time.sleep")
    @patch("src.extract.spotify_track_extractor.random.uniform", return_value=0)
    @patch("src.extract.spotify_track_extractor.get_spotify_token", return_value="token")
    @patch("src.extract.spotify_track_extractor.safe_requests")
    def test_skips_malformed_json_response(
        self, mock_safe_requests, _mock_token, _mock_uniform, _mock_sleep
    ):
        """Continues batch when response.json raises JSONDecodeError."""
        mock_resp = MagicMock()
        mock_resp.json.side_effect = json.JSONDecodeError("bad json", "doc", 0)
        mock_safe_requests.return_value = mock_resp

        assert extract_batch_spotify_data(["query"]) == []


class TestExtractSpotifyArtistMetrics:
    @patch("src.extract.spotify_artist_extractor.get_spotify_token", return_value="token")
    @patch("src.extract.spotify_artist_extractor.safe_requests")
    def test_parses_artist_payload(self, mock_safe_requests, _mock_token):
        """Maps artist API JSON to raw_spotify_artists loader fields."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "id": "artist-1",
            "name": "The Weeknd",
            "popularity": 95,
            "followers": {"total": 50_000_000},
            "genres": ["canadian pop"],
        }
        mock_safe_requests.return_value = mock_resp

        result = extract_spotify_artist_metrics("artist-1", "The Weeknd")

        assert result is not None
        assert result["artist_id"] == "artist-1"
        assert result["artist_name"] == "The Weeknd"
        assert result["follower_count"] == 50_000_000
        assert result["source"] == "Spotify"
        mock_safe_requests.assert_called_once_with(
            "GET",
            "https://api.spotify.com/v1/artists/artist-1",
            timeout=5,
            headers={"Authorization": "Bearer token"},
            rate_limit_max_retries=5,
            backoff=1.0,
        )

    @patch("src.extract.spotify_artist_extractor.get_spotify_token", return_value="token")
    @patch("src.extract.spotify_artist_extractor.safe_requests", return_value=None)
    def test_returns_none_without_response(self, _mock_safe_requests, _mock_token):
        """Returns None when safe_requests yields no response."""
        assert extract_spotify_artist_metrics("artist-1", "The Weeknd") is None

    @patch("src.extract.spotify_artist_extractor.get_spotify_token", return_value="token")
    @patch("src.extract.spotify_artist_extractor.safe_requests")
    def test_returns_none_when_rate_limit_exhausted(self, mock_safe_requests, _mock_token):
        """Returns None when safe_requests raises HTTP 429 after all retries."""
        response = MagicMock()
        response.status_code = 429
        mock_safe_requests.side_effect = requests.HTTPError(
            "429 Client Error",
            response=response,
        )

        assert extract_spotify_artist_metrics("artist-1", "The Weeknd") is None
        mock_safe_requests.assert_called_once()
        assert mock_safe_requests.call_args.kwargs["rate_limit_max_retries"] == 5
