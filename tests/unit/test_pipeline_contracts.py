"""Cross-module contracts: extractor payloads must pass loader validation."""

import pytest

from src.load.snowflake_loader import REQUIRED_TABLE_FIELDS, load_raw_records
from tests.unit.constants import (
    VALID_RAW_AUDIO_FEATURES,
    VALID_RAW_LASTFM,
    VALID_RAW_SPOTIFY_ARTISTS,
    VALID_RAW_SPOTIFY_TRACKS,
)


@pytest.mark.parametrize(
    "table,id_column,record",
    [
        ("raw_lastfm", "song_id", VALID_RAW_LASTFM),
        ("raw_audio_features", "song_id", VALID_RAW_AUDIO_FEATURES),
        ("raw_spotify_tracks", "song_id", VALID_RAW_SPOTIFY_TRACKS),
        ("raw_spotify_artists", "artist_id", VALID_RAW_SPOTIFY_ARTISTS),
    ],
    ids=["lastfm", "audio_features", "spotify_tracks", "spotify_artists"],
)
def test_fixture_records_satisfy_loader_required_fields(table, id_column, record):
    """Shared test fixtures include every field the loader requires for that RAW table."""
    required = REQUIRED_TABLE_FIELDS[table]
    missing = required - record.keys()
    assert not missing, f"Fixture missing keys for {table}: {missing}"
    assert record.get(id_column)


@pytest.mark.parametrize(
    "table,id_column,record",
    [
        ("raw_lastfm", "song_id", VALID_RAW_LASTFM),
        ("raw_audio_features", "song_id", VALID_RAW_AUDIO_FEATURES),
        ("raw_spotify_tracks", "song_id", VALID_RAW_SPOTIFY_TRACKS),
        ("raw_spotify_artists", "artist_id", VALID_RAW_SPOTIFY_ARTISTS),
    ],
    ids=["lastfm", "audio_features", "spotify_tracks", "spotify_artists"],
)
def test_extractor_fixtures_load_through_snowflake_loader(
    table, id_column, record, mock_write_pandas, mock_get_snowflake_connection
):
    """End-to-end contract: fixture dicts pass validation and trigger a mocked Snowflake write."""
    n_rows, error_count = load_raw_records(
        table=table,
        records=[record],
        id_columns=id_column,
        run_id="contract-run",
    )

    assert n_rows == 1
    assert error_count == 0
    mock_write_pandas.assert_called_once()
    mock_get_snowflake_connection.assert_called_once()
