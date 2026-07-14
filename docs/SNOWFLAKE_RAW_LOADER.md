# Snowflake Raw Loader — `load_raw_records`

Reference for `src/load/snowflake_loader.py`, the shared helper that writes extract output into Snowflake RAW tables before dbt runs.

---

## Role in the pipeline

```
┌─────────────────┐     load_raw_records      ┌──────────────────┐     dbt      ┌─────────────┐
│ Python extract  │ ────────────────────────► │ MUSICDB.RAW.*    │ ───────────► │ STAGING     │
│ (Spotify, etc.) │   append + metadata       │ append-only      │   transform  │ → marts     │
└─────────────────┘                           └──────────────────┘              └─────────────┘
```

| Layer | Who writes | What happens |
|-------|------------|--------------|
| **RAW** | `load_raw_records` | Land source payloads fast; minimal logic |
| **STAGING** | dbt | Cast, trim, dedupe, filter bad rows |
| **MARTS** | dbt | Star schema for Tableau / analytics |

**Design rule:** Python extracts and loads. SQL (dbt) transforms. Do not normalize or join in `load_raw_records`.

---

## Function signature

```python
def load_raw_records(
    table: str,
    records: list[dict],
    id_column: str,
    run_id: str,
) -> tuple[int, int]:
```

| Parameter | Description |
|-----------|-------------|
| `table` | RAW table name, e.g. `"raw_spotify_tracks"` |
| `records` | List of dicts from the extractor (one dict per API entity) |
| `id_column` | Natural key field name: `"song_id"` or `"artist_id"` |
| `run_id` | Pipeline run id (Airflow `context["run_id"]` or manual uuid) |

**Returns:** `(success_count, error_count)`

---

## Raw table schema

All four RAW tables share the same pattern (defined in `music_streaming_dbt/models/staging/_raw__sources.yml`):

| Column | Type (Snowflake) | Set by |
|--------|------------------|--------|
| `song_id` or `artist_id` | `VARCHAR` | Extractor (via `id_column`) |
| `payload` | `VARIANT` | Full record JSON |
| `_run_id` | `VARCHAR` | `run_id` argument |
| `_loaded_at` | `TIMESTAMP_NTZ` | Loader (UTC now) |

### DDL example

```sql
CREATE TABLE IF NOT EXISTS MUSICDB.RAW.raw_spotify_tracks (
    song_id     VARCHAR NOT NULL,
    payload     VARIANT NOT NULL,
    _run_id     VARCHAR,
    _loaded_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

Repeat for `raw_spotify_artists` (`artist_id`), `raw_lastfm` (`song_id`), `raw_audio_features` (`song_id`).

---

## Input record shape

Extractors pass **flat dicts** from the API. The loader:

1. Reads `record[id_column]` → top-level id column
2. Stores the **entire dict** (or a subset) as `payload`

Example input from Spotify track extract:

```python
{
    "song_id": "3n3Ppam7vgaVa1iaRUc9Lp",
    "name": "Mr. Brightside",
    "artist_id": "0C0XlULifJtAgn6NyCGu",
    "artist_name": "The Killers",
    "album_id": "...",
    "duration_ms": 222973,
    "popularity": 85,
}
```

Row written to Snowflake:

| song_id | payload | _run_id | _loaded_at |
|---------|---------|---------|------------|
| `3n3Ppam7...` | `{ entire dict as JSON }` | `manual-2025-07-09` | `2025-07-09 09:00:00` |

dbt staging then flattens `payload:name`, `payload:artist_id`, etc. (see `stg_spotify__tracks.sql`).

---

## Usage examples

### Manual run (local dev)

```python
from uuid import uuid4
from src.load.snowflake_loader import load_raw_records

run_id = f"manual-{uuid4()}"

success, errors = load_raw_records(
    table="raw_spotify_tracks",
    records=track_dicts,
    id_column="song_id",
    run_id=run_id,
)
print(f"Loaded {success} rows, {errors} errors")
```

### Airflow task (future)

```python
def extract_spotify_tracks(**context):
    tracks = fetch_spotify_tracks(...)
    load_raw_records(
        table="raw_spotify_tracks",
        records=tracks,
        id_column="song_id",
        run_id=context["run_id"],
    )
```

### Table → id_column mapping

| `table` | `id_column` | Extractor |
|---------|-------------|-----------|
| `raw_spotify_tracks` | `song_id` | `spotify_track_extractor.py` |
| `raw_spotify_artists` | `artist_id` | `spotify_artist_extractor.py` |
| `raw_lastfm` | `song_id` | `lastfm_extractor.py` |
| `raw_audio_features` | `song_id` | `audio_features_extractor.py` |

---

## Error handling

| Situation | Behavior |
|-----------|----------|
| Missing `id_column` on a record | Skip row, increment `error_count`, log warning |
| Empty `records` list | Return `(0, 0)` — not an error |
| Snowflake connection failure | Raise — fail the task |
| Single row insert failure | Log, increment `error_count`, continue batch |

RAW loads are **append-only**. Duplicates in RAW are OK; dbt staging dedupes:

```sql
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY song_id
  ORDER BY _loaded_at DESC
) = 1
```

---

## Idempotency

| Layer | Strategy |
|-------|----------|
| **RAW** | Append; duplicates allowed |
| **Staging** | Dedupe to latest `_loaded_at` per natural key |
| **Marts** | dbt incremental `merge` on surrogate/natural keys |

Rerunning an extract + load may add duplicate keys in RAW. Rerunning dbt is safe.

---

## Environment variables

Used by `get_snowflake_connection()` (called internally):

| Variable | Example |
|----------|---------|
| `SNOWFLAKE_ACCOUNT` | From Snowsight Admin → Account identifier |
| `SNOWFLAKE_USER` | `SPENNYFINN` |
| `SNOWFLAKE_PRIVATE_KEY_PATH` | Path to `.p8` key file |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Optional |
| `SNOWFLAKE_ROLE` | `ACCOUNTADMIN` |
| `SNOWFLAKE_WAREHOUSE` | `COMPUTE_WH` |
| `SNOWFLAKE_DATABASE` | `MUSICDB` |
| `SNOWFLAKE_SCHEMA` | `RAW` |

Test connectivity:

```bash
python3 -m src.load.test
```

---

## After loading — run dbt

```bash
cd music_streaming_dbt
dbt run --select staging+
dbt test --select staging+
```

Staging models read from RAW sources defined in `_raw__sources.yml`.

---

## Implementation status

`load_raw_records` is documented but **not yet implemented** (returns nothing). Planned approach:

- `snowflake.connector.pandas_tools.write_pandas` for batch inserts, or
- `executemany` with `PARSE_JSON` for `payload`

Keep batches ≤ 1,000–5,000 rows for API extract sizes in this project.
