"""Smoke tests for extractor main() batch loops (Snowflake and APIs mocked)."""

from unittest.mock import MagicMock, patch

import pytest

from src.extract import audio_features_extractor, lastfm_extractor
from src.extract import spotify_track_extractor_snowflake as spotify_seed_main


class TestLastfmExtractorMain:
    @patch("src.extract.lastfm_extractor.load_raw_records", return_value=(1, 0))
    @patch("src.extract.lastfm_extractor.snowflake_connection")
    @patch("src.extract.lastfm_extractor.process_last_fm_data")
    @patch("src.extract.lastfm_extractor.fetch_all")
    @patch("src.extract.lastfm_extractor.os.getenv", return_value="test-key")
    def test_loads_batch_when_matches_exist(
        self,
        _mock_getenv,
        mock_fetch_all,
        mock_process,
        mock_snowflake_conn,
        mock_load,
    ):
        """main() loads matched records into raw_lastfm with the given run_id."""
        mock_fetch_all.return_value = [
            ("artist-1", "song-1", "Blinding Lights", "The Weeknd"),
        ]
        mock_process.return_value = {
            "song_id": "song-1",
            "artist_id": "artist-1",
            "original_song_name": "Blinding Lights",
            "original_artist_name": "The Weeknd",
            "listeners": 100,
            "artist_listeners": 1000,
            "artist_playcount": 2000,
            "source": "Lastfm",
        }
        mock_snowflake_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_snowflake_conn.return_value.__exit__ = MagicMock(return_value=False)

        lastfm_extractor.main(batch_size=5, run_id="run-test")

        mock_load.assert_called_once()
        kwargs = mock_load.call_args.kwargs
        assert kwargs["table"] == "raw_lastfm"
        assert kwargs["run_id"] == "run-test"
        assert len(kwargs["records"]) == 1

    @patch("src.extract.lastfm_extractor.os.getenv", return_value=None)
    def test_raises_when_api_key_missing(self, _mock_getenv):
        """main() raises RuntimeError when LAST_FM_KEY is not in the environment."""
        with pytest.raises(RuntimeError, match="LAST_FM_KEY"):
            lastfm_extractor.main(batch_size=5, run_id="run-test")

    @patch("src.extract.lastfm_extractor.load_raw_records")
    @patch("src.extract.lastfm_extractor.process_last_fm_data", return_value=None)
    @patch("src.extract.lastfm_extractor.fetch_all")
    @patch("src.extract.lastfm_extractor.os.getenv", return_value="test-key")
    def test_skips_load_when_no_matches_in_chunk(
        self, _mock_getenv, mock_fetch_all, _mock_process, mock_load
    ):
        """Does not call load_raw_records when every song in the chunk fails matching."""
        mock_fetch_all.return_value = [
            ("artist-1", "song-1", "Blinding Lights", "The Weeknd"),
        ]

        lastfm_extractor.main(batch_size=5, run_id="run-test")

        mock_load.assert_not_called()


class TestAudioFeaturesExtractorMain:
    @patch("src.extract.audio_features_extractor.load_raw_records", return_value=(1, 0))
    @patch("src.extract.audio_features_extractor.snowflake_connection")
    @patch("src.extract.audio_features_extractor.get_audio_features")
    @patch("src.extract.audio_features_extractor.fetch_all")
    @patch.dict(
        "os.environ",
        {"SPOTIFY_CLIENT_ID": "id", "SPOTIFY_CLIENT_SECRET": "secret"},
        clear=False,
    )
    def test_loads_batch_when_features_exist(
        self,
        mock_fetch_all,
        mock_get_features,
        mock_snowflake_conn,
        mock_load,
    ):
        """main() loads feature dicts into raw_audio_features when extraction succeeds."""
        mock_fetch_all.return_value = [("Blinding Lights", "The Weeknd", "song-1")]
        mock_get_features.return_value = {
            "song_id": "song-1",
            "bpm": 120.0,
            "energy": 0.5,
            "zero_crossing_rate": 0.1,
            "harmonic_ratio": 0.6,
            "percussive_ratio": 0.4,
            "preview_url": "https://example.com/p.mp3",
            "source": "Librosa",
        }
        mock_snowflake_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_snowflake_conn.return_value.__exit__ = MagicMock(return_value=False)

        audio_features_extractor.main(batch_size=5, run_id="run-audio")

        mock_load.assert_called_once()
        kwargs = mock_load.call_args.kwargs
        assert kwargs["table"] == "raw_audio_features"
        assert kwargs["run_id"] == "run-audio"

    @patch("src.extract.audio_features_extractor.fetch_all", return_value=[])
    @patch.dict(
        "os.environ",
        {"SPOTIFY_CLIENT_ID": "id", "SPOTIFY_CLIENT_SECRET": "secret"},
        clear=False,
    )
    def test_exits_when_no_rows(self, mock_fetch_all):
        """Returns early when staging gap query returns no songs."""
        audio_features_extractor.main(batch_size=5, run_id="run-audio")

        mock_fetch_all.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    def test_raises_when_spotify_client_id_missing(self):
        """Raises RuntimeError when SPOTIFY_CLIENT_ID is missing from the environment."""
        with pytest.raises(RuntimeError, match="SPOTIFY_CLIENT"):
            audio_features_extractor.main(batch_size=5, run_id="run-audio")


