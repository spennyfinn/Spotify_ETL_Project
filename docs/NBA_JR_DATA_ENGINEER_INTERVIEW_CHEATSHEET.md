# NBA Jr. Data Engineer — 3-Hour Interview Study Guide

**Role:** Jr Data Engineer (Snowflake / Tableau) — contract-to-hire  
**Client:** NBA — Secaucus, NJ  
**This interview:** Friday preliminary screen (technical + fit, not the 4–5 hr coding panel)

> **How to use this doc:** Study in order. Each block has a time budget. Definitions are short — the goal is to explain **how pieces connect** and **answer interview questions out loud**, not memorize glossaries.

---

## 3-Hour Study Plan

| Block | Time | Focus | Success check |
|-------|------|-------|---------------|
| **1** | 45 min | Your story + NBA context + full stack flow | Can draw the architecture diagram from memory |
| **2** | 60 min | Pipeline design + Snowflake/dbt/SQL working together | Can walk through Scenario A (ticketing) in 5 min |
| **3** | 45 min | Tableau + SSIS + behavioral | Can explain live vs extract and Control vs Data Flow |
| **4** | 30 min | SQL patterns + cram cards | Can write dedup + funnel SQL from memory |

**Morning of (15 min):** Re-read Section 7 (cram cards) + rehearse 60-second pitch once.

---

## 1. Your Story + NBA Context (45 min)

### Who you are (Spencer Finnegan)

- **NYU** — Environmental Studies major, Computer Science minor
- **PropertyTools.ai** — Junior developer: document extraction pipeline, Google Analytics setup, front-end work
- **Projects:** Music streaming ETL (Python, Kafka, PostgreSQL, ML) + NYC 311 analytics platform (Python, dbt, Dagster, BigQuery, dashboard)
- **Now:** Migrating music pipeline to Snowflake + dbt + Airflow

### 90-second "Tell me about yourself" (say this out loud 3×)

> "I'm Spencer Finnegan. I graduated from NYU with a major in Environmental Studies and a minor in Computer Science, and I've been building toward data engineering through work and personal projects.
>
> At PropertyTools.ai I was a junior developer, where I contributed most notably to a document extraction pipeline — taking unstructured documents and turning them into structured data the product could use. I also set up Google Analytics and did some front-end work, which gave me exposure to how data gets collected and consumed on both sides of a pipeline.
>
> On the project side, I've built two pipelines that map directly to this role. First, a music streaming ETL that extracts from Spotify and Last.fm APIs, transforms and validates the data in Python, and loads a normalized star schema in PostgreSQL — orchestrated with Kafka and tested heavily. I'm now migrating that same pipeline to Snowflake, dbt, and Airflow, which is the ELT pattern I'd use here.
>
> Second, I built a NYC 311 analytics platform using Python, dbt, Dagster, and BigQuery — full ELT from raw civic complaint data through staged models to KPI marts, plus a dashboard for stakeholders. That taught me warehouse-layer transforms, orchestration, and serving governed metrics to BI — the same workflow as landing fan data in Snowflake, modeling it with dbt, and refreshing Tableau.
>
> What draws me to the NBA role is that the problems are the same ones I've been solving: multi-source ingestion, idempotent loads, entity matching across systems, and data quality at scale — just applied to fan engagement, ticketing, and stats instead of music and civic data."

### 60-second version (if they cut you off)

> "I'm Spencer — NYU grad, CS minor, junior developer at PropertyTools.ai where I built a document extraction pipeline. My two main data projects are a music ETL — Python and Kafka into a PostgreSQL star schema, now migrating to Snowflake and dbt — and a NYC 311 platform with Python, dbt, Dagster, and BigQuery plus a KPI dashboard. Both taught me multi-source ingestion, idempotent loads, and entity matching — the same problems as unifying NBA fan data across ticketing, app events, and CRM."

### Map your experience → NBA (use when they ask "relevant experience?")

**PropertyTools.ai**

| Your work | NBA equivalent | **How it connects** |
|-----------|----------------|---------------------|
| Document extraction pipeline | Unstructured source → structured tables | Same as parsing JSON/CSV payloads into raw → staging |
| Google Analytics setup | Amplitude / GA ingestion | You understand event collection and downstream reporting |
| Front-end development | Consumption layer awareness | You know what happens after the mart lands |

**Music streaming ETL**

