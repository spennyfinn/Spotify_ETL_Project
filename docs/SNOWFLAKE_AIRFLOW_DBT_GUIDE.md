# Migration Guide: Snowflake + Airflow + dbt + GitHub Actions

This guide outlines how to rework the music streaming ETL pipeline from its current architecture (Python extract/transform/load, Kafka orchestration, PostgreSQL) into a modern data stack built for learning and production patterns.

**What you have today**

| Layer | Current approach |
|-------|------------------|
| Extract | 4 Python scripts (Spotify, Last.fm, audio features) |
| Transport | Confluent Kafka (5 topics) |
| Transform | Python + Pydantic validation |
| Load | Python batch upserts → PostgreSQL (6 tables) |
| Orchestration | Manual script execution |
| Tests | Pytest (152 tests, in-process, no live Kafka) |

**What you are building toward**

| Layer | Target approach |
|-------|-----------------|
| Extract | Python (Airflow `PythonOperator` tasks) |
| Raw storage | Snowflake raw tables |
| Transform | dbt (SQL models) |
| Load | dbt incremental/merge models → Snowflake marts |
| Orchestrate | Airflow (DAGs, schedules, retries, observability) |
| CI/CD | GitHub Actions (dbt tests, DAG parse checks, linting) |

---

## Table of Contents

