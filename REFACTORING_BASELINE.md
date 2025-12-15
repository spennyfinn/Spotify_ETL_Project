# Current System State Documentation
**Date:** December 15, 2025
**Branch:** refactor/spotify-first
**Purpose:** Baseline metrics before refactoring to Spotify-first architecture

---

## Data Volumes

### Database Record Counts
**Record Your Results:**
- Total Songs: 897
- Total Artists: 9648
- Total Albums: 919
- Total Tags: 4267
- Total Similar Artist Relationships: 48473
- Songs with Spotify Data: 877
- Songs with Last.fm Data: 897
- Songs with Both Sources: 877
---

## Data Completeness

### Data Source Coverage

**Record Your Results:**
- Spotify Data Coverage: 97.77%
- Last.fm Data Coverage: 100%
- Songs Missing Spotify Data: 20
- Songs Missing Last.fm Data: 0

---

## Processing Rates

### Extraction Frequencies

**Last.fm Extraction:**
- Frequency: Daily (every 24 hours / 86400 seconds)
- Tracks per run: ~950 tracks (pages 1-20, ~50 tracks per page)
- Estimated processing time per run: 10-15 minutes

**Spotify Extraction:**
- Frequency: Hourly (every 1 hour / 3600 seconds)
- Songs processed per run: Varies (depends on missing data)
- Estimated processing time per run: 5 minutes

### API Call Rates

**Last.fm API:**
- Rate limit: 5 requests/second
- Calls per daily run:
  - Top tracks: 20 calls (1 per page)
  - Track details: ~950 calls (1 per track)
  - Artist details: ~950 calls (1 per artist)
  - Total: ~1920 calls per day
- Average calls per hour: ~80 calls/hour

**Spotify API:**
- Rate limit: 30 requests/second
- Calls per hourly run: Varies (depends on missing data)
- Average calls per hour: 100 calls/hour

---

## Database Size
**Record Your Results:**
- Total Database Size: 18MB
- Largest Table: similar_artists (5464 kB)
- Smallest Table: albums (328 kB)

---

## Data Quality Metrics

**Record Your Results:**
- Songs Missing Critical Fields: 0
- Songs Missing Duration: 0
- Songs Missing Rank: 0
- Duplicate Ranks: 0
- Most Recent Release Date: 2025-12-05

---

## Performance Metrics

### Processing Times

**How to Measure:**
- Check logs from your last run of each script
- Or run scripts with timing: `time python Extract_Lastfm_Data.py`
- Check database timestamps if available

**Last.fm Daily Extraction:**
- Total duration: ~10-15 minutes (estimated based on ~950 tracks)
- Tracks processed: ~950 tracks per run (pages 1-20)
- Average time per track: ~0.6-0.9 seconds (estimated: 10-15 min / 950 tracks)

**Spotify Hourly Extraction:**
- Average duration: ~5 minutes (estimated)
- Average songs processed: ~20 songs per run (based on 20 missing Spotify data)
- Average time per song: ~15 seconds (estimated: 5 min / 20 songs, includes API delays)



---

## Current Issues/Limitations

1. **Data Quality Issues:**
   - 20 songs missing Spotify data (2.23% of total)
   - Last.fm data quality can be inconsistent (user-generated tags, listener counts)
   - Some songs may have incomplete metadata
   - No data quality monitoring or validation beyond Pydantic schemas

2. **Performance Issues:**
   - Last.fm extraction takes 10-15 minutes for ~950 tracks (sequential API calls)
   - Spotify extraction processes ~20 songs/hour (limited by missing data)
   - No parallel processing or batching optimization
   - Database queries could be optimized with better indexing

3. **API Limitations:**
   - Last.fm API: 5 requests/second rate limit (can slow down extraction)
   - Spotify API: 30 requests/second limit (not currently a bottleneck)
   - Last.fm API reliability can vary (occasional timeouts or missing data)
   - No retry logic or exponential backoff for failed API calls

4. **Missing Features:**
   - **Data Visualization & Analytics Dashboard**
     - No interactive dashboard to visualize insights
     - No way to explore data trends or patterns
     - Missing Streamlit/Tableau/Power BI integration
   
   - **Machine Learning Components**
     - No predictive models (popularity prediction, genre classification)
     - No recommendation system for similar artists/songs
     - Missing audio features data (Spotify Audio Features API not integrated)
   
   - **Additional Data Sources**
     - Spotify Audio Features API not integrated (danceability, energy, tempo, etc.)
     - MusicBrainz API not integrated (more comprehensive metadata)
     - YouTube Data API not integrated (video metrics)
   
   - **Business Insights & Analysis**
     - No documented insights or analysis
     - No EDA notebook
     - No business recommendations based on data
   
   - **Testing & Code Quality**
     - No unit tests
     - No integration tests
     - No code quality tools (linting, formatting)
   
   - **Documentation Enhancements**
     - Missing architecture diagrams
     - No project presentation
     - No data dictionary

---

## Notes

- **Current Architecture:** Last.fm is primary data source, Spotify enriches existing tracks
- **Data Coverage:** Excellent Last.fm coverage (100%), good Spotify coverage (97.77%)
- **Database Health:** No data quality issues detected (no missing critical fields, no duplicate ranks)
- **Refactoring Goal:** Switch to Spotify-first architecture for better data quality and ML capabilities
- **Key Observation:** Similar artists table is largest (5.4MB), indicating strong relationship data
- **Processing Pattern:** Last.fm runs daily, Spotify runs hourly to backfill missing data
- **Next Steps:** Begin refactoring to make Spotify primary source, Last.fm as enrichment

