# Music Streaming ELT Pipeline

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Snowflake](https://img.shields.io/badge/warehouse-Snowflake-29B5E8.svg)
![dbt](https://img.shields.io/badge/transform-dbt-FF694B.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/unit%20tests-168%20passing-brightgreen.svg)

An **ELT** pipeline for music streaming analytics: Python extractors land API payloads in **Snowflake RAW**, **dbt** builds staging through marts, and **unit tests + GitHub Actions** guard the Python load/match logic. Legacy Kafka/PostgreSQL paths remain in the repo for reference but are not the active architecture.

---

## Overview

| Layer | Responsibility |
|--------|----------------|
| **Extract (Python)** | Spotify seed, artist backfill, Last.fm enrichment, Librosa audio features |
| **Load (Python)** | `load_raw_records` → RAW tables (`VARIANT` JSON + `_run_id`, `_loaded_at`) |
| **Transform (dbt)** | Staging → intermediate → star-schema marts + YAML tests |
| **Orchestration (planned)** | Airflow DAGs (manual script runs today) |

**Data sources:** Spotify Web API, Last.fm API, Librosa on Spotify preview URLs.

**Docs:**

- [Testing guide](docs/TESTING.md) — pytest layout, CI, test catalog  
- [Snowflake + Airflow + dbt migration guide](docs/SNOWFLAKE_AIRFLOW_DBT_GUIDE.md) — full roadmap and phases  

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  EXTRACT (Python)                                                       │
│  spotify_track_extractor_snowflake  →  RAW.raw_spotify_tracks (seed)    │
│  spotify_artist_extractor           →  RAW.raw_spotify_artists          │
│  lastfm_extractor                   →  RAW.raw_lastfm                   │
│  audio_features_extractor           →  RAW.raw_audio_features           │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  TRANSFORM (dbt on Snowflake)                                           │
│  STAGING: stg_spotify__tracks, stg_spotify__artists, stg_lastfm,        │
│           stg_audio__features                                           │
│  INTERMEDIATE: int_albums, int_artist__genres, int_song__enriched         │
│  MARTS: dim_*, fct_songs, fct_audio_features, bridge_artist_genres      │
└─────────────────────────────────────────────────────────────────────────┘
```

Backfill extractors query **STAGING gap sets** (tracks without Last.fm / audio / artist rows), not PostgreSQL.

---

## Tech stack

| Category | Technologies |
|----------|----------------|
| **Language** | Python 3.12+ |
| **Warehouse** | Snowflake (`snowflake-connector-python`, JWT key-pair auth) |
| **Transform** | dbt (`dbt-snowflake`), `dbt_utils`, `dbt_expectations` |
| **APIs** | Spotify, Last.fm |
| **Audio** | librosa, spotify_preview_finder |
| **Testing** | pytest, Hypothesis, responses |
| **CI** | GitHub Actions (pytest + `dbt parse`) |
| **Analysis** | Jupyter, pandas, scipy, statsmodels (notebooks/) |

---

## Project structure

```
music_streaming_pipeline/
├── src/
│   ├── extract/
│   │   ├── spotify_track_extractor_snowflake.py   # Seed tracks → RAW
│   │   ├── spotify_artist_extractor.py            # Artist gap backfill → RAW
│   │   ├── lastfm_extractor.py                    # Last.fm gap backfill → RAW
│   │   └── audio_features_extractor.py            # Librosa gap backfill → RAW
│   ├── load/
│   │   └── snowflake_loader.py                    # load_raw_records
│   └── utils/
│       ├── snowflake_utils.py
│       ├── text_processing_utils.py               # Normalization + similarity (Last.fm)
│       └── http_utils.py
├── music_streaming_dbt/                           # dbt project (staging → marts)
├── tests/unit/                                    # Python unit tests
├── docs/                                          # TESTING.md, migration guide
├── notebooks/                                     # EDA & statistics notebooks
├── deprecated_scripts/                            # Legacy Kafka/Postgres helpers
└── .github/workflows/ci.yml
```

Legacy: `src/transform/data_transformer.py`, `src/load/data_loader.py`, `docker/docker-compose.yml` (Kafka).

---

## Prerequisites

- Python 3.12+ and `pip install -r requirements.txt`
- Snowflake account with database **`MUSICDB`** (or your env override) and schemas **`RAW`**, **`STAGING`**, **`intermediate`**, **`marts`**
- RAW tables: `raw_spotify_tracks`, `raw_spotify_artists`, `raw_lastfm`, `raw_audio_features`
- API keys: Spotify (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`), Last.fm (`LAST_FM_KEY`)
- Snowflake env vars (see `.env.example` — add Snowflake settings locally if not committed)
- dbt profile **`music_streaming_dbt`** in `~/.dbt/profiles.yml`

---

## Setup

```bash
git clone https://github.com/spennyfinn/music_streaming_pipeline.git
cd music_streaming_pipeline
pip install -r requirements.txt
cp .env.example .env   # fill in API + Snowflake credentials

cd music_streaming_dbt
dbt deps
```

---

## Running the pipeline (manual)

Run in order; repeat **dbt** after each backfill batch that adds RAW rows.

### 1. Seed Spotify tracks

```bash
python -m src.extract.spotify_track_extractor_snowflake
```

Optional args: `main(batch_size=5, start_idx=0, run_id="...")` from code or adjust `__main__` defaults.

### 2. Build staging and downstream models

```bash
cd music_streaming_dbt
dbt build --select staging+
```

`staging+` = all staging models plus intermediate and marts (and their tests).

### 3. Backfill enrichments (any order; each reads STAGING gaps)

```bash
python -m src.extract.spotify_artist_extractor
python -m src.extract.lastfm_extractor
python -m src.extract.audio_features_extractor
```

### 4. Refresh marts after new RAW data

```bash
cd music_streaming_dbt
dbt build --select staging+
```

**Selectors:**

```bash
dbt run --select staging+              # run only, no tests
dbt build --select stg_spotify__tracks+   # one branch
dbt build --select stg_lastfm stg_audio__features   # specific staging models
```

---

## Tests and CI

```bash
pytest tests/unit/ -v
```

GitHub Actions (`.github/workflows/ci.yml`):

- **Python unit tests** on every push/PR  
- **`dbt deps` + `dbt parse`** (compile check; no live Snowflake in CI)

See [docs/TESTING.md](docs/TESTING.md) for the full test catalog.

---

## What to do next (rework checklist)

| Priority | Task | Status |
|----------|------|--------|
| 1 | End-to-end manual run: seed → dbt → backfills → dbt | You validate in Snowflake |
| 2 | Snowflake vars in `.env.example` + local `profiles.yml` | Recommended |
| 3 | **`dbt test`** against dev (not only `parse` in CI) | Optional CI secrets |
| 4 | **Airflow** — single DAG: extract → `dbt build` → enrich TaskGroup | Not started |
| 5 | Update notebooks to query **marts** (or exports) instead of Postgres | Pending |
| 6 | Remove/archive legacy Kafka/Postgres path when confident | Pending |
| 7 | README / portfolio: Airflow UI screenshot once DAG exists | Pending |

Detailed phase plan: [docs/SNOWFLAKE_AIRFLOW_DBT_GUIDE.md](docs/SNOWFLAKE_AIRFLOW_DBT_GUIDE.md).

---

## Data analysis

Notebooks under `notebooks/` (EDA, correlations, hypothesis tests, ANOVA). Historical exports used PostgreSQL; point new analysis at Snowflake marts or CSV exports.

| Notebook | Description |
|----------|-------------|
| `01_EDA.ipynb` | Popularity, BPM, energy, danceability |
| `02_correlations.ipynb` | Pearson correlations and regression plots |
| `03_two_tailed_test.ipynb` | Mann-Whitney U, Cohen's d |
| `04_ANOVA.ipynb` | ANOVA by album format and decade |

---
