# Testing guide

This document describes how to run tests before pushing code and what each test file covers. Individual tests use **docstrings** (the string right under each `def test_...`) to explain intent; run with verbose mode to see them:

```bash
pytest tests/unit/ -v
```

## Quick commands

| Command | Purpose |
|---------|---------|
| `pytest tests/unit/ -v` | Full Python unit suite (~159 tests), no Snowflake/API secrets |
| `pytest tests/unit/load/ -v` | RAW loader only |
| `pytest tests/unit/extract/ -v` | Extractors + main() wiring |
| `pytest path::TestClass::test_name -v` | Single test |
| `cd music_streaming_dbt && dbt deps && dbt parse` | Compile dbt models (CI job) |

`pytest.ini` sets `pythonpath = .` so you do not need `PYTHONPATH=.` locally.

## CI (GitHub Actions)

Workflow: `.github/workflows/ci.yml`

1. **unit-tests** — `pytest tests/unit/`
2. **dbt-parse** — `dbt deps` + `dbt parse` in `music_streaming_dbt/`

With Snowflake credentials (manual / nightly): run `dbt test` against a dev schema to execute YAML tests in `music_streaming_dbt/models/`.

---

## Architecture

```
Extract (Python, mocked HTTP)  →  load_raw_records (mocked write_pandas)  →  dbt staging/marts (dbt test)
         ↑                                              ↑
   text_processing_utils                          REQUIRED_TABLE_FIELDS
```

**Unit tests** mock Snowflake and external APIs. **dbt tests** validate staging filters, ranges, and mart relationships on real data.

Shared fixtures live in `tests/conftest.py` (`mock_write_pandas`, connection mocks).

Test payloads for RAW tables live in `tests/unit/constants.py` (`VALID_RAW_*`, parametrized cases).

---

## Test catalog

### `tests/unit/test_text_utils.py`

Last.fm matching depends on these helpers.

| Test | What it checks |
|------|----------------|
| `test_normalize_valid_song_name` | Normalization table: case, ft/feat, `&`, remix brackets, unicode |
| `test_normalize_wrong_types_song_name` | Non-strings raise `TypeError` |
| `test_normalize_song_name_properties` | Hypothesis: lowercase, trimmed, no `&`/feat |
| `test_has_valid_collaborators` | Detects collaborator markers in titles |
| `test_has_collaborators_wrong_types` | Invalid types raise |
| `test_has_collaborators_properties` | Hypothesis: marker ⇒ True; case invariant |
| `test_extract_collaborators_valid_types` | Parses collaborator lists from titles |
| `test_extract_collaborators_wrong_types` | Invalid types raise |
| `test_similarity_score` | Exact, partial, and zero similarity cases |
| `test_similarity_score_wrong_types` | Invalid types raise |
| `test_similarity_score_properties` | Hypothesis: score ∈ [0,1], symmetric, self=1 |

---

### `tests/unit/load/test_snowflake_loader.py`

Target: `src/load/snowflake_loader.load_raw_records`.

| Test | What it checks |
|------|----------------|
| `test_accepts_valid_record_for_each_table` | Valid fixture per RAW table loads 1 row |
| `test_write_pandas_receives_json_payload_per_table` | DataFrame has id, `_run_id`, JSON `payload` |
| `test_empty_records_returns_zero` | `[]` → `(0, 0)`, no DB |
| `test_rejects_empty_table_name` | Empty `table` raises |
| `test_rejects_mismatched_table_and_id_column` | Wrong table/id pair raises |
| `test_rejects_empty_id_columns` | Empty `id_columns` raises |
| `test_all_invalid_skips_write_pandas` | All bad rows → no `write_pandas` |
| `test_rejects_missing_song_id` | Blank ID → error count 1 |
| `test_rejects_missing_required_field` | Missing required field → error |
| `test_mixed_batch_counts_errors` | 1 good + 1 bad → `(1, 1)` |
| `test_opens_and_closes_own_connection` | Opens/closes conn when `conn=None` |
| `test_reuses_passed_connection_without_closing` | Caller-owned conn not closed |
| `test_normalizes_table_name_before_write` | Uppercase table/id normalized |
| `test_strips_whitespace_from_id_in_output_row` | ID stripped in output row |
| `test_write_pandas_uses_env_database_and_schema` | Env `SNOWFLAKE_*` passed to write |
| `test_multiple_valid_records_single_write_call` | Batch of 2 → one DataFrame |
| `test_snowflake_error_is_propagated` | `SnowflakeError` re-raised |

---

### `tests/unit/test_pipeline_contracts.py`

| Test | What it checks |
|------|----------------|
| `test_fixture_records_satisfy_loader_required_fields` | `VALID_RAW_*` keys match loader rules |
| `test_extractor_fixtures_load_through_snowflake_loader` | Fixtures pass full load path (mocked) |

---

### `tests/unit/extract/test_lastfm_extractor.py`