| Your project | NBA equivalent | **How it connects** |
|-------------|----------------|---------------------|
| Spotify + Last.fm extractors | Stats API, ticketing vendor, Amplitude | Python pulls data; transform belongs in warehouse |
| Kafka (5 topics) | Event streams, decoupled ingestion | Orchestration — Airflow DAG or Snowpipe in modern stack |
| Pydantic validation | dbt tests + staging filters | Bad rows caught before marts |
| PostgreSQL star schema | Snowflake `dim_*` / `fct_*` marts | BI connects to marts, not raw |
| `ON CONFLICT` upserts | `MERGE` / dbt incremental | Idempotent reruns — no duplicate rows |
| Cross-API entity matching | Fan identity resolution | Join ticketing `fan_id` to app `user_id` via email/hash |
| ML popularity pipeline | RFM / engagement scoring | Downstream analytics on governed marts |
| `stg_spotify__tracks.sql` | `stg_league_pass__events` | Flatten JSON, type cast, dedupe, filter bad rows |

**NYC 311 analytics platform** *(lead with this for dbt/warehouse questions)*

| Your project | NBA equivalent | **How it connects** |
|-------------|----------------|---------------------|
| BigQuery warehouse | Snowflake | Same ELT pattern — different engine |
| dbt staging → marts | dbt on Snowflake | **Direct match** — this is the job |
| Dagster orchestration | Airflow / Snowflake Tasks | DAG dependencies, schedules, retries |
| KPI dashboard | Tableau on marts | Stakeholders consume governed metrics, not raw |
| Civic complaint grain | Ticket sale / app event grain | Declare grain, build dims/facts, test keys |

**Concrete dbt example to mention:** Your `stg_spotify__tracks` model reads raw JSON, flattens fields, standardizes text, dedupes on `song_id`, filters nulls. *"Same pattern on 311 complaint records or League Pass events — flatten payload, enforce types, dedupe on natural key, quarantine bad rows."*

### What the NBA actually cares about (business → pipeline)

The NBA is a **fan engagement + commerce + stats** business. Data engineering turns fragmented touchpoints into **one trusted analytics layer**.

| Domain | Sources | Pipeline output | Who consumes |
|--------|---------|-----------------|--------------|
| Fan engagement | NBA App, League Pass, web analytics | `fct_app_events`, engagement marts | Marketing, product |
| Ticketing & commerce | Vendor CSV/API, season tickets | `fct_ticket_sales`, revenue aggregates | Sales, finance, teams |
| Marketing | CRM, campaigns, attribution | RFM segments, campaign ROI | Growth, DTC |
| Stats | NBA Stats API, play-by-play | `fct_player_game_stats` | NBA.com, media, internal BI |

**Phrase to use:** *"I'd design pipelines that turn fragmented fan touchpoints into governed, analytics-ready marts so marketing and BI trust the same numbers."*

### Public Fan Data Platform (you don't need to pretend you built it)

NBA teams run a **centralized Snowflake fan platform** (discussed at Snowflake Summit):

- **20+ sources** → Snowflake raw → staging → marts
- **dbt, Fivetran**, stored procedures, Snowflake sharing
- **PII governance** — masking, row access policies, consent flags
- **Tableau/Power BI** on marts

Say: *"I've studied the public fan platform architecture. My music pipeline follows the same ELT pattern at smaller scale."*

### Latency — know what a Jr. role owns

| Type | Latency | Tools | Jr. role? |
|------|---------|-------|-----------|
| Batch nightly | Hours | COPY, dbt, SSIS → S3 → Snowflake | **Yes — core work** |
| Near-real-time | Minutes | Snowpipe, Streams, Tasks | **Yes — common** |
| Live game stats | Seconds | Kafka, dedicated streaming | Usually senior / separate team |

---

## 2. How the Stack Works Together (60 min)

This is the most important section. Interviewers want to hear you describe **flow**, not tool definitions in isolation.

### End-to-end architecture (draw this on paper)

```
SOURCES                    INGEST                    WAREHOUSE                         CONSUME
─────────                  ──────                    ─────────                         ───────
Ticketing vendor CSV  ──►  SSIS or Python  ──►  RAW (VARIANT/typed, append-only)
Amplitude / GA        ──►  Fivetran        ──►       │
League Pass events    ──►  Snowpipe        ──►       ▼
SQL Server CRM        ──►  SSIS → S3       ──►  STAGING (dbt: clean, type, dedupe)
Stats API             ──►  Python          ──►       │
                                                      ▼
                                                 INTERMEDIATE (joins, identity resolution)
                                                      │
                                                      ▼
                                                 MARTS (dim_fan, fct_ticket_sales, …)
                                                      │
                                                      ▼
                                                 Tableau (live or extract refresh)
```

### ETL vs ELT — when each piece runs

**Old pattern (ETL):** Extract → Transform in Python/SSIS → Load clean data  
**NBA modern pattern (ELT):** Extract → Load raw fast → Transform in Snowflake with SQL/dbt

