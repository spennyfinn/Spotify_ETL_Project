"""Unit tests for load_raw_records — Snowflake is mocked throughout."""

import json
from unittest.mock import MagicMock, patch

import pytest
from snowflake.connector.errors import Error as SnowflakeError

from src.load.snowflake_loader import load_raw_records
from tests.unit.constants import (
    RAW_LOAD_TABLE_CASES,
    RAW_LOAD_TABLE_CASE_IDS,
    RAW_PAYLOAD_SHAPE_CASES,
    RAW_PAYLOAD_SHAPE_CASE_IDS,
    VALID_RAW_LASTFM,
)


class TestLoadRawRecordsAcceptance:
    @pytest.mark.parametrize(
        "table,id_column,record",
        RAW_LOAD_TABLE_CASES,
        ids=RAW_LOAD_TABLE_CASE_IDS,
    )
    def test_accepts_valid_record_for_each_table(
        self, table, id_column, record, mock_snowflake_write, mock_snowflake_connection
    ):
        """Valid fixture for each RAW table loads one row with zero validation errors."""
        n_rows, error_count = load_raw_records(
            table=table,
            records=[record],
            id_columns=id_column,
            run_id="run-1",
        )

        assert n_rows == 1
        assert error_count == 0
        mock_snowflake_write.assert_called_once()
        mock_snowflake_connection.assert_called_once()


class TestLoadRawRecordsPayloadShape:
    @pytest.mark.parametrize(
        "table,id_column,record,df_id_key,payload_assert",
        RAW_PAYLOAD_SHAPE_CASES,
        ids=RAW_PAYLOAD_SHAPE_CASE_IDS,
    )
    def test_write_pandas_receives_json_payload_per_table(
        self,
        table,
        id_column,
        record,
        df_id_key,
        payload_assert,
        mock_snowflake_write,
        mock_snowflake_connection,
    ):
        """DataFrame row has id, _run_id, and JSON-serialized payload dbt can parse."""
        n_rows, error_count = load_raw_records(
            table=table,
            records=[record],
            id_columns=id_column,
            run_id="run-abc",
        )

        assert n_rows == 1
        assert error_count == 0

        row = mock_snowflake_write.call_args.kwargs["df"].iloc[0]
        assert row[df_id_key] == record[df_id_key]
        assert row["_run_id"] == "run-abc"
        assert isinstance(row["payload"], str)

        key, expected = payload_assert
        assert json.loads(row["payload"])[key] == expected


class TestLoadRawRecordsValidation:
    def test_empty_records_returns_zero(self):
        """Empty input list returns (0, 0) without touching Snowflake."""
        n_rows, error_count = load_raw_records(
            table="raw_lastfm",
            records=[],
            id_columns="song_id",
            run_id="run-1",
        )

        assert n_rows == 0
        assert error_count == 0

    def test_rejects_empty_table_name(self):
        """Missing table name raises before any load attempt."""
        with pytest.raises(ValueError, match="No table defined"):
            load_raw_records(
                table="",
                records=[VALID_RAW_LASTFM],
                id_columns="song_id",
                run_id="run-1",
            )

    def test_rejects_mismatched_table_and_id_column(self):
        """Table/id_column pair must match TABLE_ID_PAIRS (e.g. raw_lastfm + song_id)."""
        with pytest.raises(ValueError, match="valid pairs"):
            load_raw_records(
                table="raw_lastfm",
                records=[VALID_RAW_LASTFM],
                id_columns="artist_id",
                run_id="run-1",
            )

    def test_rejects_empty_id_columns(self):
        """Empty id_columns raises when records are non-empty."""
        with pytest.raises(ValueError, match="id_column"):
            load_raw_records(
                table="raw_lastfm",
                records=[VALID_RAW_LASTFM],
                id_columns="",
                run_id="run-1",
            )

    def test_all_invalid_skips_write_pandas(
        self, mock_snowflake_write, mock_snowflake_connection
    ):
        """When every row fails validation, write_pandas and connection are never used."""
        bad = VALID_RAW_LASTFM.copy()
        bad["song_id"] = ""

        n_rows, error_count = load_raw_records(
            table="raw_lastfm",
            records=[bad],
            id_columns="song_id",
            run_id="run-1",
        )

        assert n_rows == 0
        assert error_count == 1
        mock_snowflake_connection.assert_not_called()
        mock_snowflake_write.assert_not_called()

    def test_rejects_missing_song_id(self):
        """Blank song_id increments error_count and skips the row."""
        bad = VALID_RAW_LASTFM.copy()
        bad["song_id"] = ""

        n_rows, error_count = load_raw_records(
            table="raw_lastfm",
            records=[bad],
            id_columns="song_id",
            run_id="run-1",
        )

        assert n_rows == 0
        assert error_count == 1

    def test_rejects_missing_required_field(self):
        """Missing REQUIRED_TABLE_FIELDS key counts as one validation error."""
        bad = VALID_RAW_LASTFM.copy()
        del bad["listeners"]

        n_rows, error_count = load_raw_records(
            table="raw_lastfm",
            records=[bad],
            id_columns="song_id",
            run_id="run-1",
        )

        assert n_rows == 0
        assert error_count == 1

    def test_mixed_batch_counts_errors(
        self, mock_snowflake_write, mock_snowflake_connection
    ):
        """One valid and one invalid row yields (1 loaded, 1 error) in a single write."""
        bad = VALID_RAW_LASTFM.copy()
        bad["listeners"] = ""
        good = VALID_RAW_LASTFM.copy()

        n_rows, error_count = load_raw_records(
            table="raw_lastfm",
            records=[bad, good],
            id_columns="song_id",
            run_id="run-1",
        )

        assert n_rows == 1
        assert error_count == 1
        mock_snowflake_write.assert_called_once()
        mock_snowflake_connection.assert_called_once()


