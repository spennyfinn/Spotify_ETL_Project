"""Unit tests for audio feature extraction (Librosa path mocked)."""

from unittest.mock import patch

import pytest

from src.extract.audio_features_extractor import (
    _build_feature_record,
    _get_preview_url,
    get_audio_features,
)
from src.load.snowflake_loader import REQUIRED_TABLE_FIELDS


class TestBuildFeatureRecord:
    def test_includes_all_loader_required_fields(self):
        """Feature dict includes every key raw_audio_features validation expects."""
        record = _build_feature_record(
            song_id="song-1",
            preview_url="https://example.com/preview.mp3",
            bpm=120.0,
            energy=0.5,
            spectral_centroid=2000.0,
            zero_crossing_rate=0.1,
            harmonic_ratio=0.6,
            percussive_ratio=0.4,
        )

        required = REQUIRED_TABLE_FIELDS["raw_audio_features"]
        assert required.issubset(record.keys())
        assert record["source"] == "Librosa"
        assert record["song_id"] == "song-1"


class TestGetPreviewUrl:
    def test_returns_url_when_finder_succeeds(self):
        """Returns preview URL when spotify_preview_finder reports success."""
        with patch("src.extract.audio_features_extractor.finder") as mock_finder:
            mock_finder.search_and_get_links.return_value = {
                "success": True,
                "results": [{"previewUrl": "https://p.scdn.co/preview.mp3"}],
            }

            url = _get_preview_url("Blinding Lights", "The Weeknd")

        assert url == "https://p.scdn.co/preview.mp3"

    def test_returns_none_when_no_results(self):
        """Returns None when the finder returns an empty results list."""
        with patch("src.extract.audio_features_extractor.finder") as mock_finder:
            mock_finder.search_and_get_links.return_value = {
                "success": True,
                "results": [],
            }

            assert _get_preview_url("Unknown", "Nobody") is None

    def test_returns_none_when_success_flag_false(self):
        """Returns None when success is False even if a preview URL is present."""
        with patch("src.extract.audio_features_extractor.finder") as mock_finder:
            mock_finder.search_and_get_links.return_value = {
                "success": False,
                "results": [{"previewUrl": "https://p.scdn.co/preview.mp3"}],
            }

            assert _get_preview_url("Song", "Artist") is None


class TestGetAudioFeatures:
    def test_happy_path_with_mocks(self):
        """Full pipeline returns _build_feature_record output when all steps succeed."""
        feature_record = _build_feature_record(
            song_id="song-1",
            preview_url="https://p.scdn.co/preview.mp3",
            bpm=128.0,
            energy=0.4,
            spectral_centroid=1500.0,
            zero_crossing_rate=0.05,
            harmonic_ratio=0.55,
            percussive_ratio=0.45,
        )

        with (
            patch(
                "src.extract.audio_features_extractor._get_preview_url",
                return_value="https://p.scdn.co/preview.mp3",
            ),
            patch(
                "src.extract.audio_features_extractor._load_preview_audio",
                return_value=(object(), 22050),
            ),
            patch(
                "src.extract.audio_features_extractor._extract_bpm",
                return_value=128.0,
            ),
            patch(
                "src.extract.audio_features_extractor._extract_energy",
                return_value=0.4,
            ),
            patch(
                "src.extract.audio_features_extractor._extract_spectral_centroid",
                return_value=1500.0,
            ),
            patch(
                "src.extract.audio_features_extractor._extract_zero_crossing_rate",
                return_value=0.05,
            ),
            patch(
                "src.extract.audio_features_extractor._extract_harmonic_percussive_ratios",
                return_value=(0.55, 0.45),
            ),
        ):
            result = get_audio_features("Blinding Lights", "The Weeknd", "song-1")

        assert result == feature_record

    def test_returns_none_when_preview_missing(self):
        """Stops early with None when no Spotify preview URL is found."""
        with patch(
            "src.extract.audio_features_extractor._get_preview_url",
            return_value=None,
        ):
            assert get_audio_features("Song", "Artist", "id-1") is None

    def test_returns_none_when_bpm_extraction_fails(self):
        """Stops with None when Librosa BPM step fails after audio is loaded."""
        with (
            patch(
                "src.extract.audio_features_extractor._get_preview_url",
                return_value="https://p.scdn.co/preview.mp3",
            ),
            patch(
                "src.extract.audio_features_extractor._load_preview_audio",
                return_value=(object(), 22050),
            ),
            patch(
                "src.extract.audio_features_extractor._extract_bpm",
                return_value=None,
            ),
        ):
            assert get_audio_features("Song", "Artist", "id-1") is None
