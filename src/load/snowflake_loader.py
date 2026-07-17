"""Snowflake raw-layer loader for the music streaming ELT pipeline.

Extract scripts call ``load_raw_records`` to append API payloads into RAW tables.
dbt staging models (``stg_spotify__tracks``, etc.) read from those tables next.
"""

import json
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from snowflake.connector import SnowflakeConnection
from snowflake.connector.errors import Error as SnowflakeError
from snowflake.connector.pandas_tools import write_pandas
from src.utils.snowflake_utils import get_snowflake_connection
from config.logging import error_logger

logger = logging.getLogger(__name__)



_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

TABLE_ID_PAIRS = {
    "raw_spotify_tracks": "song_id",
    "raw_spotify_artists": "artist_id",
    "raw_lastfm": "song_id",
    "raw_audio_features": "song_id",
}

REQUIRED_TABLE_FIELDS = {
    "raw_spotify_tracks": {"name", "artist_id", "duration_ms", "source"},
    "raw_spotify_artists": {"artist_name", "follower_count", "popularity", "source"},
    "raw_lastfm": {
        "original_song_name",
        "original_artist_name",
        "artist_id",
        "listeners",
        "artist_listeners",
        "artist_playcount",
        "source",
    },
    "raw_audio_features": {
        "bpm",
        "energy",
        "zero_crossing_rate",
        "harmonic_ratio",
        "percussive_ratio",
        "preview_url",
        "source",
    },
}


        
    

def load_raw_records(
    table: str,
    records: list[dict],
    id_columns: str,
    run_id: str,
    conn: SnowflakeConnection | None = None,
) -> tuple[int, int]:
    """Append validated records to a RAW table via ``write_pandas``.

    Pass ``conn`` to reuse an open connection (caller owns lifecycle). When
    ``conn`` is omitted, a short-lived connection is opened and closed here.
    """
    if not table:
        raise ValueError("No table defined, unable to upload data to Snowflake")

    if not records:
        return (0, 0)

    if not id_columns:
        raise ValueError("There is no defined id_column")

    table = str(table.lower().strip())
    id_columns = str(id_columns.lower().strip())
    table_id_pairs = list(TABLE_ID_PAIRS.items())
    table_id = (table, id_columns)

    if table_id not in table_id_pairs:
        raise ValueError("The table and id_column is not in the valid pairs")

    if not records:
        return (0, 0)

    error_count = 0
    successful_records = []
    for record in records:
        record_id = record.get(id_columns)
        if record_id is None or str(record_id).strip() == "":
            error_count += 1
            continue

        missing_fields = False
        for field in REQUIRED_TABLE_FIELDS[table]:
            value = record.get(field)
            if value is None or str(value).strip() == "":
                missing_fields = True
                break

        if missing_fields:
            error_count += 1
            continue

        data = {
            id_columns: str(record_id).strip(),
            "payload": record.copy(),
            "_run_id": run_id,
        }

        successful_records.append(data)

    if not successful_records:
        return (0, error_count)

    own_conn = conn is None
    if own_conn:
        conn = get_snowflake_connection()

    try:
        rows_for_insertion = []
        for row in successful_records:
            rows_for_insertion.append({
                **row,
                "payload": json.dumps(row["payload"]),
            })

        df = pd.DataFrame(rows_for_insertion)

        _, _, n_rows, _ = write_pandas(
            conn=conn,
            df=df,
            table_name=table,
            database=os.getenv("SNOWFLAKE_DATABASE", "MUSICDB"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
            auto_create_table=False,
            quote_identifiers=False,
        )

        logger.info(
            "Loaded %s rows into %s (skipped %s invalid rows)",
            n_rows,
            table,
            error_count,
        )
        return (n_rows, error_count)

    except KeyError as e:
        error_logger.error("Missing Snowflake config: %s", e)
        raise
    except SnowflakeError as e:
        logger.error("Snowflake error loading into %s: %s", table, e)
        raise
    except Exception as e:
        logger.error("Unexpected error loading into %s: %s", table, e)
        raise
    finally:
        if own_conn and conn is not None:
            conn.close()



    


        
    
            
        
    

    