class TestSpotifyTrackSeedMain:
    @patch("src.extract.spotify_track_extractor_snowflake.load_raw_records", return_value=(2, 0))
    @patch("src.extract.spotify_track_extractor_snowflake.snowflake_connection")
    @patch("src.extract.spotify_track_extractor_snowflake.extract_batch_spotify_data")
    @patch(
        "src.extract.spotify_track_extractor_snowflake.get_words_list",
        return_value=["alpha", "beta", "gamma"],
    )
    def test_loads_extracted_tracks(
        self, _mock_words, mock_extract, mock_snowflake_conn, mock_load
    ):
        """Seed main() batches word-list queries and loads tracks into raw_spotify_tracks."""
        mock_extract.return_value = [
            {"song_id": "s1", "name": "A", "artist_id": "a1", "duration_ms": 1, "source": "Spotify"},
        ]
        mock_snowflake_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_snowflake_conn.return_value.__exit__ = MagicMock(return_value=False)

        spotify_seed_main.main(batch_size=2, start_idx=0, run_id="seed-run")

        mock_load.assert_called()
        assert mock_load.call_args.kwargs["table"] == "raw_spotify_tracks"
        assert mock_load.call_args.kwargs["run_id"] == "seed-run"

    @patch("src.extract.spotify_track_extractor_snowflake.get_words_list", return_value=["a"])
    def test_raises_on_invalid_start_idx(self, _mock_words):
        """Raises ValueError when start_idx is out of range for the words list."""
        with pytest.raises(ValueError, match="start_idx"):
            spotify_seed_main.main(batch_size=1, start_idx=99, run_id="seed-run")

    @patch("src.extract.spotify_track_extractor_snowflake.get_words_list", return_value=[])
    def test_raises_when_words_list_empty(self, _mock_words):
        """Raises RuntimeError when get_words_list returns nothing to query."""
        with pytest.raises(RuntimeError, match="No words list"):
            spotify_seed_main.main(batch_size=1, start_idx=0, run_id="seed-run")


class TestSpotifyArtistExtractorMain:
    @patch("src.extract.spotify_artist_extractor.load_raw_records", return_value=(1, 0))
    @patch("src.extract.spotify_artist_extractor.snowflake_connection")
    @patch("src.extract.spotify_artist_extractor.extract_spotify_artist_metrics")
    @patch("src.extract.spotify_artist_extractor.fetch_all")
    @patch.dict(
        "os.environ",
        {"SPOTIFY_CLIENT_ID": "id", "SPOTIFY_CLIENT_SECRET": "secret"},
        clear=False,
    )
    def test_loads_batch_when_metrics_exist(
        self,
        mock_fetch_all,
        mock_extract,
        mock_snowflake_conn,
        mock_load,
    ):
        """main() loads artist metrics into raw_spotify_artists."""
        from src.extract import spotify_artist_extractor

        mock_fetch_all.return_value = [("artist-1", "The Weeknd")]
        mock_extract.return_value = {
            "artist_id": "artist-1",
            "artist_name": "The Weeknd",
            "follower_count": 1_000,
            "popularity": 90,
            "genres": ["pop"],
            "source": "Spotify",
        }
        mock_snowflake_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_snowflake_conn.return_value.__exit__ = MagicMock(return_value=False)

        spotify_artist_extractor.main(batch_size=5, run_id="artist-run")

        mock_load.assert_called_once()
        kwargs = mock_load.call_args.kwargs
        assert kwargs["table"] == "raw_spotify_artists"
        assert kwargs["run_id"] == "artist-run"
        assert kwargs["id_columns"] == "artist_id"

    @patch("src.extract.spotify_artist_extractor.fetch_all", return_value=[])
    @patch.dict(
        "os.environ",
        {"SPOTIFY_CLIENT_ID": "id", "SPOTIFY_CLIENT_SECRET": "secret"},
        clear=False,
    )
    def test_exits_when_no_gap_rows(self, mock_fetch_all):
        """Returns early when all artists already exist in staging."""
        from src.extract import spotify_artist_extractor

        spotify_artist_extractor.main(batch_size=5, run_id="artist-run")

        mock_fetch_all.assert_called_once()
