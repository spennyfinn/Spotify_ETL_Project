"""Unit tests for Last.fm matching and enrichment logic."""

import json
from unittest.mock import patch

import pytest
import responses

from src.extract.lastfm_extractor import (
    LASTFM_API_URL,
    _build_track_match,
    _is_valid_match,
    _lastfm_get,
    get_track_from_lastfm,
    match_artists_from_lastfm,
    process_last_fm_data,
)

API_KEY = "test-lastfm-key"


class TestIsValidMatch:
    @pytest.mark.parametrize(
        "track_name,matched_artist,listeners,expected",
        [
            ("blinding lights", "the weeknd", 100, True),
            ("blinding lights", "the weeknd", 5, False),
            ("blinding lights", "unknown", 100, False),
            ("", "the weeknd", 100, False),
        ],
        ids=["valid", "too_few_listeners", "unknown_artist", "empty_track"],
    )
    def test_is_valid_match(self, track_name, matched_artist, listeners, expected):
        """Threshold rules: min listeners, non-unknown artist, non-empty track name."""
        assert _is_valid_match(
            "blinding lights",
            "the weeknd",
            track_name,
            matched_artist,
            listeners,
        ) is expected

    def test_rejects_low_similarity(self):
        """Rejects candidates when song/artist similarity scores are below cutoffs."""
        assert _is_valid_match(
            "blinding lights",
            "the weeknd",
            "completely different song",
            "another artist",
            500,
        ) is False


class TestBuildTrackMatch:
    def test_preserves_spotify_ids_and_original_names(self):
        """Match dict keeps Spotify ids and original names for downstream loader/dbt."""
        match = _build_track_match(
            song_name="Blinding Lights",
            artist_name="The Weeknd",
            song_id="spotify-track-1",
            artist_id="spotify-artist-1",
            track_name="Blinding Lights",
            matched_artist_name="The Weeknd",
            listeners=1234,
        )

        assert match["song_id"] == "spotify-track-1"
        assert match["artist_id"] == "spotify-artist-1"
        assert match["original_song_name"] == "Blinding Lights"
        assert match["original_artist_name"] == "The Weeknd"
        assert match["listeners"] == 1234


class TestLastfmGet:
    @responses.activate
    def test_returns_none_on_http_error(self):
        """HTTP 5xx from Last.fm returns None (no exception to caller)."""
        responses.add(responses.GET, LASTFM_API_URL, status=503)

        assert _lastfm_get({"method": "track.getInfo"}, API_KEY) is None

    @responses.activate
    def test_returns_none_when_api_error_field_present(self):
        """JSON body with top-level error field is treated as not found."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={"error": 6, "message": "Track not found"},
        )

        assert _lastfm_get({"method": "track.getInfo"}, API_KEY) is None

    @responses.activate
    def test_includes_api_key_in_query(self):
        """Every request includes api_key and format=json query params."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={"track": {"name": "x", "listeners": "10", "artist": {"name": "y"}}},
        )

        _lastfm_get({"method": "track.getInfo", "track": "x", "artist": "y"}, API_KEY)

        assert responses.calls[0].request.params["api_key"] == API_KEY


class TestGetTrackFromLastfm:
    @responses.activate
    def test_uses_track_get_info_when_valid(self):
        """Primary path: track.getInfo succeeds with one API call."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "track": {
                    "name": "Blinding Lights",
                    "listeners": "1500",
                    "artist": {"name": "The Weeknd"},
                }
            },
        )

        match = get_track_from_lastfm(
            "Blinding Lights",
            "The Weeknd",
            "song-1",
            "artist-1",
            API_KEY,
        )

        assert match is not None
        assert match["song_id"] == "song-1"
        assert match["listeners"] == 1500
        assert len(responses.calls) == 1

    @responses.activate
    @patch("src.extract.lastfm_extractor.time.sleep")
    def test_falls_back_to_track_search(self, _mock_sleep):
        """When getInfo fails, falls back to track.search."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={"error": 6, "message": "Track not found"},
        )
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "results": {
                    "trackmatches": {
                        "track": {
                            "name": "Blinding Lights",
                            "artist": "The Weeknd",
                            "listeners": "2000",
                        }
                    }
                }
            },
        )

        match = get_track_from_lastfm(
            "Blinding Lights",
            "The Weeknd",
            "song-1",
            "artist-1",
            API_KEY,
        )

        assert match is not None
        assert match["listeners"] == 2000
        assert len(responses.calls) == 2

    @responses.activate
    @patch("src.extract.lastfm_extractor.time.sleep")
    def test_search_picks_higher_scoring_candidate(self, _mock_sleep):
        """Among valid search hits, selects the best combined similarity score."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={"error": 6, "message": "Track not found"},
        )
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "results": {
                    "trackmatches": {
                        "track": [
                            {
                                "name": "Blinding Lights (Remix)",
                                "artist": "The Weeknd",
                                "listeners": "5000",
                            },
                            {
                                "name": "Blinding Lights",
                                "artist": "The Weeknd",
                                "listeners": "8000",
                            },
                        ]
                    }
                }
            },
        )

        match = get_track_from_lastfm(
            "Blinding Lights",
            "The Weeknd",
            "song-1",
            "artist-1",
            API_KEY,
        )

        assert match is not None
        assert match["listeners"] == 8000

    @responses.activate
    def test_get_info_accepts_string_artist_block(self):
        """When artist is a string (not dict), falls back to Spotify artist name."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "track": {
                    "name": "Blinding Lights",
                    "listeners": "1500",
                    "artist": "The Weeknd",
                }
            },
        )

        match = get_track_from_lastfm(
            "Blinding Lights",
            "The Weeknd",
            "song-1",
            "artist-1",
            API_KEY,
        )

        assert match is not None
        assert match["listeners"] == 1500