| Test | What it checks |
|------|----------------|
| `test_is_valid_match` | Listeners, unknown artist, empty track |
| `test_rejects_low_similarity` | Low song/artist similarity rejected |
| `test_preserves_spotify_ids_and_original_names` | Match dict shape for loader |
| `test_returns_none_on_http_error` | HTTP errors → `None` |
| `test_returns_none_when_api_error_field_present` | API `error` JSON → `None` |
| `test_includes_api_key_in_query` | `api_key` on requests |
| `test_uses_track_get_info_when_valid` | Primary getInfo path |
| `test_falls_back_to_track_search` | Search when getInfo fails |
| `test_search_picks_higher_scoring_candidate` | Best search candidate wins |
| `test_get_info_accepts_string_artist_block` | String `artist` in JSON |
| `test_adds_artist_stats_and_source` | artist.getInfo enrichment fields |
| `test_rejects_low_artist_similarity` | Artist similarity &lt; 0.9 fails |
| `test_returns_none_without_original_artist_name` | Missing artist name guard |
| `test_returns_complete_record` | Full `process_last_fm_data` success |
| `test_returns_none_when_track_lookup_fails` | No track match → `None` |
| `test_returns_none_when_artist_enrichment_fails` | Track ok, artist fails → `None` |

---

### `tests/unit/extract/test_audio_features_extractor.py`

| Test | What it checks |
|------|----------------|
| `test_includes_all_loader_required_fields` | `_build_feature_record` vs loader |
| `test_returns_url_when_finder_succeeds` | Preview URL from finder |
| `test_returns_none_when_no_results` | Empty finder results |
| `test_returns_none_when_success_flag_false` | `success: false` guard |
| `test_happy_path_with_mocks` | Full orchestration (Librosa mocked) |
| `test_returns_none_when_preview_missing` | No preview → `None` |
| `test_returns_none_when_bpm_extraction_fails` | BPM failure → `None` |

---

### `tests/unit/extract/test_spotify_extractors.py`

| Test | What it checks |
|------|----------------|
| `test_maps_api_json_to_loader_fields` | Search JSON → track dict |
| `test_skips_items_missing_album_or_artist` | Incomplete items skipped |
| `test_skips_track_when_artists_list_empty` | Empty `artists[]` skipped |
| `test_collects_tracks_from_search_pages` | Four offset pages aggregated |
| `test_continues_when_request_fails` | Failed requests → empty list |
| `test_skips_malformed_json_response` | `JSONDecodeError` handled |
| `test_parses_artist_payload` | Artist API → loader dict |
| `test_returns_none_without_response` | No HTTP response → `None` |

---

### `tests/unit/extract/test_extractor_mains.py`

| Test | What it checks |
|------|----------------|
| `test_loads_batch_when_matches_exist` (Last.fm) | `main()` → `raw_lastfm` load |
| `test_raises_when_api_key_missing` | No `LAST_FM_KEY` |
| `test_skips_load_when_no_matches_in_chunk` | No load if all match failures |
| `test_loads_batch_when_features_exist` (audio) | `main()` → `raw_audio_features` |
| `test_exits_when_no_rows` (audio) | Empty staging gap query |
| `test_raises_when_spotify_client_id_missing` | Missing Spotify env |
| `test_loads_extracted_tracks` (seed) | Spotify seed `main()` → `raw_spotify_tracks` |
| `test_raises_on_invalid_start_idx` | Bad `start_idx` |
| `test_raises_when_words_list_empty` | Empty word list |

---

### `tests/unit/utils/test_http_utils.py`

| Test | What it checks |
|------|----------------|
| `test_safe_requests_success_first_try` | Single 200 response |
| `test_safe_requests_retries_then_succeeds` | Retry then success |
| `test_safe_requests_raises_after_max_retries` | Exhausted retries raise |

---

### `tests/unit/utils/test_snowflake_utils.py`

| Test | What it checks |
|------|----------------|
| `test_fetch_all_with_passed_cursor` | Reuses cursor, no close |
| `test_fetch_all_opens_short_lived_cursor` | Opens context when no cursor |

---

### `tests/unit/utils/test_transformer_utils.py`

Legacy helpers (Postgres-era transforms).

| Test | What it checks |
|------|----------------|
| `test_safe_int` | int parsing / defaults |
| `test_safe_float_parses_numeric_string` | float parsing |
| `test_safe_float_empty_returns_default` | Empty → 0.0 |
| `test_strips_and_lowercases` | `safe_string` |
| `test_blank_returns_none` | Whitespace → None |
| `test_logs_missing_none_values` | `determine_missing_fields` logging |

---

## Not covered by unit tests (use dbt or manual runs)

| Area | Where quality is enforced |
|------|---------------------------|
| Staging SQL filters (`stg_*`) | dbt models + `_staging__models.yml` tests |
| Mart FKs / grains | `_marts_models.yml` `relationships`, `unique` |
| Real Librosa decode / HPSS | Manual or future integration test |
| Live Snowflake RAW append | Optional `@pytest.mark.integration` |
| Legacy Kafka/Postgres loaders | Deprecated path; not in CI |

---

## Pre-push checklist

1. `pytest tests/unit/ -v` — all green  
2. `cd music_streaming_dbt && dbt deps && dbt parse` — models compile  
3. After changing extract payloads or loader rules, confirm `tests/unit/test_pipeline_contracts.py` still passes  
4. Before release: `dbt test` on dev Snowflake (optional but recommended)
