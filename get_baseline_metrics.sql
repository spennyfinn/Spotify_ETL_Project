-- Baseline Metrics Collection Script
-- Run this script to collect all baseline metrics before refactoring
-- Usage: psql -U your_db_user -d your_db_name -f get_baseline_metrics.sql

\echo '=== DATA VOLUMES ==='
SELECT 'Total Songs' as metric, COUNT(*)::text as value FROM songs
UNION ALL
SELECT 'Total Artists', COUNT(*)::text FROM artists
UNION ALL
SELECT 'Total Albums', COUNT(*)::text FROM albums
UNION ALL
SELECT 'Total Tags', COUNT(*)::text FROM tags
UNION ALL
SELECT 'Total Similar Artists', COUNT(*)::text FROM similar_artists
UNION ALL
SELECT 'Songs with Spotify Data', 
    COUNT(*) FILTER (WHERE popularity IS NOT NULL AND release_date IS NOT NULL)::text 
    FROM songs
UNION ALL
SELECT 'Songs with Last.fm Data',
    COUNT(*) FILTER (WHERE song_listeners IS NOT NULL AND engagement_ratio IS NOT NULL)::text
    FROM songs
UNION ALL
SELECT 'Songs with Both Sources',
    COUNT(*) FILTER (
        WHERE popularity IS NOT NULL 
          AND release_date IS NOT NULL
          AND song_listeners IS NOT NULL 
          AND engagement_ratio IS NOT NULL
    )::text
    FROM songs;

\echo ''
\echo '=== DATA COMPLETENESS ==='
SELECT 
    'Spotify Coverage %' as metric,
    ROUND(COUNT(*) FILTER (WHERE popularity IS NOT NULL AND release_date IS NOT NULL) * 100.0 / COUNT(*), 2)::text || '%' as value
FROM songs
UNION ALL
SELECT 
    'Last.fm Coverage %',
    ROUND(COUNT(*) FILTER (WHERE song_listeners IS NOT NULL AND engagement_ratio IS NOT NULL) * 100.0 / COUNT(*), 2)::text || '%'
FROM songs
UNION ALL
SELECT 
    'Songs Missing Spotify Data',
    COUNT(*) FILTER (WHERE popularity IS NULL OR release_date IS NULL)::text
FROM songs
UNION ALL
SELECT 
    'Songs Missing Last.fm Data',
    COUNT(*) FILTER (WHERE song_listeners IS NULL OR engagement_ratio IS NULL)::text
FROM songs;

\echo ''
\echo '=== DATABASE SIZE ==='
SELECT 'Database Size' as metric, pg_size_pretty(pg_database_size(current_database())) as value;

\echo ''
\echo '=== TABLE SIZES ==='
SELECT 
    tablename as metric,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS value
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;

\echo ''
\echo '=== DATA QUALITY ==='
SELECT 
    'Songs Missing Critical Fields' as metric,
    COUNT(*) FILTER (WHERE song_name IS NULL OR artist_id IS NULL)::text as value
FROM songs
UNION ALL
SELECT 
    'Songs Missing Duration',
    COUNT(*) FILTER (WHERE duration_seconds IS NULL)::text
FROM songs
UNION ALL
SELECT 
    'Songs Missing Rank',
    COUNT(*) FILTER (WHERE rank IS NULL)::text
FROM songs
UNION ALL
SELECT 
    'Duplicate Ranks',
    (
        SELECT COUNT(*)::text
        FROM (
            SELECT rank, COUNT(*) 
            FROM songs 
            WHERE rank IS NOT NULL
            GROUP BY rank 
            HAVING COUNT(*) > 1
        ) duplicates
    )
UNION ALL
SELECT 
    'Most Recent Release Date',
    COALESCE(MAX(release_date)::text, 'N/A')
FROM songs
WHERE release_date IS NOT NULL;

\echo ''
\echo '=== ARTIST STATISTICS ==='
SELECT 
    'Artists On Tour' as metric,
    COUNT(*) FILTER (WHERE on_tour = TRUE)::text as value
FROM artists
UNION ALL
SELECT 
    'Total Artist Listeners',
    SUM(total_listeners)::text
FROM artists
UNION ALL
SELECT 
    'Total Artist Playcount',
    SUM(total_playcount)::text
FROM artists;

\echo ''
\echo '=== SONG STATISTICS ==='
SELECT 
    'Average Song Listeners' as metric,
    ROUND(AVG(song_listeners), 2)::text as value
FROM songs
WHERE song_listeners IS NOT NULL
UNION ALL
SELECT 
    'Average Engagement Ratio',
    ROUND(AVG(engagement_ratio), 5)::text
FROM songs
WHERE engagement_ratio IS NOT NULL
UNION ALL
SELECT 
    'Average Popularity (Spotify)',
    ROUND(AVG(popularity), 2)::text
FROM songs
WHERE popularity IS NOT NULL
UNION ALL
SELECT 
    'Explicit Songs Count',
    COUNT(*) FILTER (WHERE is_explicit = TRUE)::text
FROM songs
WHERE is_explicit IS NOT NULL;

