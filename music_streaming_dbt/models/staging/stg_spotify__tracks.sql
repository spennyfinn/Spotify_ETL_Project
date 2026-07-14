WITH source AS (
    SELECT
        song_id,
        _run_id,
        _loaded_at,
        parse_json(payload::varchar) AS payload
    FROM {{ source('raw', 'raw_spotify_tracks') }}
),

flattened AS (
SELECT 
    trim(song_id::varchar) AS song_id,
    lower(trim(payload:name::varchar)) AS song_name,
    trim(payload:artist_id::varchar) AS artist_id,
    lower(trim(payload:artist_name::varchar)) AS artist_name,
    trim(payload:album_id::varchar) AS album_id,
    lower(payload:album_name::varchar) AS album_title,
    lower(payload:album_type::varchar) AS album_type,
    payload:album_total_tracks::int AS album_total_tracks,
    payload:release_date::varchar AS release_date,
    COALESCE(payload:release_date_precision::varchar,
             CASE LENGTH(payload:release_date::varchar)
                WHEN 4 THEN 'year'
                WHEN 7 THEN 'month'
                WHEN 10 THEN 'day'
                END
    ) AS release_date_precision,
    payload:duration_ms::int AS duration_ms,
    floor(payload:duration_ms::int/1000) AS duration_seconds,
    round(floor(payload:duration_ms::int/1000)/60,2) as duration_minutes,
    payload:popularity::int AS popularity,
    payload:explicit::boolean AS is_explicit,
    payload:track_number::int as track_number,
    payload:is_playable::boolean as is_playable,
    trim(payload:source::varchar) as source,
    _run_id,
    _loaded_at
FROM SOURCE
WHERE song_id IS NOT NULL   
    AND payload:artist_id IS NOT NULL
    AND payload:name IS NOT NULL
    AND payload:duration_ms::int <= 10800000
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY song_id
    ORDER BY _loaded_at DESC
) = 1

)

SELECT * FROM flattened