class TestMatchArtistsFromLastfm:
    @responses.activate
    def test_adds_artist_stats_and_source(self):
        """artist.getInfo adds mbid, tour flag, listener stats, and source=Lastfm."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "artist": {
                    "name": "The Weeknd",
                    "mbid": "mbid-123",
                    "ontour": "0",
                    "stats": {"listeners": "5000000", "playcount": "90000000"},
                }
            },
        )

        track_data = {
            "song_id": "song-1",
            "artist_id": "artist-1",
            "original_artist_name": "The Weeknd",
            "listeners": 1000,
        }

        result = match_artists_from_lastfm(track_data, API_KEY)

        assert result is not None
        assert result["source"] == "Lastfm"
        assert result["mbid"] == "mbid-123"
        assert result["artist_listeners"] == 5_000_000
        assert result["artist_playcount"] == 90_000_000

    @responses.activate
    def test_rejects_low_artist_similarity(self):
        """Artist enrichment fails when Last.fm name similarity to Spotify is below 0.9."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "artist": {
                    "name": "Totally Different Person",
                    "stats": {"listeners": "1", "playcount": "1"},
                }
            },
        )

        track_data = {
            "original_artist_name": "The Weeknd",
            "listeners": 100,
        }

        assert match_artists_from_lastfm(track_data, API_KEY) is None

    def test_returns_none_without_original_artist_name(self):
        """Cannot call artist.getInfo without original_artist_name on track_data."""
        assert match_artists_from_lastfm({"listeners": 10}, API_KEY) is None


class TestProcessLastFmData:
    @responses.activate
    @patch("src.extract.lastfm_extractor.time.sleep")
    def test_returns_complete_record(self, _mock_sleep):
        """Happy path: track match + artist enrichment returns loader-ready dict."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "track": {
                    "name": "Blinding Lights",
                    "listeners": "1500",
                    "artist": {"name": "The Weeknd"},
                }
            },
        )
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "artist": {
                    "name": "The Weeknd",
                    "mbid": "mbid-123",
                    "ontour": "0",
                    "stats": {"listeners": "5000000", "playcount": "90000000"},
                }
            },
        )

        result = process_last_fm_data(
            "Blinding Lights",
            "The Weeknd",
            "song-1",
            "artist-1",
            API_KEY,
        )

        assert result is not None
        assert result["source"] == "Lastfm"
        assert result["song_id"] == "song-1"
        assert result["artist_playcount"] == 90_000_000

    @responses.activate
    def test_returns_none_when_track_lookup_fails(self):
        """Returns None when both getInfo and search produce no valid match."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            body=json.dumps({"error": 6, "message": "not found"}),
        )
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={"results": {"trackmatches": {"track": []}}},
        )

        assert (
            process_last_fm_data(
                "Blinding Lights",
                "The Weeknd",
                "song-1",
                "artist-1",
                API_KEY,
            )
            is None
        )

    @responses.activate
    def test_returns_none_when_artist_enrichment_fails(self):
        """Returns None when track matches but artist.getInfo fails validation."""
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={
                "track": {
                    "name": "Blinding Lights",
                    "listeners": "1500",
                    "artist": {"name": "The Weeknd"},
                }
            },
        )
        responses.add(
            responses.GET,
            LASTFM_API_URL,
            json={"error": 6, "message": "Artist not found"},
        )

        assert (
            process_last_fm_data(
                "Blinding Lights",
                "The Weeknd",
                "song-1",
                "artist-1",
                API_KEY,
            )
            is None
        )