| Step | Who does it | Why |
|------|-------------|-----|
| **Extract** | Python, Fivetran, SSIS, Snowpipe | APIs, file formats, legacy SQL Server — not warehouse SQL |
| **Load raw** | `COPY INTO`, `write_pandas`, Fivetran | Preserve source fidelity; replay transforms if logic changes |
| **Transform** | dbt models in Snowflake | SQL is fast at scale; version-controlled; testable |
| **Serve** | Tableau on marts | Business users never query raw |

**One-liner:** *"Extract stays outside Snowflake; transform moves into the warehouse; orchestration ties the schedule together."*

### Layer-by-layer — what happens and why

| Layer | Purpose | Key operations | Fails if you skip it |
|-------|---------|----------------|----------------------|
| **RAW** | Audit trail, reprocessing | Append-only, keep `_loaded_at`, `_run_id`, VARIANT JSON | Can't debug bad mart rows or replay after logic change |
| **STAGING** | Source-aligned cleanup | Cast types, trim, rename, filter nulls, dedupe latest | BI sees dirty data; joins break on type mismatch |
| **INTERMEDIATE** | Business logic | Cross-source joins, fan matching, attribution rules | Each mart reimplements logic; numbers disagree |
| **MARTS** | Analytics-ready | Star schema `dim_*` / `fct_*`, declared grain | Tableau slow, ambiguous metrics, no governance |

### Snowflake — only what you need to explain how it fits

**Three layers (say this when asked "how does Snowflake work?"):**
1. **Storage** — columnar micro-partitions in cloud (S3/Azure); cheap; no indexes
2. **Compute** — virtual warehouses (separate from databases); pay per second; auto-suspend
3. **Cloud services** — auth, query planning, metadata (always on)

**Objects you'll actually connect in a pipeline:**

| Object | Role in the pipeline | Pairs with |
|--------|---------------------|------------|
| **Warehouse** | Runs COPY, dbt, queries | Auto-suspend after idle; separate ETL vs BI warehouses |
| **Stage + COPY INTO** | Batch file landing | Nightly CSV from S3; scheduled Airflow task |
| **Snowpipe** | Continuous micro-batch load | App events every few minutes |
| **VARIANT + FLATTEN** | Semi-structured JSON in raw | dbt staging `payload:field::type` |
| **MERGE** | Upsert / incremental | dbt incremental models; idempotent reruns |
| **Stream + Task** | Change detection + scheduled SQL | Near-real-time mart updates without Airflow |
| **RBAC + masking** | Analysts see marts only; PII masked | Fan email hidden from most roles |

**PostgreSQL → Snowflake (your migration story):**

| Postgres | Snowflake |
|----------|-----------|
| `ON CONFLICT DO UPDATE` | `MERGE INTO` |
| `JSONB` | `VARIANT` |
| Dedup subquery | `QUALIFY ROW_NUMBER() … = 1` |
| External cron | Airflow DAG or Snowflake `TASK` |

**Cost control (common question):** Right-size warehouses, auto-suspend (60s), separate `etl_wh` from `bi_wh`, don't leave Large warehouses idle overnight.

### dbt — how it sits in the pipeline

dbt is **not** an orchestrator. It is **transform + test + document** inside Snowflake.

```
Airflow:  extract_task >> snowflake_load_task >> dbt_run_task >> dbt_test_task >> tableau_refresh
dbt:      raw sources → stg_* → int_* → dim_*/fct_*  (each model = one SQL file + YAML tests)
```

| dbt concept | Pipeline role |
|-------------|---------------|
| `sources.yml` | Documents raw tables; lineage starts here |
| Staging models | 1:1 with source, cleaned |
| Mart models | Business-facing star schema |
| `unique`, `not_null`, `relationships` tests | Catch bad data before Tableau refresh |
| Incremental materialization | MERGE for large fact tables |

**Your talking point:** *"dbt replaced my Python transform layer — same validation, but in SQL with built-in tests and lineage."*

### Orchestration — who schedules what

| Tool | Schedules | NBA likely use |
|------|-----------|----------------|
| **Airflow** | Full DAG: extract → load → dbt → refresh | Modern pipelines |
| **Snowflake Tasks** | SQL steps inside Snowflake (often chained) | Stream processing, simple chains |
| **SSIS + SQL Agent** | Legacy Windows ETL | SQL Server sources → files → Snowflake |
| **Fivetran** | Managed SaaS sync | Amplitude, Salesforce — hands-off extract/load |

**Jr. engineer answer:** *"I'd want one orchestrator of record per pipeline — Airflow for multi-system DAGs, Snowflake Tasks for in-warehouse micro-batches, SSIS where legacy sources require it."*

