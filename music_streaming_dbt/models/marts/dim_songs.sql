WITH dim AS (
SELECT
    song_id,
    song_name,
    duration_ms,
    duration_seconds,
    duration_minutes,
    track_number,
    release_date,
    release_date_precision,
    is_playable,
    is_explicit,
    mbid
FROM {{ ref('int_song__enriched') }}
)

SELECT * FROM dim
