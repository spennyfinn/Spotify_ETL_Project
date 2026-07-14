WITH source AS (
    SELECT
        song_id,
        _run_id,
        _loaded_at,
        parse_json(payload::varchar) AS payload
    FROM {{ source('raw', 'raw_lastfm') }}
),


flattened as (
SELECT 
    trim(song_id::varchar) as song_id,
    lower(trim(payload:original_song_name::varchar)) AS song_name,
    lower(trim(payload:original_artist_name::varchar)) AS artist_name,
    trim(payload:artist_id::varchar) AS artist_id,
    payload:listeners::int AS num_song_listeners,
    trim(payload:mbid::varchar) AS mbid,
    payload:on_tour::boolean AS on_tour,
    payload:artist_listeners::int AS artist_total_listeners,
    payload:artist_playcount::int AS artist_total_playcount,
    round( payload:listeners::int /nullif(payload:artist_listeners::int, 0),5) as engagement_ratio,
    round( payload:artist_playcount::int /nullif(payload:artist_listeners::int ,0),5) as plays_per_listener,
    payload:source::varchar AS source,
    _run_id,
    _loaded_at
FROM source
WHERE song_id IS NOT NULL
    AND payload:original_artist_name IS NOT NULL
    AND payload:original_song_name IS NOT NULL
    AND payload:artist_id IS NOT NULL
    AND payload:listeners::int > 0
    AND round( payload:listeners::int /nullif(payload:artist_listeners::int, 0),5) BETWEEN 0 AND 1
    AND payload:artist_listeners::int > 0
    AND payload:artist_playcount::int > 0
    AND _run_id IS NOT NULL
    AND _loaded_at IS NOT NULL
QUALIFY ROW_NUMBER() OVER(
    PARTITION BY song_id
    ORDER BY _loaded_at DESC
) =1
)

SELECT * FROM flattened