### Data modeling — how dims and facts connect

**Process (use on any design question):**
1. Name the **business process** (ticket sale, app session)
2. Declare **grain** (one row per what?)
3. Pick **dimensions** (fan, team, date)
4. Pick **facts/measures** (amount, count — additive?)
5. Assign **surrogate keys** (`fan_key`) separate from source IDs
6. Load **dimensions before facts**

**Star schema example — ticketing:**

```
dim_fan ──────┐
dim_team ─────┼──► fct_ticket_sales  (grain: one row per ticket)
dim_date ─────┘         measures: sale_amount, seat_count
```

**SCD Type 2 (fan moves markets / loyalty tier history):** New row with `valid_from` / `valid_to` / `is_current`. Query current: `WHERE is_current = TRUE`.

**Identity resolution (Fan 360):** Staging per source → match on hashed email / device_id → single `fan_key` in `dim_fan`. Same pattern as your Spotify/Last.fm artist matching.

### Pipeline design — 8-step framework (use for any "design a pipeline" question)

1. **Sources** — API, files, SQL Server, streaming?
2. **Volume & latency** — rows/day? nightly OK or need minutes?
3. **Ingestion** — Snowpipe (continuous) vs COPY (batch) vs Fivetran vs SSIS
4. **Raw** — land fast, VARIANT for JSON, metadata columns
5. **Transform** — staging → intermediate → marts; declare grain and keys
6. **Data quality** — dbt tests, quarantine bad rows, row-count alerts
7. **Consumption** — which marts? Tableau live vs extract? refresh time?
8. **Ops** — monitoring, backfill plan, cost controls

**Error handling philosophy:** *"Fail on critical errors (source down, zero rows). Quarantine non-critical bad rows so one bad ticket doesn't block the nightly load."*

---

## 3. Interview Questions You Will Likely Get (with answer structure)

### "Walk me through a pipeline you built end to end."

**Pick one based on the question.** If they say "dbt" or "warehouse" → **311 platform**. If they say "APIs" or "streaming" → **music pipeline**.

**311 platform (2 min — best for this role):**
1. **Source** — NYC Open Data 311 complaint records
2. **Extract** — Python to pull/load raw into BigQuery
3. **Transform** — dbt: staging (clean, type, dedupe) → marts (KPIs by borough, category, response time)
4. **Orchestrate** — Dagster schedules extract → dbt run → dbt test
5. **Quality** — dbt tests on keys, not-null, business rules
6. **Consume** — Dashboard for stakeholders on KPI marts

Tie to NBA: *"Same flow — land raw in Snowflake, dbt to marts, refresh Tableau for marketing or ops."*

**Music pipeline (2 min — your go-to "walk me through end to end" answer):**

Use this structure: **v1 in 30 sec → v2 (current) in 90 sec → NBA tie-in in 10 sec.** Telling both versions shows you understand ETL → ELT migration, not just one stack.

> **Opening:** "My biggest project is a music streaming pipeline I built end to end — and I've since reworked it from a classic ETL stack into modern ELT, which is the same evolution I'd expect at the NBA."
>
> **V1 (original — Kafka + Postgres):** "I wrote separate Python extractors for Spotify and Last.fm APIs. Each published to its own Kafka topic — five topics total — which decoupled extract from transform. A single transformation consumer read from those topics, routed records through source-specific logic, deduplicated them, and validated everything against Pydantic schemas. Only clean records went to the load step, which upserted into a normalized PostgreSQL star schema — six tables with idempotent `ON CONFLICT` loads. I had 150+ automated tests across the pipeline."
>
> **V2 (current — Snowflake + dbt + Tableau):** "I'm reworking that same pipeline into ELT. Python still handles ingestion — APIs don't belong in SQL — but now it loads straight into raw tables in Snowflake with minimal transformation. From there, dbt owns the warehouse layers:
> - **Staging** — one model per source; flatten JSON, cast types, standardize text, dedupe on natural keys like `song_id`
> - **Intermediate** — business joins, like enriching songs with Last.fm listener data or rolling up artist genres
> - **Marts** — final star schema: `dim_artists`, `dim_songs`, `dim_albums`, `fct_songs`, `fct_audio_features`, plus a genre bridge table
>
> Each layer has dbt tests — unique, not-null, relationships — so bad data gets caught before BI sees it. I built a Tableau dashboard on the marts to track KPIs like popularity, engagement ratios, and audio feature distributions."
>
> **NBA tie-in:** "Same pattern as NBA fan data — Python lands raw events, dbt builds governed marts, Tableau consumes KPIs. The multi-source matching I did across Spotify and Last.fm is the same problem as fan identity resolution across ticketing and the app."