1. [Conceptual Shift: ETL → ELT](#1-conceptual-shift-etl--elt)
2. [Background You Need Before Starting](#2-background-you-need-before-starting)
3. [Target Architecture](#3-target-architecture)
4. [What Stays Python vs. What Moves to dbt](#4-what-stays-python-vs-what-moves-to-dbt)
5. [Recommended Project Structure](#5-recommended-project-structure)
6. [Phase-by-Phase Migration Plan](#6-phase-by-phase-migration-plan)
7. [Snowflake Setup](#7-snowflake-setup)
8. [dbt Setup and Modeling Strategy](#8-dbt-setup-and-modeling-strategy)
9. [Airflow Orchestration Design](#9-airflow-orchestration-design)
10. [GitHub Actions CI/CD](#10-github-actions-cicd)
11. [Mapping Your Current Pipeline to the New Stack](#11-mapping-your-current-pipeline-to-the-new-stack)
12. [Testing Strategy Across Tools](#12-testing-strategy-across-tools)
13. [Common Pitfalls and Decisions](#13-common-pitfalls-and-decisions)
14. [Suggested Learning Order](#14-suggested-learning-order)
15. [Resources](#15-resources)

---

## 1. Conceptual Shift: ETL → ELT

Your current pipeline is classic **ETL**: extract data, transform it in Python, then load clean records into PostgreSQL.

The stack you are adopting follows **ELT**:

1. **Extract** raw data from APIs (still Python — APIs and librosa do not belong in SQL).
2. **Load** raw-ish records into Snowflake quickly (minimal transformation).
3. **Transform** inside Snowflake using dbt SQL models.

**Why this matters for your migration**

- Kafka becomes unnecessary. Airflow replaces it as the coordination layer — DAG task dependencies define *when* extract runs, *when* raw data lands, and *when* dbt transforms execute.
- Your Python transform layer (`data_transformer.py`, Pydantic validators) largely moves into dbt models + dbt tests.
- Your Python load layer (`data_loader.py`, upsert logic) becomes dbt incremental/merge models.
- PostgreSQL-specific SQL (`ON CONFLICT DO UPDATE`) becomes Snowflake `MERGE` statements (dbt abstracts this via incremental strategies).

---

## 2. Background You Need Before Starting

### Snowflake fundamentals

Understand these before writing a line of pipeline code:

| Concept | What it is | Why you need it |
|---------|-----------|-----------------|
| **Account / Region** | Your Snowflake tenant | All connections start here |
| **Warehouse** | Compute cluster (sizes: X-Small → 6X-Large) | Runs queries; you pay when it runs |
| **Database → Schema → Table** | Three-level namespace | Organize raw vs. staging vs. marts |
| **Role & grants** | RBAC for users/services | Separate dev vs. CI vs. prod access |
| **Stage** | Cloud storage pointer (S3/GCS/Azure or internal) | Landing files before `COPY INTO` |
| **File format** | JSON, CSV, Parquet parsing rules | Match your extract output |
| **`COPY INTO`** | Bulk load from stage → table | Fast raw ingestion |
| **`MERGE`** | Upsert (match + insert/update) | Replaces PostgreSQL `ON CONFLICT` |
| **Variant column** | Semi-structured JSON storage | Useful for raw API payloads before flattening |

**Key Snowflake behavior to internalize:** storage is cheap, compute is metered. Design for loading raw data cheaply, then transform on demand with appropriately sized warehouses.

### dbt fundamentals

dbt is a **transformation framework** — it compiles SQL and runs it against your warehouse. It does not extract data or orchestrate jobs by itself.

| Concept | What it is |
|---------|-----------|
| **Project** | Folder with `dbt_project.yml`, models, tests, macros |
| **Profile** | Connection config (`profiles.yml`) — dev vs. prod targets |
| **Source** | Declared upstream table (`sources.yml`) |
| **`ref()`** | Reference another dbt model (builds the DAG) |
| **Model** | One `.sql` file → one table or view in Snowflake |
| **Materialization** | How a model is persisted: `view`, `table`, `incremental`, `ephemeral` |
| **Seed** | CSV loaded as a table (good for small reference data) |
| **Test** | Data quality checks: `unique`, `not_null`, `accepted_values`, custom SQL |
| **Macro** | Reusable Jinja/SQL snippet (like a function) |
| **Snapshot** | Slowly changing dimension tracking (SCD Type 2) |

**dbt's DAG is implicit:** if model B uses `ref('A')`, dbt knows A must run before B. Airflow orchestrates *when* the entire dbt project (or subsets) runs; dbt handles model ordering internally.

### Airflow fundamentals

Airflow is a **workflow orchestrator** — it schedules and monitors pipelines defined as DAGs (Directed Acyclic Graphs).

| Concept | What it is |
|---------|-----------|
| **DAG** | A pipeline definition — a set of tasks with dependencies, no cycles |
| **Task** | A single unit of work (one step in the pipeline) |
| **Operator** | Template for a task type (`PythonOperator`, `BashOperator`, etc.) |
| **TaskGroup** | Groups related tasks for cleaner DAG layout (e.g., parallel extractors) |
| **Scheduler** | Background process that triggers DAG runs based on schedule |
| **Webserver** | UI at `localhost:8080` — view runs, logs, task status, retry |
| **Executor** | How tasks run: `SequentialExecutor` (dev), `LocalExecutor`, `CeleryExecutor`, `KubernetesExecutor` |
| **Connection** | Stored credentials (Snowflake, APIs) managed in Airflow UI or env vars |
| **Variable** | Key-value config (JSON blobs, feature flags) |
| **XCom** | Cross-communication — pass small metadata between tasks (not for large datasets) |
| **Sensor** | Task that waits for a condition (file lands, partition exists, upstream DAG completes) |
| **Hook** | Reusable connection logic (e.g., `SnowflakeHook`) |

**Integration pattern you'll use:** Airflow `PythonOperator` tasks run extract logic and write to Snowflake raw tables → `BashOperator` (or Astronomer Cosmos) runs `dbt run` and `dbt test` as downstream tasks.

**Important Airflow principle:** Airflow orchestrates work; it should not hold large datasets in XCom. Extract tasks write to Snowflake; dbt reads from Snowflake. Pass only metadata (row counts, run IDs) via XCom if needed.

### GitHub Actions fundamentals (for data pipelines)

| Concept | What it is |
|---------|-----------|
| **Workflow** | YAML file in `.github/workflows/` triggered by push/PR |
| **Job** | Set of steps on a runner |
| **Secret** | Encrypted env vars (Snowflake creds, dbt keys) |
| **Matrix** | Run same job across multiple configs |
| **PR checks** | Run dbt parse/test against a dev schema on every PR |

Typical data pipeline CI does **not** run full extracts on every push (API rate limits, cost). Instead: lint SQL, parse dbt, validate Airflow DAGs load without import errors, run unit tests, run dbt against a slim dev schema.

---

## 3. Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AIRFLOW (Orchestrator)                      │
│  DAGs · Schedules · Task Dependencies · Retries · Web UI            │
└─────────────────────────────────────────────────────────────────────┘
         │                    │                         │
         ▼                    ▼                         ▼
┌─────────────────┐  ┌─────────────────┐    ┌─────────────────────┐
│ Python Extract  │  │  Load Raw to    │    │  dbt run + test     │
│ (PythonOperator)│─▶│  Snowflake      │───▶│  (BashOperator /    │
│  APIs, librosa  │  │                 │    │   Cosmos)           │
└─────────────────┘  └─────────────────┘    └─────────────────────┘
                              │                         │
                              ▼                         ▼
                     ┌─────────────────────────────────────────┐
                     │              SNOWFLAKE                  │
                     │  RAW → STAGING → INTERMEDIATE → MARTS   │
                     └─────────────────────────────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  GitHub Actions  │  ← CI on every PR
                     └─────────────────┘
```

### Suggested Snowflake layer naming

| Schema | Purpose | Example contents |
|--------|---------|-----------------|
| `RAW` | Untouched API payloads | `raw_spotify_tracks`, `raw_lastfm_artists` |
| `STAGING` | dbt staging models — cleaned, typed, renamed | `stg_spotify__tracks` |
| `INTERMEDIATE` | Business logic joins, dedup | `int_tracks_unioned` |
| `MARTS` | Final analytics-ready tables | `dim_artists`, `fact_songs`, `fact_audio_features` |

This mirrors dbt best practice (staging → intermediate → marts) and maps cleanly to your current 6-table PostgreSQL schema.

---

## 4. What Stays Python vs. What Moves to dbt

### Keep in Python (Airflow-managed)

These are poor fits for SQL/dbt:

| Current module | Why it stays Python |
|----------------|---------------------|
| `spotify_track_extractor.py` | External HTTP API, pagination, rate limiting |
| `spotify_artist_extractor.py` | Same + parallel API calls |
| `lastfm_extractor.py` | API calls + **similarity scoring** (Levenshtein/difflib) |
| `audio_features_extractor.py` | **librosa** signal processing on audio bytes |
| Spotify/Last.fm auth | Token refresh logic |

Airflow wraps these as **`PythonOperator` tasks** (or callables in a shared `extract/` module) that write directly to Snowflake raw tables.

### Move to dbt (SQL)

| Current module | dbt replacement |
|----------------|-----------------|
| `data_transformer.py` | Staging + intermediate models (lowercase, type casts, derived fields like `engagement_ratio`, `danceability`) |
| Pydantic validators (`src/validate/`) | dbt tests + staging model constraints (`where` filters, `cast`, `coalesce`) |
| `data_loader.py` | Incremental/merge marts models |
| `parsers.py` | Staging SQL that unnests/flattens raw JSON |
| PostgreSQL schema DDL | dbt model definitions + `schema.yml` documentation |

### Retire entirely

| Component | Replacement |
|-----------|-------------|
| Kafka + `kafka_utils.py` | Airflow task dependencies |
| Manual script execution | Airflow schedules |
| PostgreSQL | Snowflake |
| `docker-compose.yml` Kafka services | Airflow docker-compose (see Phase 0) |

---

## 5. Recommended Project Structure

Reorganize the repo into a **polyglot monorepo** — common pattern for Airflow + dbt projects:

```
music_streaming_pipeline/
├── .github/
│   └── workflows/
│       ├── dbt-ci.yml              # dbt parse, lint, test on PR
│       └── airflow-ci.yml          # DAG import check, pytest
├── airflow/
│   ├── dags/
│   │   ├── music_seed_pipeline.py      # Spotify tracks → dbt (seed)
│   │   ├── music_enrich_pipeline.py    # Backfill extractors → dbt
│   │   └── music_full_pipeline.py      # Chains seed then enrich
│   ├── plugins/                        # Custom hooks/operators (if needed)
│   └── Dockerfile                      # Optional custom Airflow image
├── docker/
│   └── docker-compose.yml              # Airflow + Postgres (metadata DB)
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml                    # DO NOT commit — use env vars / CI secrets
│   ├── models/
│   │   ├── staging/
│   │   │   ├── spotify/
│   │   │   ├── lastfm/
│   │   │   └── audio_features/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── seeds/
│   ├── macros/
│   ├── tests/
│   └── snapshots/
├── extract/                            # Python extract logic (refactored from src/extract/)
│   ├── spotify_tracks.py
│   ├── spotify_artists.py
│   ├── lastfm.py
│   ├── audio_features.py
│   └── snowflake_loader.py             # Shared raw-table write helper
├── config/
├── docs/
├── tests/                              # Python unit tests for extract logic
├── requirements.txt                    # apache-airflow, dbt-snowflake, etc.
└── README.md
```

You do not need to adopt this layout on day one, but keeping `airflow/dags/`, `dbt/`, and `extract/` separate avoids confusion about which tool owns which code.

---

## 6. Phase-by-Phase Migration Plan

Work in phases. Each phase should leave you with something runnable.

### Phase 0 — Accounts, tooling, and learning setup

**Goal:** All tools installed, accounts created, "hello world" for each.

- [ ] Create a Snowflake trial account (or use Snowflake free learning credits).
- [ ] Install locally: `dbt-snowflake`, `apache-airflow`, `snowflake-connector-python`, provider packages (`apache-airflow-providers-snowflake`, `apache-airflow-providers-dbt-cloud` optional).
- [ ] Stand up local Airflow via Docker Compose (official Apache Airflow example or Astronomer CLI — pick one and stick with it).
- [ ] Create a GitHub repo branch strategy: `main` (prod), `dev` (integration), feature branches.
- [ ] Run `dbt init` to scaffold a dbt project connected to Snowflake.
- [ ] Write a minimal `hello_world` DAG with one `BashOperator` task; confirm it appears in the Airflow UI and runs green.
- [ ] Confirm you can connect to Snowflake from dbt, Python, and an Airflow Snowflake connection.

**Exit criteria:** `dbt debug` passes. Airflow UI loads at `localhost:8080`. A test DAG runs successfully. You can `SELECT 1` from Snowflake via all three paths.

**Local Airflow options (pick one):**

| Option | Pros | Cons |
|--------|------|------|
| **Official Airflow Docker Compose** | Standard, well-documented | Heavier setup, many containers |
| **Astronomer CLI (`astro dev start`)** | Polished dev experience | Extra tooling to learn |

For a junior DE portfolio, the official Docker Compose is fine and more universally recognized.

---

### Phase 1 — Snowflake foundation

**Goal:** Warehouse, databases, schemas, roles, and raw landing tables exist.

- [ ] Create databases: `MUSIC_DEV`, `MUSIC_PROD` (or use schema-based separation in one DB while learning).
- [ ] Create schemas: `RAW`, `STAGING`, `INTERMEDIATE`, `MARTS`.
- [ ] Create warehouses: `DEV_WH` (X-Small, auto-suspend 60s), `CI_WH` (X-Small).
- [ ] Create roles: `DBT_ROLE`, `EXTRACT_ROLE`, `ANALYST_ROLE` with least-privilege grants.
- [ ] Design raw tables — one per source, with metadata columns:
  - `_loaded_at` (timestamp)
  - `_run_id` (Airflow `run_id` or `dag_run.run_id` — for lineage)
  - Payload column(s): typed columns OR a `VARIANT` JSON column for flexibility
- [ ] Decide ingestion method:
  - **Option A (simpler for learning):** Python writes rows directly via `snowflake-connector` INSERT/batch.
  - **Option B (more production-like):** Python writes Parquet/JSON to a stage → `COPY INTO` raw table.
- [ ] Store Snowflake credentials as an Airflow **Connection** (`snowflake_default`).

**Exit criteria:** You can manually load a sample JSON record into a raw table and query it. Airflow connection test succeeds.

---

### Phase 2 — dbt: staging models (replace Python transform)

**Goal:** Replicate transform logic from `data_transformer.py` as SQL.

Work source-by-source. Recommended order:

1. **Spotify tracks** (simplest — maps directly to your most-tested path)
2. **Artist genres**
3. **Last.fm enrichment**
4. **Audio features**

For each source:

- [ ] Declare the raw table as a dbt **source** in `sources.yml`.
- [ ] Create a **staging model** that:
  - Selects from raw
  - Applies lowercase/trim (replaces `safe_string` normalization)
  - Casts types (replaces `safe_int`, `safe_float`)
  - Filters out records missing required fields (replaces Pydantic `ValidationError` skips)
  - Computes derived fields (`engagement_ratio`, `danceability`, `duration_minutes`, etc.)
- [ ] Add **schema tests** mirroring your Pydantic constraints:
  - `not_null` on required columns
  - `accepted_values` on enums (`album_type`, `release_date_precision`)
  - `dbt_expectations` or custom tests for range checks (popularity 0–100, BPM 30–300)
- [ ] Run `dbt run --select staging` and `dbt test --select staging`.

**Exit criteria:** Staging models produce the same logical records your Python transformer produced (validate by comparing row counts and spot-checking values against existing PostgreSQL exports).

---

### Phase 3 — dbt: marts (replace Python load)

**Goal:** Final tables with upsert/incremental logic.

- [ ] Model your 6 PostgreSQL tables as dbt marts:
  - `dim_artists`
  - `dim_albums`
  - `fact_songs`
  - `fact_audio_features`
  - `dim_genres`
  - `bridge_artist_genres`
- [ ] Use **`incremental` materialization with `merge` strategy** (Snowflake) for idempotent upserts — this replaces `ON CONFLICT DO UPDATE`.
  - Define a `unique_key` per model (e.g., `song_id`, `artist_id`).
- [ ] Handle foreign key ordering via dbt DAG: artists → albums → songs → audio features → genres → artist_genres.
- [ ] Add referential integrity tests (`relationships` test between marts).
- [ ] Document all models in `_models.yml`.

**Exit criteria:** Running `dbt run` populates all mart tables. Running `dbt test` passes. Re-running is idempotent (no duplicates).

---

### Phase 4 — Refactor Python extract layer

**Goal:** Extract scripts write to Snowflake raw tables instead of Kafka.

- [ ] Strip Kafka imports and `kafka_utils.py` usage from extractors.
- [ ] Refactor each extractor into a callable function (your integration tests already exercise functions directly — lean into this pattern).
- [ ] Create a shared `extract/snowflake_loader.py` helper that batch-inserts into raw tables with `_loaded_at` and `_run_id`.
- [ ] Each extract callable should accept an optional `run_id` parameter (pass Airflow's `context['run_id']` from the operator).
- [ ] Keep API retry logic, rate limiting, and ProcessPoolExecutor for audio/artist extraction.
- [ ] **Last.fm similarity matching** stays in Python — write matched records to raw, not unmatched candidates.
- [ ] Backfill extractors query Snowflake marts (not PostgreSQL) to find records needing enrichment.

**Exit criteria:** Running an extractor manually populates Snowflake raw tables. dbt staging models pick up the new data on next `dbt run`.

---

### Phase 5 — Airflow orchestration

**Goal:** Full pipeline runs from the Airflow UI with correct dependency ordering.

#### Step 5a — Define Airflow connections and variables

- [ ] **Connection `snowflake_default`:** account, user, role, warehouse, database, schema.
- [ ] **Connection or env vars for APIs:** Spotify client ID/secret, Last.fm key (use Airflow Connections or `.env` mounted into containers — never hardcode in DAG files).
- [ ] **Variable `dbt_project_dir`:** path to `dbt/` relative to Airflow home (or absolute path in Docker volume mount).

#### Step 5b — Choose how Airflow invokes dbt

| Approach | When to use | Lineage in Airflow UI |
|----------|-------------|----------------------|
| **`BashOperator`** calling `dbt run` / `dbt test` | Start here — simplest | One task per dbt invocation |
| **Astronomer Cosmos** | When you want each dbt model as its own Airflow task | Full model-level task graph |
| **dbt Cloud operator** | If you adopt dbt Cloud | Managed by dbt Cloud |

**Recommendation:** Begin with `BashOperator` for `dbt run --select staging+` and `dbt test`. Graduate to Cosmos once the pipeline is stable and you want finer-grained retries/observability per model.

#### Step 5c — Build the DAGs

Model your **seed → enrich** pattern explicitly. Two common patterns:

**Pattern A — Single DAG (recommended while learning):**

```
extract_spotify_tracks
        │
        ▼
   dbt_run_seed          (dbt run --select staging+ after seed raw data)
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
extract_artists    extract_lastfm    extract_audio_features
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                    dbt_run_enrich
                           │
                           ▼
                       dbt_test
```

Use a **`TaskGroup`** for the three parallel backfill extractors. Use `>>` dependency syntax to enforce ordering.

**Pattern B — Two DAGs with trigger:**

- `music_seed_pipeline` DAG: extract Spotify → dbt run
- `music_enrich_pipeline` DAG: backfill extracts → dbt run → dbt test
- Use `TriggerDagRunOperator` at the end of seed to kick off enrich, or an **`ExternalTaskSensor`** in enrich that waits for seed to finish.

Pattern A is easier to reason about and debug locally.

#### Step 5d — Task configuration checklist

For each `PythonOperator` extract task:

- [ ] Set `retries=2` and `retry_delay=timedelta(minutes=5)` for API flakiness.
- [ ] Set `execution_timeout` (especially for audio features — librosa is slow).
- [ ] Use `on_failure_callback` or Airflow's email/Slack alerting (optional but good portfolio material).
- [ ] Log row counts written to Snowflake; optionally push count to XCom for a downstream validation task.

For each dbt task:

- [ ] Run from the correct working directory (`dbt_project_dir`).
- [ ] Pass `--profiles-dir` and target (`--target dev`).
- [ ] Chain `dbt test` after `dbt run` with a hard dependency.

#### Step 5e — Scheduling

- [ ] Add a **`schedule`** to the full pipeline DAG (e.g., `@weekly` or cron `0 6 * * 1` for Monday 6 AM while learning).
- [ ] Set `catchup=False` to avoid backfilling every missed interval during development.
- [ ] Set meaningful `start_date`, `tags=['music', 'elt']`, and `description` in DAG default args — interviewers notice polished DAG metadata.

**Exit criteria:** Triggering the full DAG from the Airflow UI runs extract → dbt → test successfully. Re-running is idempotent. Task logs are readable.

---

### Phase 6 — GitHub Actions CI/CD

**Goal:** Automated checks on every pull request.

#### Workflow 1: dbt CI (`.github/workflows/dbt-ci.yml`)

Trigger: pull request to `main` or `dev`.

Steps:
1. Checkout code.
2. Set up Python.
3. Install dbt + adapter.
4. Inject Snowflake credentials from GitHub Secrets.
5. Run `dbt deps` (if using packages).
6. Run `dbt parse` (validates project compiles).
7. Run `dbt run --select staging` against a **`CI` schema** (not prod!).
8. Run `dbt test --select staging`.
9. Optionally run SQLFluff lint on changed `.sql` files.

#### Workflow 2: Airflow CI (`.github/workflows/airflow-ci.yml`)

Steps:
1. Install project dependencies (`apache-airflow`, providers, pytest).
2. Run **`python -m pytest tests/`** for extract unit tests.
3. Validate DAG files import without error:
   - `airflow dags list` (requires Airflow metadata DB — use SQLite for CI or `airflow db init` in workflow)
   - Or a lightweight script that imports each DAG file and calls `dag.test()` (Airflow 2.5+)
4. Optionally run **`ruff`** or **`flake8`** on `airflow/dags/` and `extract/`.

#### Workflow 3: Deploy (optional, later)

Trigger: merge to `main`.

Steps:
1. Run dbt against prod target.
2. Sync DAG files to your Airflow deployment (volume mount, S3 sync, or CI deploy to Astro Cloud / MWAA).

**Secrets to configure in GitHub:**

| Secret | Used by |
|--------|---------|
| `SNOWFLAKE_ACCOUNT` | dbt, Airflow, CI |
| `SNOWFLAKE_USER` | dbt, Airflow, CI |
| `SNOWFLAKE_PASSWORD` or private key | dbt, Airflow, CI |
| `SNOWFLAKE_ROLE` | dbt, Airflow, CI |
| `SNOWFLAKE_WAREHOUSE` | dbt, Airflow, CI |
| `SPOTIFY_CLIENT_ID/SECRET` | Airflow extract tasks (not CI unless you run extracts) |
| `LAST_FM_KEY` | Airflow extract tasks |

**Exit criteria:** A PR with a broken dbt model or a DAG import error fails CI. A clean PR passes.

---

### Phase 7 — Decommission legacy stack

**Goal:** Remove dead code and update documentation.

- [ ] Remove Kafka from `docker-compose.yml` and `requirements.txt`.
- [ ] Delete or archive `src/utils/kafka_utils.py`, Kafka consumer loops in transformer/loader.
- [ ] Remove PostgreSQL-specific code (`psycopg2`, `database_utils.py` load queries) once Snowflake path is stable.
- [ ] Update main `README.md` with new architecture, Airflow UI URL, and how to trigger DAGs.
- [ ] Update analysis notebooks to read from Snowflake (or export marts to CSV as you do today).
- [ ] Add `docs/DECISIONS.md` noting why Airflow was chosen (industry standard, DAG scheduling, provider ecosystem).

**Exit criteria:** No Kafka or PostgreSQL dependencies in the active pipeline path.

---

## 7. Snowflake Setup

### Account provisioning checklist

1. Sign up at [snowflake.com](https://signup.snowflake.com/) (trial is sufficient for learning).
2. Note your **account identifier** (format varies by cloud/region, e.g., `xy12345.us-east-1`).
3. Create a dedicated user for pipeline automation (not your personal login).
4. Enable key-pair authentication for CI (more secure than passwords in secrets).

### Environment separation strategy

While learning, use **one database with schema separation**:

```
MUSIC_DB
├── RAW          ← extract writes here
├── STAGING      ← dbt staging models
├── INTERMEDIATE ← dbt intermediate models
├── MARTS        ← dbt final models
└── CI           ← GitHub Actions ephemeral schema (drop/recreate per run)
```

Move to separate databases (`MUSIC_DEV`, `MUSIC_PROD`) when you start deploying on a schedule.

### Cost control habits

- Set `AUTO_SUSPEND = 60` on all warehouses.
- Use X-Small for dev/CI.
- Never run CI against prod schemas.
- Monitor query history in Snowflake UI during development.

---

## 8. dbt Setup and Modeling Strategy

### Initialize the project

Run `dbt init` and select Snowflake as the adapter. Configure `profiles.yml` to use environment variables rather than hardcoded credentials.

### Translating your PostgreSQL schema

Your current 6 tables map to a **dimensional model**:

| PostgreSQL table | dbt mart | Type |
|-----------------|----------|------|
| `artists` | `dim_artists` | Dimension |
| `albums` | `dim_albums` | Dimension |
| `songs` | `fact_songs` | Fact |
| `song_audio_features` | `fact_audio_features` | Fact |
| `genres` | `dim_genres` | Dimension |
| `artist_genres` | `bridge_artist_genres` | Bridge |

### Incremental strategy for upserts

Your current loader uses `ON CONFLICT DO UPDATE`. In dbt on Snowflake:

- Materialization: `incremental`
- Strategy: `merge`
- `unique_key`: primary key column(s)

This gives you the same idempotent re-run behavior your pipeline relies on today.

### Handling the genre many-to-many

Your current loader inserts genres, then artist_genres relationships. In dbt:

- `dim_genres`: incremental merge on `genre_name`
- `bridge_artist_genres`: incremental merge on `(artist_id, genre_id)` composite key
- Use intermediate models to unnest the `genres` array from artist staging before joining.

### Tests to replicate Pydantic validation

| Pydantic constraint | dbt equivalent |
|--------------------|----------------|
| Required fields | `not_null` test |
| `popularity` 0–100 | custom test or `dbt_expectations.expect_column_values_to_be_between` |
| `album_type` enum | `accepted_values` test |
| Foreign keys | `relationships` test |
| Unique IDs | `unique` test |

Install the `dbt_expectations` or `elementary` package for richer data quality checks as you advance.

---

## 9. Airflow Orchestration Design

### Recommended pattern: TaskFlow API (Airflow 2.x)

Airflow 2.x supports the **`@dag` decorator** and **`@task` decorator** (TaskFlow API) as a modern alternative to classic `PythonOperator` + `DAG()` context manager syntax. Both are valid; TaskFlow is cleaner for Python-heavy pipelines.

Conceptually, your DAGs should follow these rules:

| Rule | Why |
|------|-----|
| **DAGs are definitions, not scripts** | No extract logic inline in the DAG file — import callables from `extract/` |
| **Idempotent tasks** | Re-running a task should not duplicate data (use merge keys, `_run_id` tracking) |
| **One concern per task** | One extract source per task; separate `dbt run` from `dbt test` |
| **No large XCom payloads** | Write data to Snowflake; pass only counts/metadata between tasks |
| **Explicit dependencies** | Never rely on timing — use `>>` or `set_downstream()` |

### DAG inventory

| DAG | Schedule | Purpose |
|-----|----------|---------|
| `music_seed_pipeline` | Manual / triggered | Spotify track extract → dbt (initial data) |
| `music_enrich_pipeline` | Manual / triggered | Backfill extracts → dbt |
| `music_full_pipeline` | Weekly (while learning) | Seed → dbt → enrich → dbt → test |

Start with one `music_full_pipeline` DAG. Split into separate DAGs only when you need independent scheduling.

### TaskGroup for parallel backfill

After the seed dbt run completes, the three backfill extractors (artists, Last.fm, audio) have no dependency on each other — run them in parallel inside a **`TaskGroup`** to mirror your current "4 extractors can run in parallel" design.

All three must finish before the enrich dbt run starts.

### Passing Airflow context to extract functions

Your extract callables should accept Airflow context for traceability:

- `context['run_id']` → write to `_run_id` column in raw tables
- `context['ds']` → logical date of the DAG run (useful for incremental filtering)
- `context['task_instance']` → logging, XCom push for row counts

Define a thin wrapper in each DAG or a shared `extract/task_wrappers.py` that pulls context and calls the core extract function.

### dbt invocation from Airflow

**Starter approach (BashOperator):**

Run dbt as shell commands with explicit project and profiles directories. Use separate tasks for run vs. test so test failures are visible independently.

**Intermediate approach (Astronomer Cosmos):**

Cosmos reads your `dbt_project.yml` and renders each dbt model as an Airflow task, respecting `ref()` dependencies. Install via `pip install astronomer-cosmos`. Configure a `ProjectConfig`, `ProfileConfig`, and `RenderConfig` pointing at your dbt project.

This is worth adding in Phase 5 once BashOperator dbt tasks work — it demonstrates advanced Airflow + dbt integration in interviews.

### Local development workflow

1. Start Airflow: `docker-compose -f docker/docker-compose.yml up -d` (or `astro dev start`).
2. Open UI: `http://localhost:8080` (default login often `airflow` / `airflow`).
3. Unpause the DAG and click **Trigger DAG**.
4. Watch task progress in Graph or Grid view; click a task → **Log** for debugging.

This replaces running 6 Python scripts manually and watching Kafka UI.

### Deployment options (pick one later)

| Option | Best for |
|--------|----------|
| **Local Docker Compose** | Solo learning, portfolio project |
| **AWS MWAA** | Production on AWS, managed Airflow |
| **Astronomer Astro** | Managed Airflow, strong dbt/Cosmos support |
| **Self-hosted (EC2/K8s)** | Full control, more ops overhead |

Start with local Docker Compose. Document MWAA or Astro as the production path in `docs/DECISIONS.md` without requiring cloud spend to complete the project.

### Airflow metadata database

Airflow needs its own Postgres (or MySQL) for DAG run history, task state, and connections — this is **separate from Snowflake**. Your `docker-compose.yml` should include:

- `postgres` (Airflow metadata)
- `airflow-webserver`
- `airflow-scheduler`
- `airflow-triggerer` (for deferrable operators/sensors, Airflow 2.2+)

Do not confuse Airflow's Postgres with your old pipeline Postgres — the old one goes away; this one stays as Airflow infrastructure.

---

## 10. GitHub Actions CI/CD

### Branch strategy

```
feature/*  →  PR  →  dev  →  PR  →  main
                      ↑              ↑
                   dbt CI         dbt CI + deploy
                   (CI schema)    (prod schema)
```

### What to run on every PR (cheap, fast)

- `dbt parse`
- `dbt compile`
- SQLFluff lint (changed files only)
- `dbt test` against CI schema with seed/mock data
- `pytest` for Python extract unit tests
- Airflow DAG import validation (no syntax/import errors)

### What NOT to run on every PR

- Full Spotify/Last.fm extracts (rate limits, cost, flakiness)
- librosa audio processing (slow, needs network)
- Full dbt run against prod
- Spinning up full Airflow Docker stack (too slow — use import-only checks)

### CI schema isolation pattern

In CI workflow:
1. Generate a unique schema name: `CI_<pr_number>_<run_id>`.
2. Set `DBT_SCHEMA` env var or use dbt target `ci` with dynamic schema.
3. Load a small seed/fixture dataset into raw tables (or use dbt seeds).
4. Run dbt.
5. Drop the CI schema after the run (Snowflake `DROP SCHEMA ... CASCADE`).

### GitHub Secrets setup

Go to **Repository → Settings → Secrets and variables → Actions** and add Snowflake + dbt credentials. Never commit `profiles.yml` with real passwords.

---

## 11. Mapping Your Current Pipeline to the New Stack

| Current component | New home | Notes |
|----------------|----------|-------|
| `spotify_track_extractor.py` | Airflow `PythonOperator` + Snowflake `RAW.raw_spotify_tracks` | Seed task |
| `spotify_artist_extractor.py` | Airflow task + `RAW.raw_spotify_artists` | Backfill task in TaskGroup |
| `lastfm_extractor.py` | Airflow task + `RAW.raw_lastfm` | Similarity logic stays Python |
| `audio_features_extractor.py` | Airflow task + `RAW.raw_audio_features` | librosa stays Python; set long timeout |
| `data_transformer.py` | dbt staging models | Delete after migration |
| `src/validate/*.py` | dbt tests + staging SQL | Delete after migration |
| `data_loader.py` | dbt incremental marts | Delete after migration |
| `kafka_utils.py` | Delete | Airflow task dependencies replace |
| `database_utils.py` (load queries) | Delete | dbt replaces |
| `database_utils.py` (read queries for backfill) | Refactor | Query Snowflake marts for gaps |
| `tests/integration/test_end_to_end.py` | Split: Python tests for extract; dbt tests for transform/load | |
| `docker-compose.yml` (Kafka) | Replace with Airflow stack | |
| PostgreSQL (pipeline DB) | Snowflake | |
| Analysis notebooks | Point at Snowflake marts or exported CSV | |

---

## 12. Testing Strategy Across Tools

| Layer | Tool | What to test |
|-------|------|-------------|
| Extract functions | pytest | API parsing, retry logic, similarity scoring (mock HTTP) |
| Raw ingestion | Airflow task + Snowflake query | Row count > 0, required keys present (manual or test DAG) |
| Staging transforms | dbt tests | Schema, ranges, not-null, uniqueness |
| Mart logic | dbt tests | Relationships, incremental correctness |
| DAG integrity | Airflow `dag.test()` / CI import check | No import errors, dependencies resolve |
| End-to-end | Airflow full DAG run in dev | Trigger pipeline, verify marts populated |
| CI | GitHub Actions | Parse, compile, test pass on PR |

Your existing 152 pytest tests are valuable for extract logic. Tests that cover transform/load with mocked cursors should be replaced by dbt tests, not ported verbatim.

---

## 13. Common Pitfalls and Decisions

### Pitfall: Putting business logic in the DAG file
Keep DAG files thin — import extract callables from `extract/`. DAG files define dependencies and config only.

### Pitfall: Trying to move API calls into dbt
dbt cannot call the Spotify API. Keep extract in Python.

### Pitfall: Running dbt before raw data exists
Airflow task dependencies must enforce: all upstream extract tasks succeed before dbt run tasks execute. Use `TriggerRule` carefully if you add optional extract branches.

### Pitfall: Using XCom to pass extracted data between tasks
XCom is for metadata (row counts, status flags), not thousands of JSON records. Extract tasks write to Snowflake; dbt reads from Snowflake.

### Pitfall: Case sensitivity
Snowflake is case-sensitive for quoted identifiers. Standardize on lowercase unquoted names in all models. Your Python code lowercases strings — replicate this in staging SQL with `lower(trim(column))`.

### Pitfall: Merge vs. append
If you use `incremental` with `append` strategy, you will get duplicates. Use `merge` for upsert behavior.

### Pitfall: Last.fm entity matching in SQL
Levenshtein/fuzzy matching in Snowflake SQL is possible (`EDITDISTANCE` function) but awkward. **Recommendation:** keep matching in Python extract, write only matched records to raw.

### Pitfall: Audio feature compute cost
librosa is CPU-heavy. Give the audio extract task a generous `execution_timeout` and run it in the parallel TaskGroup, not sequentially with other heavy tasks. Do not run it in CI.

### Pitfall: DAG not appearing in Airflow UI
Common causes: import error in DAG file (check scheduler logs), file not in `dags/` folder, missing `DAG()` object or `@dag` decorator, syntax error. Run `airflow dags list-import-errors` to debug.

### Decision: BashOperator vs. Cosmos for dbt
Start BashOperator. Move to Cosmos when you want per-model task visibility and retries.

### Decision: One DAG vs. multiple DAGs
One `music_full_pipeline` DAG while learning. Split when seed and enrich need different schedules.

### Decision: VARIANT vs. typed raw columns
- **VARIANT** (JSON): flexible while iterating on API response shapes.
- **Typed columns**: better query performance, stricter contracts.
- **Recommendation:** start with VARIANT in raw, flatten in staging.

### Decision: Local Docker vs. MWAA/Astro for portfolio
Local Docker is sufficient to demonstrate competence. Document how you *would* deploy to MWAA or Astro — that shows production awareness without cloud cost.

### Decision: Keep PostgreSQL temporarily?
Yes — run Snowflake and PostgreSQL in parallel during Phase 2–3 to validate dbt output against existing PostgreSQL exports before cutover.

---

## 14. Suggested Learning Order

If you are new to these tools, follow this sequence to avoid overwhelm:

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Snowflake basics + SQL | Warehouse, schemas, `COPY INTO`, `MERGE` hands-on |
| 2 | dbt fundamentals | Init project, 1 staging model, 1 mart, tests |
| 3 | dbt advanced | Incremental merge, sources, macros, packages |
| 4 | Airflow basics | Docker setup, hello-world DAG, PythonOperator, UI navigation |
| 5 | Airflow + dbt | BashOperator dbt tasks, TaskGroups, seed → enrich DAG |
| 6 | GitHub Actions | dbt CI + DAG import check workflows |
| 7 | Migration | Port one source end-to-end (Spotify tracks) |
| 8+ | Remaining sources + Cosmos | Last.fm, artists, audio features, decommission legacy |

---

## 15. Resources

### Snowflake
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Snowflake MERGE syntax](https://docs.snowflake.com/en/sql-reference/sql/merge)
- [Key-pair authentication setup](https://docs.snowflake.com/en/user-guide/key-pair-auth)

### dbt
- [dbt Developer Hub](https://docs.getdbt.com/)
- [dbt Snowflake setup](https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup)
- [Incremental models guide](https://docs.getdbt.com/docs/build/incremental-models)
- [dbt best practices: staging → marts](https://docs.getdbt.com/guides/best-practices/how-we-structure/1-guide-overview)
- [dbt_expectations package](https://github.com/calogica/dbt-expectations)

### Airflow
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow Docker Compose setup](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [TaskFlow API tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html)
- [Airflow Snowflake provider](https://airflow.apache.org/docs/apache-airflow-providers-snowflake/stable/index.html)
- [Astronomer Cosmos (dbt + Airflow)](https://astronomer.github.io/astronomer-cosmos/)
- [AWS MWAA overview](https://docs.aws.amazon.com/mwaa/latest/userguide/what-is-mwaa.html) (production reference)

### GitHub Actions
- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [dbt CI job example (dbt Labs)](https://docs.getdbt.com/docs/deploy/ci-cd)

### Migration context
- [ELT vs ETL (dbt Labs)](https://www.getdbt.com/analytics-engineering/transformation/elt)
- Your existing pipeline README for current behavior reference

---

## Quick Reference: Daily Commands (after migration)

| Task | Command |
|------|---------|
| Start Airflow (Docker) | `docker-compose -f docker/docker-compose.yml up -d` |
| Open Airflow UI | `http://localhost:8080` |
| List DAGs | `airflow dags list` |
| Check DAG import errors | `airflow dags list-import-errors` |
| Trigger DAG manually | Airflow UI → Trigger, or `airflow dags trigger music_full_pipeline` |
| Test a DAG locally | `airflow dags test music_full_pipeline <YYYY-MM-DD>` |
| Run all dbt models | `dbt run` |
| Run dbt tests | `dbt test` |
| Run one staging model | `dbt run --select stg_spotify__tracks` |
| Check dbt connection | `dbt debug` |
| Run Python extract tests | `pytest tests/` |
| Lint SQL | `sqlfluff lint dbt/models/` |

---

*This guide is a roadmap, not an implementation. Work one phase at a time, validate each layer against your existing PostgreSQL exports before decommissioning the legacy stack, and keep extract logic in Python until you have a compelling reason to move it.*