class TestLoadRawRecordsConnection:
    def test_opens_and_closes_own_connection(
        self, mock_snowflake_write,
    ):
        """When conn is omitted, loader opens a connection and closes it in finally."""
        mock_conn = MagicMock()

        with patch(
            "src.load.snowflake_loader.get_snowflake_connection",
            return_value=mock_conn,
        ) as mock_get_conn:
            load_raw_records(
                table="raw_lastfm",
                records=[VALID_RAW_LASTFM],
                id_columns="song_id",
                run_id="run-1",
            )

        mock_get_conn.assert_called_once()
        mock_conn.close.assert_called_once()
        mock_snowflake_write.assert_called_once()

    def test_reuses_passed_connection_without_closing(
        self, mock_snowflake_write,
    ):
        """Caller-owned conn is passed to write_pandas and never closed by loader."""
        mock_conn = MagicMock()

        load_raw_records(
            table="raw_lastfm",
            records=[VALID_RAW_LASTFM],
            id_columns="song_id",
            run_id="run-1",
            conn=mock_conn,
        )

        mock_conn.close.assert_not_called()
        mock_snowflake_write.assert_called_once()
        assert mock_snowflake_write.call_args.kwargs["conn"] is mock_conn


class TestLoadRawRecordsSnowflakeWriteOptions:
    def test_normalizes_table_name_before_write(
        self, mock_snowflake_write, mock_snowflake_connection
    ):
        """Table and id_column names are lowercased/stripped before write_pandas."""
        load_raw_records(
            table="RAW_LASTFM",
            records=[VALID_RAW_LASTFM],
            id_columns="SONG_ID",
            run_id="run-1",
        )

        assert mock_snowflake_write.call_args.kwargs["table_name"] == "raw_lastfm"

    def test_strips_whitespace_from_id_in_output_row(
        self, mock_snowflake_write, mock_snowflake_connection
    ):
        """Primary key in the output DataFrame is stripped of surrounding whitespace."""
        record = VALID_RAW_LASTFM.copy()
        record["song_id"] = "  abc123  "

        load_raw_records(
            table="raw_lastfm",
            records=[record],
            id_columns="song_id",
            run_id="run-1",
        )

        row = mock_snowflake_write.call_args.kwargs["df"].iloc[0]
        assert row["song_id"] == "abc123"

    @patch.dict("os.environ", {"SNOWFLAKE_DATABASE": "TESTDB", "SNOWFLAKE_SCHEMA": "TESTRAW"})
    def test_write_pandas_uses_env_database_and_schema(
        self, mock_snowflake_write, mock_snowflake_connection
    ):
        """write_pandas receives database/schema from env and does not auto-create tables."""
        load_raw_records(
            table="raw_lastfm",
            records=[VALID_RAW_LASTFM],
            id_columns="song_id",
            run_id="run-1",
        )

        kwargs = mock_snowflake_write.call_args.kwargs
        assert kwargs["database"] == "TESTDB"
        assert kwargs["schema"] == "TESTRAW"
        assert kwargs["auto_create_table"] is False

    def test_multiple_valid_records_single_write_call(
        self, mock_snowflake_write, mock_snowflake_connection
    ):
        """Multiple valid rows are batched into one DataFrame and one write_pandas call."""
        first = VALID_RAW_LASTFM.copy()
        second = VALID_RAW_LASTFM.copy()
        second["song_id"] = "def456"

        n_rows, error_count = load_raw_records(
            table="raw_lastfm",
            records=[first, second],
            id_columns="song_id",
            run_id="run-1",
        )

        assert error_count == 0
        df = mock_snowflake_write.call_args.kwargs["df"]
        assert len(df) == 2
        mock_snowflake_write.assert_called_once()

    def test_snowflake_error_is_propagated(self, mock_snowflake_connection):
        """SnowflakeError from write_pandas is re-raised to the caller."""
        with patch("src.load.snowflake_loader.write_pandas") as mock_wp:
            mock_wp.side_effect = SnowflakeError("load failed")
            with pytest.raises(SnowflakeError, match="load failed"):
                load_raw_records(
                    table="raw_lastfm",
                    records=[VALID_RAW_LASTFM],
                    id_columns="song_id",
                    run_id="run-1",
                )