**Layer cheat sheet (if they ask "why staging vs intermediate vs marts?"):**

| Layer | Your models | Purpose |
|-------|-------------|---------|
| **Raw** | `raw_spotify_tracks`, etc. | Source fidelity, replay transforms |
| **Staging** | `stg_spotify__tracks`, `stg_lastfm`, `stg_audio__features` | Clean one source, dedupe, type |
| **Intermediate** | `int_song__enriched`, `int_artist__genres`, `int_albums` | Cross-source joins and enrichment |
| **Marts** | `dim_*`, `fct_*`, `bridge_artist_genres` | Analytics-ready star schema for Tableau |

**If they interrupt with "just the current version" (60 sec):**

> "Python extracts from Spotify and Last.fm into Snowflake raw tables. dbt staging models clean and dedupe per source. Intermediate models join across sources — like matching artists between APIs. Marts are a star schema — dims and facts — with dbt tests on every layer. Tableau sits on top for KPIs. Same ELT pattern as landing fan data raw, transforming in the warehouse, and serving Tableau."

Tie to NBA: *"Same as unifying fan IDs across ticketing, app, and CRM — land raw, transform in SQL, test before BI."*

---

### "Design a nightly ticketing pipeline." (most likely design question)

**Prompt:** Vendor drops CSV on S3 at 2 AM. Marketing needs dashboard by 8 AM.

#### Your answer (polished — practice this out loud)

> "I'd design this as an event-driven ELT pipeline with a hard SLA at 8 AM.
>
> **Ingestion (2–3 AM):** The vendor drops a CSV on S3 at 2 AM. I'd configure an S3 event notification to an SQS queue, which triggers **Snowpipe** to auto-ingest the file into `raw.ticket_sales` — append-only, with `_loaded_at` and file metadata for audit. Alternative for a single predictable nightly file: skip Snowpipe and run a scheduled **`COPY INTO`** from an external stage at 3 AM via Airflow — simpler, same result.
>
> **Transform (3–6 AM):** Once raw data lands, an **Airflow DAG** or **Snowflake Task** kicks off dbt:
> - **Staging** — cast types, trim strings, dedupe on `ticket_id` with `ROW_NUMBER`, filter nulls; quarantine rows with negative amounts to a `rejected_records` table
> - **Intermediate** — join to existing `dim_fan` and `dim_team` on natural keys
> - **Marts** — `fct_ticket_sales` at grain = one row per ticket; pre-aggregate `daily_team_revenue` for the dashboard
>
> **Data quality:** Before BI sees anything — row-count check vs prior day (alert if ±30%), dbt tests on `unique(ticket_id)`, `not_null(sale_amount)`, and `sale_amount >= 0`. Fail the pipeline on zero rows; quarantine bad rows, don't block the whole load.
>
> **Consumption (7 AM):** Scheduled **Tableau extract refresh** on `daily_team_revenue` — extract, not live, since this is a nightly historical dashboard. Marketing has fresh data by 8 AM with buffer for failures.
>
> **Ops:** Slack alert if any step fails; `COPY_HISTORY` / Snowpipe load history for debugging; backfill by re-processing a date range with `COPY` + dbt `--full-refresh` on affected models."

#### Timeline (shows you thought about the SLA)

```
2:00 AM  Vendor drops CSV on S3
2:05 AM  S3 event → SQS → Snowpipe loads raw.ticket_sales
3:00 AM  Airflow/dbt: staging → intermediate → marts (+ tests)
6:00 AM  Pipeline complete; buffer if anything retries
7:00 AM  Tableau extract refresh on daily_team_revenue
8:00 AM  Marketing opens dashboard ✓
```

#### Step reference (if they want you to enumerate)

| Step | What you'd say |
|------|----------------|
| 1 | S3 external stage; S3 → SQS → **Snowpipe** (or scheduled **COPY INTO** at 3 AM) |
| 2 | Row-count check vs prior day; alert if ±30% |
| 3 | dbt `stg_ticket_sales`: cast, trim, dedupe on `ticket_id` with `QUALIFY ROW_NUMBER()` |
| 4 | Intermediate: join to `dim_fan`, `dim_team`; quarantine bad amounts |
| 5 | Mart: `fct_ticket_sales` (grain = one ticket); `daily_team_revenue` for Tableau |
| 6 | dbt tests: `unique(ticket_id)`, `not_null(sale_amount)`, `sale_amount >= 0` |
| 7 | Tableau extract refresh 7 AM |
| 8 | Backfill: re-run COPY for date range + dbt `--full-refresh` on affected models |

