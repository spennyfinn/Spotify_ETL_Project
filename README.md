# Music Streaming ETL Pipeline

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-12+-blue.svg)
![Kafka](https://img.shields.io/badge/kafka-7.4.0-black.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-152%20passing-brightgreen.svg)

A production-grade ETL (Extract, Transform, Load) pipeline that orchestrates real-time music data ingestion from multiple APIs (Spotify and Last.fm), enriches tracks with audio signal features, and persists the data to a normalized PostgreSQL database using Apache Kafka for streaming coordination.

## 🎯 Project Overview

This project demonstrates end-to-end data engineering capabilities by building a scalable pipeline that:

- Extracts music metadata from **Spotify** (tracks, albums, artists, genres) and **Last.fm** (listener metrics, playcount, engagement)
- Transforms and validates data using **Pydantic schemas** for type safety
- Computes **audio features** (BPM, energy, spectral characteristics) from 30-second preview clips using **librosa**
- Streams data through **5 Kafka topics** for decoupled processing
- Loads into a **6-table normalized PostgreSQL schema** with idempotent upserts
- Maintains data quality through **152 automated tests** (unit + end-to-end)

**Key Metrics:**
- Processes up to **200 tracks per query** from Spotify API
- Extracts **8+ signal-based audio features** per track
- Achieves **similarity-based entity matching** (thresholds 0.7-0.9) for cross-API joins
- Handles **parallel processing** with ProcessPoolExecutor for audio feature extraction
- Publishes data in **50-record Kafka batches** for optimal throughput

---

## 🏗️ Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         EXTRACT LAYER                           │
│                   (4 Independent Extractors)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │  Spotify    │   │  Spotify    │   │   Last.fm   │          │
│  │   Tracks    │   │   Artists   │   │   Artists   │          │
│  │  Extractor  │   │  Extractor  │   │  Extractor  │          │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘          │
│         ↓                 ↓                  ↓                  │
│         │                 │                  │                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │music_top    │   │artist_genres│   │lastfm_artist│          │
│  │_tracks      │   │             │   │             │          │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘          │
│         │                 │                  │                  │
│  ┌─────────────┐          │                  │                  │
│  │    Audio    │          │                  │                  │
│  │  Features   │          │                  │                  │
│  │  Extractor  │          │                  │                  │
│  └──────┬──────┘          │                  │                  │
│         ↓                 │                  │                  │
│  ┌─────────────┐          │                  │                  │
│  │music_audio  │          │                  │                  │
│  │_features    │          │                  │                  │
│  └──────┬──────┘          │                  │                  │
│         └─────────────────┴──────────────────┘                  │
│                            ↓                                    │
└────────────────────────────┼───────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      TRANSFORM LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  • Data normalization (lowercase, whitespace removal)          │
│  • Pydantic validation (4 schemas)                             │
│  • Similarity matching (0.7-0.9 thresholds)                    │
│  • Feature engineering (danceability, engagement_ratio)        │
│       ↓                                                         │
│  music_transformed (standardized topic)                         │
└────────────────────────┼───────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                        LOAD LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│              PostgreSQL (6-table schema)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐            │
│  │ artists  │  │ albums   │  │ songs            │            │
│  └──────────┘  └──────────┘  └──────────────────┘            │
│  ┌──────────────────────┐  ┌────────┐  ┌──────────────┐      │
│  │ song_audio_features  │  │ genres │  │ artist_genres│      │
│  └──────────────────────┘  └────────┘  └──────────────┘      │
│  • Idempotent upserts (ON CONFLICT DO UPDATE)                 │
│  • Batch inserts for performance                               │
└─────────────────────────────────────────────────────────────────┘
```

### Kafka Topics

**Raw Data Topics (Extract → Transform):**
1. **`music_top_tracks`**: Spotify track metadata from search queries (name, album, artist, popularity, duration, release date)
2. **`lastfm_artist`**: Last.fm enrichment data (artist listeners, playcount, on_tour status, engagement metrics)
3. **`music_audio_features`**: Computed signal features from preview audio (BPM, energy, spectral centroid, harmonic/percussive ratios)
4. **`artist_genres`**: Spotify artist profiles (popularity, followers, genre associations)

**Standardized Topic (Transform → Load):**
5. **`music_transformed`**: Validated, normalized records ready for database insertion (all 4 sources merged)

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.9+ |
| **Streaming** | Confluent Kafka 7.4.0, Zookeeper |
| **Database** | PostgreSQL (psycopg2-binary) |
| **Data Processing** | Pandas, NumPy, SciPy, statsmodels |
| **Visualisation** | Matplotlib, Seaborn |
| **Audio Analysis** | librosa 0.10.0 |
| **APIs** | Spotify Web API, Last.fm API |
| **Validation** | Pydantic 2.5.0 |
| **Testing** | Pytest, unittest |
| **HTTP** | requests 2.31.0 |
| **Web Scraping** | BeautifulSoup4 |
| **Containerization** | Docker, Docker Compose |

---

## 📁 Project Structure

```
music_streaming_pipeline/
│
├── src/
│   ├── extract/
│   │   ├── spotify_track_extractor.py      # [1] Extracts tracks from Spotify search → music_top_tracks
│   │   ├── spotify_artist_extractor.py     # [2] Extracts artist profiles/genres → artist_genres
│   │   ├── lastfm_extractor.py             # [3] Enriches with Last.fm metrics → lastfm_artist
│   │   └── audio_features_extractor.py     # [4] Computes audio features → music_audio_features
│   │
│   ├── transform/
│   │   └── data_transformer.py             # Normalization & validation
│   │
│   ├── load/
│   │   ├── data_loader.py                  # PostgreSQL batch insertion
│   │   └── parsers.py                      # Message parsing utilities
│   │
│   ├── validate/
│   │   ├── spotify_track_validator.py      # Pydantic schema for Spotify
│   │   ├── lastfm_validator.py             # Pydantic schema for Last.fm
│   │   ├── audio_features_validator.py     # Pydantic schema for audio
│   │   └── artist_validator.py             # Pydantic schema for artists
│   │
│   └── utils/
│       ├── kafka_utils.py                  # Kafka producer/consumer helpers
│       ├── database_utils.py               # PostgreSQL connection utilities
│       ├── spotify_api_utils.py            # Spotify auth & query builders
│       ├── http_utils.py                   # Retry logic & error handling
│       └── text_processing_utils.py        # String normalization
│
├── tests/
│   ├── unit/
│   │   ├── test_parsers.py
│   │   ├── test_text_utils.py
│   │   └── validate/
│   │       ├── test_spotify_track_validator.py
│   │       ├── test_lastfm_validator.py
│   │       └── test_audio_features_validator.py
│   │
│   ├── integration/
│   │   └── test_end_to_end.py              # Full pipeline tests
│   │
│   └── conftest.py                         # Pytest fixtures
│
├── docker/
│   └── docker-compose.yml                  # Kafka, Zookeeper, Kafka UI
│
├── notebooks/
│   ├── 01_EDA.ipynb                        # Exploratory data analysis (popularity, BPM, energy, danceability)
│   ├── 02_correlations.ipynb               # Pearson correlation analysis & scatter plots with regression lines
│   ├── 03_two_tailed_test.ipynb            # Two-sample hypothesis testing (Mann-Whitney U, Cohen's d)
│   ├── 04_ANOVA.ipynb                      # One-way ANOVA by album format and decade (Tukey HSD, eta-squared)
│   ├── STATISTICS_PRACTICE_README.md       # Statistics reference guide (hypothesis testing workflows)
│   └── music_analysis.ipynb                # Original exploratory analysis notebook
│
├── scripts/
│   ├── database_export.py                  # Export tables to CSV
│   └── setup.sh                            # Environment setup script
│
├── config/
│   ├── logging.py                          # Logging configuration
│   └── database/
│       └── create_tables.sql               # PostgreSQL schema DDL
│
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 🚀 Features

### 1. **Multi-Source Data Ingestion (4 Independent Extractors)**

**Extractor 1: Spotify Tracks** (`spotify_track_extractor.py`)
- Searches Spotify API for tracks using query terms
- Extracts metadata: name, album, artist, duration, popularity, release date, explicit flag
- Publishes to `music_top_tracks` topic

**Extractor 2: Spotify Artists** (`spotify_artist_extractor.py`)
- Queries Spotify Artist API for detailed artist profiles
- Extracts: popularity, follower count, associated genres
- Publishes to `artist_genres` topic

**Extractor 3: Last.fm Enrichment** (`lastfm_extractor.py`)
- Matches existing songs/artists with Last.fm data using similarity scoring
- Extracts: listener count, playcount, on_tour status, engagement ratios
- Publishes to `lastfm_artist` topic

**Extractor 4: Audio Features** (`audio_features_extractor.py`)
- Downloads 30-second preview clips from Spotify
- Computes signal-based features using librosa
- Publishes to `music_audio_features` topic

**All extractors include:**
- Retry logic with exponential backoff (up to 5 retries)
- Rate limiting (1-3s per page, 5-10s per query)
- Parallel processing (ProcessPoolExecutor) where applicable

### 2. **Audio Feature Extraction**
Uses **librosa** to compute signal-based features from 30-second preview clips:
- **Tempo**: BPM (beats per minute) via beat tracking
- **Energy**: RMS (root mean square) amplitude
- **Spectral Centroid**: Brightness/timbre characteristic
- **Zero-Crossing Rate**: Percussiveness indicator
- **Harmonic/Percussive Separation**: Separates tonal vs. rhythmic components
- **Danceability**: Composite metric (tempo + energy + ZCR)

### 3. **Similarity-Based Entity Matching**
- Normalizes strings (lowercase, remove whitespace) for comparison
- Uses **Levenshtein distance** (via difflib) to match Spotify ↔ Last.fm artists
- Configurable thresholds (0.7-0.9) to filter low-quality matches
- Prevents duplicate/incorrect joins across APIs

### 4. **Streaming Architecture**
- **Kafka Topics**: Decouples extraction, transformation, and loading
- **Batch Publishing**: Groups records into 50-record batches for throughput
- **Producer Configuration**: `acks=all`, `retries=3`, `snappy compression`
- **Consumer Groups**: Independent processors for each pipeline stage

### 5. **Normalized Database Schema**
Six-table relational design with constraints and indexes (see `config/database/create_tables.sql`):

```sql
CREATE TABLE artists (
    artist_id TEXT PRIMARY KEY,
    artist_name TEXT NOT NULL CHECK(length(artist_name)>0),
    on_tour BOOLEAN DEFAULT FALSE,
    total_listeners BIGINT DEFAULT 0 CHECK(total_listeners >= 0),
    total_playcount BIGINT DEFAULT 0 CHECK(total_playcount>=0),
    plays_per_listener FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    artist_popularity INT,
    artist_followers INT,
    has_genres BOOLEAN
);

CREATE TABLE albums(
    album_id TEXT PRIMARY KEY,
    album_title TEXT NOT NULL,
    artist_id TEXT REFERENCES artists(artist_id),
    album_type TEXT CHECK(album_type IN ('single', 'compilation', 'album')),
    album_total_tracks INT CHECK(album_total_tracks>0 AND album_total_tracks<=200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE songs(
    song_id TEXT PRIMARY KEY,
    song_name TEXT NOT NULL,
    artist_id TEXT REFERENCES artists(artist_id),
    album_id TEXT REFERENCES albums(album_id),
    song_listeners INT DEFAULT 0 CHECK(song_listeners >=0),
    mbid TEXT,
    duration_ms INT CHECK(duration_ms > 1000 AND duration_ms < 10800000),
    duration_seconds INT CHECK (duration_seconds >1 AND duration_seconds < 10800),
    duration_minutes FLOAT CHECK (duration_minutes > .016 AND duration_minutes < 180.0),
    engagement_ratio FLOAT CHECK (engagement_ratio >=0),
    release_date TEXT,
    release_date_precision TEXT CHECK (release_date_precision IN ('year', 'day', 'month')),
    is_explicit BOOLEAN,
    popularity INT CHECK (popularity >=0 AND popularity <= 100),
    track_number INT CHECK (track_number >0 AND track_number<=100),
    is_playable BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE song_audio_features(
    song_id TEXT PRIMARY KEY REFERENCES songs(song_id) ON DELETE CASCADE,
    bpm FLOAT CHECK(bpm >= 30 AND bpm <=300),
    energy FLOAT CHECK(energy >= 0 AND energy <= 1),
    spectral_centroid FLOAT CHECK (spectral_centroid >= 0 AND spectral_centroid <=10000),
    zero_crossing_rate FLOAT CHECK(zero_crossing_rate >= 0 AND zero_crossing_rate <= 1),
    danceability FLOAT CHECK(danceability >= 0 AND danceability <= 1),
    preview_url TEXT,
    harmonic_ratio FLOAT CHECK(harmonic_ratio >= 0 AND harmonic_ratio <= 1),
    percussive_ratio FLOAT CHECK(percussive_ratio >= 0 AND percussive_ratio <= 1),
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE genres(
    genre_id SERIAL PRIMARY KEY,
    genre_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE artist_genres(
    artist_id TEXT REFERENCES artists(artist_id) ON DELETE CASCADE,
    genre_id INT REFERENCES genres(genre_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (artist_id, genre_id)
);

-- Indexes for query optimization
CREATE INDEX idx_songs_engagement_ratio ON songs(engagement_ratio);
CREATE INDEX idx_songs_release_date ON songs(release_date);
CREATE INDEX idx_albums_total_tracks ON albums(album_total_tracks);
CREATE INDEX idx_artist_name ON artists(artist_name);
CREATE INDEX idx_songs_popularity ON songs(popularity DESC);
```

**Key Design Features:**
- **Foreign Keys**: Enforce referential integrity between tables
- **Check Constraints**: Validate data ranges (e.g., popularity 0-100, BPM 30-300)
- **Cascade Deletes**: Automatically clean up dependent records
- **Indexes**: Optimize queries on frequently filtered columns
- **Timestamps**: Track record creation and updates for auditing

### 6. **Data Quality & Testing**
- **Pydantic Validation**: 4 schemas enforce type constraints and required fields
- **Unit Tests**: 152 test cases covering extractors, transformers, parsers, validators
- **End-to-End Tests**: Full pipeline integration tests with mocked APIs
- **Idempotent Upserts**: `ON CONFLICT DO UPDATE` prevents duplicate records

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- PostgreSQL (or use Docker)
- Spotify API credentials ([Get here](https://developer.spotify.com/))
- Last.fm API key ([Get here](https://www.last.fm/api))

### 1. Clone Repository
```bash
git clone https://github.com/spennyfinn/music_streaming_pipeline.git
cd music_streaming_pipeline
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the example environment file and fill in your credentials:
```bash
cp .env.example .env
```

Then edit `.env` with your actual API keys and database credentials:
- **Spotify API**: Get credentials at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- **Last.fm API**: Get API key at [Last.fm API Account](https://www.last.fm/api/account/create)
- **PostgreSQL**: Use your local database credentials

### 4. Start Kafka Infrastructure
```bash
docker-compose -f docker/docker-compose.yml up -d
```

This starts:
- **Zookeeper** (port 2182)
- **Kafka** (port 9094)
- **Kafka UI** (http://localhost:8081)

### 5. Create PostgreSQL Database & Schema

```bash
# Create the database
psql -U your_db_user -c "CREATE DATABASE music_db;"

# Run the schema creation script
psql -U your_db_user -d music_db -f config/database/create_tables.sql
```

This will create:
- 6 tables (artists, albums, songs, song_audio_features, genres, artist_genres)
- Foreign key constraints
- Check constraints for data validation
- 5 indexes for query optimization

### 6. Run Pipeline Components

**Pipeline Stages (in order):**

```bash
# Stage 1: EXTRACT (4 independent extractors - can run in parallel)
python src/extract/spotify_track_extractor.py      # → music_top_tracks
python src/extract/spotify_artist_extractor.py     # → artist_genres
python src/extract/lastfm_extractor.py             # → lastfm_artist
python src/extract/audio_features_extractor.py     # → music_audio_features

# Stage 2: TRANSFORM (consumes all 4 raw topics)
python src/transform/data_transformer.py           # → music_transformed

# Stage 3: LOAD (consumes standardized topic)
python src/load/data_loader.py                     # → PostgreSQL
```

**Notes:**
- All 4 extractors can run **independently** and **in parallel**
- Each publishes to its own Kafka topic
- The transformer waits for messages from any of the 4 topics
- The loader processes the standardized `music_transformed` topic

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_parsers.py

# Run integration tests only
pytest tests/integration/
```

---

## 📊 Pipeline Metrics

| Metric | Value |
|--------|-------|
| Extract Modules | 4 independent data sources |
| Kafka Topics | 5 (4 raw + 1 standardized) |
| Database Tables | 6 (normalized schema) |
| Pydantic Schemas | 4 (validation models) |
| Automated Tests | 152 (unit + integration) |
| API Sources | 2 (Spotify + Last.fm) |
| Audio Features Extracted | 8+ per track |
| Batch Size (Kafka) | 50 records |
| Retry Logic | Up to 5 retries with backoff |
| Similarity Thresholds | 0.7-0.9 (artist matching) |

---

## 📈 Data Analysis

The project includes a four-notebook statistical analysis series built on top of the pipeline's PostgreSQL exports (~109K songs across 6 joined tables):

| Notebook | Description |
|----------|-------------|
| `01_EDA.ipynb` | Exploratory analysis of popularity, BPM, energy, and danceability — histograms, summary stats, correlation heatmap |
| `02_correlations.ipynb` | Full Pearson correlation analysis across all 18 features, scatter plots with regression lines and R² values for the top predictors of song popularity |
| `03_two_tailed_test.ipynb` | Two-sample hypothesis tests (Mann-Whitney U) comparing explicit vs clean songs and singles vs album tracks — includes normality checks, Cohen's d effect size, and confidence intervals |
| `04_ANOVA.ipynb` | One-way ANOVA testing popularity differences across album formats (singles, albums, compilations) and across decades (1960s–2020s) — includes Tukey HSD post-hoc and eta-squared effect sizes |

**Key findings:**
- Artist popularity is the strongest predictor of song popularity (R² = 0.36, r = 0.60)
- Explicit vs clean and singles vs albums differences are statistically significant but have negligible effect sizes (d < 0.05)
- Song popularity declines steadily across more recent decades, likely reflecting survivorship bias in older catalogue and recency weighting in the Spotify algorithm (η² = 0.013, small effect)

---

## 🧠 Data Analysis Interview Reference

A quick-reference summary of every statistical concept, function, and workflow used in the analysis notebooks — written for interview preparation.

---

### Core Concepts

| Term | What It Means |
|------|--------------|
| **p-value** | Probability that your result happened by chance. If p < 0.05, the result is statistically significant and you reject H0 |
| **Alpha (α)** | Your significance threshold — standard is 0.05 (5%) |
| **H0 (Null Hypothesis)** | Assumes no difference or no effect between groups |
| **H1 (Alternative Hypothesis)** | What you believe is actually true — there IS a difference |
| **Reject H0** | p < α — the result is statistically significant |
| **Fail to reject H0** | p > α — not enough evidence to conclude a difference exists |
| **Effect size** | How big the difference actually is, independent of sample size. A result can be significant but practically meaningless |
| **Statistical power** | Probability of detecting a real effect when one exists — increases with sample size |
| **Type I Error** | False positive — you rejected H0 but it was actually true |
| **Type II Error** | False negative — you failed to reject H0 but it was actually false |
| **Normal distribution** | Bell-shaped curve — many tests assume your data looks like this |
| **Central Limit Theorem** | With large samples (n > 30), the distribution of sample means approaches normal regardless of the raw data shape |

---

### Descriptive Statistics — `df.describe()`

Returns count, mean, std, min, 25%, 50% (median), 75%, max for every numeric column. Always run this first before any test to understand your data.

```python
df.describe()
df['column'].mean()
df['column'].median()
df['column'].std()
df['column'].value_counts()
```

---

### Correlation Analysis — `pearsonr`, `df.corr()`

**What it does:** Measures the strength and direction of the linear relationship between two continuous variables. Ranges from -1 (perfect negative) to +1 (perfect positive). 0 means no relationship.

**When to use it:** Both variables are continuous and you want to understand if they move together.

**Key functions:**
```python
# Correlation matrix across all numeric columns
df.corr()

# Pearson r and p-value for a single pair
from scipy.stats import pearsonr
r, p = pearsonr(x, y)
r_squared = r**2   # R² = proportion of variance explained

# Regression line on a scatter plot
m, b = np.polyfit(x, y, 1)
```

**Interpreting R²:** R² = 0.36 means the x variable explains 36% of the variance in y. The other 64% is driven by factors not in the model.

---

### Normality Check — `shapiro`

**What it does:** Tests whether your data is normally distributed. Required before deciding between a t-test and its non-parametric alternative.

**When to use it:** Before running a t-test or ANOVA. Sample 500 rows on large datasets — Shapiro becomes hypersensitive above ~5000 rows and will always return p < 0.05 even for trivially non-normal distributions.

```python
from scipy.stats import shapiro
_, p = shapiro(group.sample(500, random_state=42))
# p > 0.05 → normal → use t-test
# p < 0.05 → not normal → use Mann-Whitney U
```

---

### Two-Sample T-Test — `ttest_ind`

**What it does:** Tests whether two groups have significantly different means.

**When to use it:** Two groups, continuous outcome, data is approximately normal (or n > 30).

**Steps:**
1. State H0 and H1
2. Split data into two groups
3. Check normality (Shapiro-Wilk)
4. Run t-test
5. Compute Cohen's d (effect size)
6. Compute confidence intervals
7. Write conclusion

```python
from scipy.stats import ttest_ind
t_stat, p_val = ttest_ind(group1, group2)
# Uses Welch's t-test by default (does not assume equal variances)
```

**Note:** `ttest_ind` handles unequal group sizes fine. Welch's correction is applied automatically.

---

### Mann-Whitney U Test — `mannwhitneyu`

**What it does:** Non-parametric alternative to the t-test. Compares the distributions of two groups without assuming normality. Tests whether one group tends to have higher values than the other.

**When to use it:** Data fails normality, is heavily skewed, or has significant outliers.

```python
from scipy.stats import mannwhitneyu
stat, p_val = mannwhitneyu(group1, group2, alternative='two-sided')
```

**vs t-test:** Mann-Whitney compares distributions/rankings; t-test compares means. On large samples they almost always agree on the conclusion.

---

### Cohen's d (Effect Size for T-Tests)

**What it does:** Measures how many standard deviations apart the two group means are. Tells you if a statistically significant difference is actually meaningful in practice.

```python
pooled_std = np.sqrt((group1.std()**2 + group2.std()**2) / 2)
cohens_d   = (group1.mean() - group2.mean()) / pooled_std
```

| Value | Interpretation |
|-------|---------------|
| d < 0.2 | Negligible |
| 0.2 ≤ d < 0.5 | Small |
| 0.5 ≤ d < 0.8 | Medium |
| d ≥ 0.8 | Large |

**Why it matters:** With 50k+ rows, almost any difference will have p < 0.05. Cohen's d tells you if that difference is big enough to act on.

---

### Confidence Intervals — `DescrStatsW`

**What it does:** Gives a range of values that likely contains the true population mean. A 95% CI means if you ran the study 100 times, 95 of those intervals would contain the true mean.

```python
import statsmodels.stats.api as sms
ci = sms.DescrStatsW(group).tconfint_mean()
# Returns (lower_bound, upper_bound)
```

**Interpretation:** If two group CIs do not overlap, the groups are likely significantly different. If they overlap significantly, the difference may not be meaningful.

---

### Levene's Test (Equal Variance Check for ANOVA)

**What it does:** Tests whether two or more groups have equal variances — a key assumption of ANOVA.

```python
from scipy.stats import levene
stat, p = levene(group1, group2, group3)
# p > 0.05 → variances are equal → use standard ANOVA
# p < 0.05 → variances differ → consider Welch's ANOVA
```

**Note:** Like Shapiro-Wilk, Levene's becomes hypersensitive on large samples. Use boxplots to visually assess variance equality alongside the test result.

---

### One-Way ANOVA — `f_oneway`

**What it does:** Tests whether at least one of three or more groups has a significantly different mean. More appropriate than running multiple t-tests (which inflates false positive rate).

**When to use it:** Three or more groups, continuous outcome, roughly equal variances.

**Steps:**
1. State H0 and H1
2. Split data into groups
3. Check equal variance (Levene's + boxplot)
4. Run ANOVA
5. Run Tukey HSD post-hoc if significant
6. Compute eta-squared (effect size)
7. Write conclusion

```python
from scipy.stats import f_oneway
f_stat, p_val = f_oneway(group1, group2, group3)
```

**F-statistic:** Ratio of between-group variance to within-group variance. F = 19 means the groups differ 19x more than individual items vary within each group.

---

### Tukey HSD Post-Hoc Test — `pairwise_tukeyhsd`

**What it does:** After a significant ANOVA, tells you exactly WHICH pairs of groups are significantly different from each other.

```python
from statsmodels.stats.multicomp import pairwise_tukeyhsd
tukey = pairwise_tukeyhsd(endog=df['outcome'], groups=df['group'], alpha=0.05)
print(tukey)
# reject=True → that pair is significantly different
# meandiff → the difference in means between the pair
```

---

### Eta-Squared η² (Effect Size for ANOVA)

**What it does:** Proportion of total variance in the outcome explained by the grouping variable.

```python
grand_mean = df['outcome'].mean()
ss_between = sum(len(g) * (g.mean() - grand_mean)**2 for g in groups)
ss_total   = sum((df['outcome'] - grand_mean)**2)
eta_sq     = ss_between / ss_total
```

| Value | Interpretation |
|-------|---------------|
| η² < 0.01 | Negligible |
| 0.01 ≤ η² < 0.06 | Small |
| 0.06 ≤ η² < 0.14 | Medium |
| η² ≥ 0.14 | Large |

---

### The Large Sample Problem — Know This Cold

With 50,000+ rows, statistical tests become hypersensitive. Both Shapiro-Wilk and Levene's will return p = 0.00 for differences so small they are invisible on a plot and irrelevant in practice. **Always report effect size alongside p-values.** A result can be statistically significant and practically meaningless at the same time — this is the most common mistake analysts make when interpreting results on large datasets.

---

## 📝 Key Learnings

1. **Modular extractor design**: Separating data sources into 4 independent extractors enabled parallel execution and simplified debugging when one API had issues.
2. **Kafka for decoupling**: Using 5 Kafka topics (4 raw + 1 standardized) separated extraction, transformation, and loading into independent services, improving modularity and fault tolerance.
3. **Pydantic for validation**: Type-safe schemas caught data inconsistencies early in the pipeline, preventing malformed data from reaching the database.
4. **Similarity matching challenges**: Cross-API entity resolution (Spotify ↔ Last.fm) required string normalization and threshold tuning (0.7-0.9) to avoid false matches.
5. **Audio processing at scale**: Parallel processing (ProcessPoolExecutor) reduced audio feature extraction time by 3x compared to sequential processing.
6. **Idempotent upserts**: `ON CONFLICT DO UPDATE` enabled safe reprocessing without duplicate records, crucial for replay scenarios.

---

## 👤 Author

**Spencer Finnegan**  
📧 spencerfinnegan813@gmail.com  
🐙 [GitHub](https://github.com/spennyfinn)

---

## ⚠️ Known Limitations

- **API Rate Limits**: Spotify and Last.fm have rate limits; script includes delays to respect them
- **Audio Preview Availability**: Not all tracks have 30-second preview clips for feature extraction
- **Similarity Matching**: Cross-API entity resolution may produce false negatives with low thresholds
- **Data Freshness**: Pipeline requires manual execution; no automated scheduling included

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

API usage subject to [Spotify Terms of Service](https://developer.spotify.com/terms) and [Last.fm API Terms](https://www.last.fm/api/tos).