#### If they push back: "Why Snowpipe for one nightly file?"

*"Snowpipe is optional here — it's event-driven so we don't poll S3. For a single CSV at a known time, a scheduled `COPY INTO` at 3 AM via Airflow is simpler and totally fine. I'd pick Snowpipe if files arrive at unpredictable times or we want hands-off auto-ingest; I'd pick COPY if the schedule is fixed and we want fewer moving parts."*

#### What your draft had vs what to add

| You said ✓ | Also mention |
|-----------|--------------|
| S3 → SQS → Snowpipe → raw | **What triggers dbt** after raw lands (Airflow or Snowflake Task) |
| staging → intermediate → marts | **Grain** (one row per ticket), **dedupe key** (`ticket_id`) |
| Dashboard by 8 AM | **Tableau extract refresh at 7 AM** (explicit schedule + buffer) |
| | **Data quality** — row-count check, dbt tests, quarantine bad rows |
| | **Failure handling** — alert if zero rows; don't fail whole load on a few bad records |

---

### "How do you handle incremental loads / reruns without duplicates?"

**Answer flow:**
1. Define **natural key** (`ticket_id`, `event_id`)
2. Track **watermark** (`_loaded_at` or `max(updated_at)`)
3. Use **MERGE** or dbt incremental on key match
4. Pipeline is **idempotent** — safe to rerun

```sql
-- Dedup to latest (Snowflake)
SELECT * FROM raw.app_events
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY event_id ORDER BY _loaded_at DESC
) = 1;
```

Your music pipeline: `ON CONFLICT DO UPDATE` → Snowflake `MERGE` / dbt incremental.

---

### "How does near-real-time differ from batch?"

| | Batch (nightly) | Near-real-time (minutes) |
|--|-----------------|--------------------------|
| Ingest | Scheduled COPY | Snowpipe from S3 |
| Raw | Daily files | Continuous small files |
| Transform | dbt after load completes | Stream on raw → Task every 15 min MERGE to mart |
| Tableau | Extract refresh once daily | Live connection or frequent incremental extract |
| Example | Ticketing mart | League Pass concurrent viewers |

---

### "How would you build Fan 360 across ticketing, app, and email?"

1. **Staging per source** — don't merge in raw
2. **Identity resolution** intermediate — match on hashed email; confidence score
3. **`dim_fan`** with surrogate `fan_key`, SCD Type 2 for tier/market changes
4. **Consent flags** — filter PII for marketing use cases
5. **Row access policies** — team analysts see only their market
6. **Mart** — `fct_fan_engagement` unified for Tableau

*Same as your cross-API artist matching with similarity thresholds.*

---

### "How do you ensure data quality?"

Layer the checks — **don't rely on one place:**

| Layer | Check |
|-------|-------|
| Extract | Schema validation, API error handling |
| Raw load | Row count, file arrival SLA |
| Staging | Filter nulls, type casts, dedupe |
| dbt tests | unique, not_null, relationships, custom SQL |
| Mart | Reconciliation vs source totals |
| BI | Freshness SLA; alert if extract fails |

---

### "How do you control Snowflake costs?"

- Auto-suspend warehouses (60s idle)
- Right-size: X-Small for dev/BI light queries, Medium for nightly ETL
- Separate ETL and BI warehouses
- Pre-aggregate in marts (don't let Tableau scan raw)
- Clustering only on large tables with non-date filter patterns

---

### "What's the difference between a data lake and a warehouse?"

**Short answer:** Lake = cheap storage for raw files (schema-on-read); Warehouse = structured, governed, SQL-optimized for BI. **Snowflake blurs the line** — VARIANT raw layer acts like lake; marts act like warehouse. NBA pattern: raw JSON in Snowflake, not a separate Hadoop cluster.

---

### "Explain idempotency."

Running the same pipeline twice produces the **same result** — no duplicate rows. Achieved via MERGE/upsert on natural keys. Critical for retries after failure.

---

### "What is grain?"

**One row per ___**. If grain is "one ticket" you can't store daily totals in the same table. Declare grain before writing SQL — interviewers test this on design questions.

---

## 4. SQL Patterns (30 min — write these from memory)

### Dedup to latest record
```sql
SELECT *
FROM raw.app_events
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY event_id
  ORDER BY _loaded_at DESC
) = 1;
```

### Running total (cumulative revenue by team)
```sql
SELECT
  team_id,
  sale_date,
  daily_revenue,
  SUM(daily_revenue) OVER (
    PARTITION BY team_id
    ORDER BY sale_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_revenue
FROM marts.daily_team_revenue;
```

### Top N per group
```sql
SELECT * FROM (
  SELECT fan_id, product_name, purchase_count,
    ROW_NUMBER() OVER (PARTITION BY fan_id ORDER BY purchase_count DESC) AS rn
  FROM marts.fct_merch_sales
) WHERE rn <= 3;
```

### Funnel (app events → watch → purchase)
```sql
WITH funnel AS (
  SELECT
    fan_id,
    MAX(IFF(event_type = 'app_open', 1, 0)) AS opened,
    MAX(IFF(event_type = 'video_start', 1, 0)) AS watched,
    MAX(IFF(event_type = 'purchase', 1, 0)) AS purchased
  FROM marts.fct_app_events
  WHERE event_date = CURRENT_DATE - 1
  GROUP BY fan_id
)
SELECT
  SUM(opened) AS step1_opens,
  SUM(watched) AS step2_watches,
  SUM(purchased) AS step3_purchases,
  ROUND(100.0 * SUM(watched) / NULLIF(SUM(opened), 0), 1) AS watch_rate_pct
FROM funnel;
```

### MERGE (upsert)
```sql
MERGE INTO marts.fct_ticket_sales t
USING staging.stg_ticket_sales s ON t.ticket_id = s.ticket_id
WHEN MATCHED THEN UPDATE SET sale_amount = s.sale_amount, updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (ticket_id, sale_amount, fan_key, team_key) VALUES (...);
```

### Flatten JSON (raw → staging)
```sql
SELECT
  f.value:id::varchar AS item_id,
  f.value:name::varchar AS item_name
FROM raw.events e,
LATERAL FLATTEN(input => e.payload:items) f;
```

**CTEs vs subqueries vs windows:** Use CTEs to readable multi-step transforms (staging pattern). Use windows for dedup, running totals, ranking — not GROUP BY.

---

## 5. Tableau + SSIS — How They Fit (45 min)

You don't need to be a Tableau developer for a Jr. DE role. You need to explain **how BI connects to your pipelines**.

### Tableau in the pipeline

```
dbt builds marts overnight
    → Airflow triggers Tableau extract refresh (or users query live)
    → Marketing opens dashboard on Tableau Server
```

| Decision | Choose live connection when… | Choose extract when… |
|----------|------------------------------|----------------------|
| **Data freshness** | Need current data (tonight's sales) | Daily/historical is fine |
| **Performance** | Small mart, fast Snowflake query | Large data, many users |
| **Source load** | Low query volume | Protect Snowflake from 500 concurrent queries |

**Extract flow:** Tableau queries Snowflake once → saves `.hyper` file on Server → users query local copy → scheduled refresh after dbt.

**Published data source (enterprise pattern):** One governed connection to `marts.*` on Server; many workbooks share it. Change mart once → all dashboards update. **You maintain the refresh schedule.**

**LOD expressions (know the concept):** Calculations at a different grain than the viz. Example: avg fan lifetime value on a team-level chart → `{ FIXED [fan_id] : SUM([sale_amount]) }` then average. **Best practice:** pre-compute hard metrics in Snowflake marts; use Tableau calcs for display only.

**Dashboard slow?** Performance Recorder → check if Tableau queries raw → fix: pre-aggregate in mart → switch to extract → reduce marks/filters.

**Jr. DE Tableau responsibilities:** Refresh schedules, published data source permissions, troubleshooting failed extracts, pointing workbooks at marts not raw.

---

### SSIS in the pipeline (legacy — but in the JD)

SSIS = Microsoft's visual ETL for **SQL Server → files/other DBs**. NBA likely uses it for **legacy on-prem sources**, not greenfield Snowflake transforms.

```
SQL Server (ticketing CRM)
    → SSIS Package (.dtsx)
        Control Flow: orchestration (truncate, log, email on failure)
        Data Flow: row-level ETL (source → transform → destination)
    → CSV on S3
    → Snowflake COPY INTO raw
    → dbt takes over from here
```

| SSIS concept | What it does | Airflow/dbt equivalent |
|--------------|--------------|------------------------|
| **Control Flow** | Task sequence, error branches | Airflow DAG dependencies |
| **Data Flow** | Row-level transform inside one task | dbt models / staging SQL |
| **Lookup transform** | Enrich rows from reference table | SQL JOIN to dim table |
| **Precedence constraints** | Run B only if A succeeds | Airflow `>>` with trigger rules |
| **SSISDB** | Execution history, environments | Airflow UI + connections per env |

**Interview answer if you haven't used SSIS hands-on:** *"I haven't built SSIS packages in production, but I understand the pattern — Control Flow orchestrates, Data Flow moves rows, SSISDB tracks runs. In a hybrid stack I'd use SSIS for SQL Server extraction and Snowflake/dbt for warehouse transforms, which matches the migration path I'd expect at the NBA."*

**SSIS vs modern stack:** Don't replace SSIS overnight. New sources → Fivetran/Snowpipe. Legacy sources → SSIS until migrated.

---

## 6. Behavioral + Questions to Ask (15 min)

### "Tell me about yourself" (90 sec)
Use Section 1 pitch (PropertyTools → 311 platform → music pipeline → why NBA). If Snowflake comes up: *"Hands-on with dbt on BigQuery and migrating my music project to Snowflake — same ELT pattern, studying COPY/MERGE/streams for NBA-specific ingestion."*

### Other behavioral (short answers)

| Question | Answer skeleton |
|----------|-----------------|
| **Handle ambiguity?** | Clarify grain and metric definition first → thin vertical slice → validate with stakeholder |
| **Prioritize requests?** | Impact × urgency × effort; SLAs beat ad-hoc; communicate timelines early |
| **Production incident?** | Check freshness → isolate layer (extract/load/transform) → Time Travel if bad deploy → fix forward + postmortem |
| **AI tools?** | Cursor for SQL/dbt velocity; Cortex Analyst for governed text-to-SQL on marts (not raw PII) |

### Questions to ask them (pick 3)

1. "Is this role on the Fan Data Platform team or broader IT data warehouse?"
2. "What's the split between new pipeline builds vs maintaining SSIS/Snowflake jobs?"
3. "How do you orchestrate — Airflow, Snowflake Tasks, SSIS, or a mix?"
4. "What does the Tableau estate look like — mostly extracts on Snowflake marts?"
5. "How does the team handle PII and consent in the warehouse?"
6. "What would success look like in the first 90 days?"

---

## 7. Cram Cards (morning-of — 15 min)

### Load decision tree
```
Files arrive continuously, need < 15 min latency?  → Snowpipe
Files arrive daily/hourly batches?                 → COPY INTO + schedule
Need upsert / incremental?                         → MERGE or dbt incremental
Need change detection without external CDC?        → Stream + Task
Legacy SQL Server source?                          → SSIS → file → COPY
SaaS app (Amplitude, Salesforce)?                  → Fivetran → raw
```

### Tableau decision tree
```
Need real-time data?           → Live connection to mart
Historical / large / many users? → Extract + scheduled refresh after dbt
Dashboard slow?                → Pre-aggregate in Snowflake → extract
Enterprise governance?         → Published data source on Server
```

### Project → NBA one-liners

| They ask | You say |
|----------|---------|
| Pipelines | "311: Python → BigQuery raw → dbt marts → dashboard. Music: same pattern, migrating to Snowflake" |
| dbt | "Built full 311 platform with dbt + Dagster; music staging models on Snowflake now" |
| Data quality | "Pydantic + 150 tests on music; dbt tests on 311 — staging filters before marts" |
| Multi-source | "Spotify + Last.fm entity matching — same as fan identity resolution" |
| Snowflake | "Migrating music pipeline; same ELT as my BigQuery/dbt 311 work" |
| Work experience | "PropertyTools doc extraction — unstructured → structured, like JSON raw → staging" |
| ELT vs ETL | "Land raw fast, transform in warehouse — replayable and testable" |
| SSIS | "Haven't used in prod; understand legacy extract → file → Snowflake → dbt handoff" |

### Essential terms (one line each)

| Term | One-liner |
|------|-----------|
| **OLTP vs OLAP** | App DB = transactions; warehouse = analytics aggregations |
| **Idempotency** | Rerun safe — MERGE on natural key |
| **Grain** | One row per X — declare before modeling |
| **SCD Type 2** | Track history with valid_from/valid_to rows |
| **CDC** | Capture inserts/updates/deletes from source |
| **Surrogate key** | Warehouse `fan_key` — stable across source ID changes |
| **VARIANT** | Snowflake semi-structured JSON type |
| **Micro-partition** | Snowflake storage unit; pruning replaces indexes |

---

## What to Skip (not worth time in 3 hours)

- Snowflake Cortex AI deep dive (mention Analyst if asked)
- Data Vault modeling details (know it exists for multi-source audit trails)
- Every SSIS transformation by name
- Every Snowflake object (Fail-safe, UDF catalog, etc.)
- Power BI / Databricks unless they bring it up
- Round 2 coding prep (that's a separate study session)

---

*You have real pipeline experience. Frame it as the same ELT pattern the NBA uses publicly. Be honest about Snowflake/Tableau/SSIS ramp-up — show you understand how the pieces connect and you'll learn the UI fast.*
